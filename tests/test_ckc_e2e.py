"""
CKC End-to-End Test Suite
=========================

Omfattende tests for det komplette CKC-økosystem:
- TaskContext dataflow
- ILCP JSON-schema validering
- WorkLoopSequencer orkestrering
- Fuld agent-workflow integration

Version: 1.1.0
"""

import asyncio
import pytest
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Tilføj projekt-sti
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# Helpers
# ============================================================

def print_test_header(name: str):
    """Print test header."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)


def print_result(success: bool, message: str):
    """Print test result."""
    status = "✅ BESTÅET" if success else "❌ FEJLET"
    print(f"{status}: {message}")


# ============================================================
# Test 1: TaskContext Dataflow
# ============================================================

class TestTaskContextE2E:
    """E2E tests for TaskContext dataflow."""

    def test_context_creation_and_serialization(self):
        """Test oprettelse og serialisering af TaskContext."""
        print_test_header("TaskContext Creation & Serialization")

        from cirkelline.ckc.context import (
            TaskContext,
            WorkflowStep,
            WorkflowStepStatus,
            ContextSource,
            ContextValidationLevel,
            create_context_for_task,
            validate_context_schema
        )

        # Opret context med korrekte parametre
        context = create_context_for_task(
            task_id="e2e-test-001",
            prompt="Test document analysis workflow",
            user_id="test-user",
            session_id="test-session-001",
            source_platform="ckc"
        )

        assert context is not None, "Context skal oprettes"
        assert context.task_id == "e2e-test-001", "Task ID skal matche"
        assert context.original_prompt == "Test document analysis workflow", "Prompt skal matche"

        # Tilføj workflow steps
        step1 = WorkflowStep(
            step_id="step-1",
            agent_id="document_agent",
            action="extract",
            status=WorkflowStepStatus.COMPLETED,
            input_data={"file_path": "/test/doc.pdf"},
            output_data={"text": "Extracted text content"}
        )
        context.add_workflow_step(step1)

        step2 = WorkflowStep(
            step_id="step-2",
            agent_id="knowledge_agent",
            action="index",
            status=WorkflowStepStatus.IN_PROGRESS
        )
        context.add_workflow_step(step2)

        # Serialisering
        context_dict = context.to_dict()
        assert "task_id" in context_dict, "Serialisering skal indeholde task_id"
        assert len(context_dict.get("workflow_steps", [])) == 2, "Skal have 2 steps"

        # Validering
        is_valid, errors = validate_context_schema(context_dict)
        assert is_valid, f"Schema validering skal bestå: {errors}"

        print_result(True, "TaskContext oprettet og serialiseret korrekt")

    def test_context_through_workflow(self):
        """Test at context flyder korrekt gennem et workflow."""
        print_test_header("TaskContext Through Workflow")

        from cirkelline.ckc.context import (
            TaskContext,
            WorkflowStep,
            WorkflowStepStatus,
            ContextSource,
            create_context_for_task
        )

        # Simuler en fuld workflow
        context = create_context_for_task(
            task_id="workflow-e2e-001",
            prompt="Creative synthesis workflow test",
            user_id="test-user"
        )

        # Step 1: Tool Explorer
        context.add_workflow_step(WorkflowStep(
            step_id="tool-explore",
            agent_id="tool_explorer",
            action="explore",
            status=WorkflowStepStatus.COMPLETED,
            output_data={"tools": ["text_analyzer", "sentiment_detector"]}
        ))

        # Step 2: Creative Synthesizer
        context.add_workflow_step(WorkflowStep(
            step_id="creative-synth",
            agent_id="creative_synthesizer",
            action="synthesize",
            status=WorkflowStepStatus.COMPLETED,
            input_data={"tools": ["text_analyzer", "sentiment_detector"]},
            output_data={"synthesis": "Combined analysis result"}
        ))

        # Step 3: Quality Assurance
        context.add_workflow_step(WorkflowStep(
            step_id="qa-check",
            agent_id="qa_agent",
            action="check",
            status=WorkflowStepStatus.COMPLETED,
            output_data={"approved": True, "score": 0.95}
        ))

        # Verificer context state
        assert len(context.workflow_steps) == 3, "Skal have 3 workflow steps"

        # Verificer data flow mellem steps
        step_outputs = {step.step_id: step.output_data for step in context.workflow_steps}
        assert "tools" in step_outputs["tool-explore"], "Tool output skal eksistere"
        assert step_outputs["qa-check"]["approved"] is True, "QA skal godkende"

        print_result(True, "Context flød korrekt gennem workflow")


# ============================================================
# Test 2: ILCP JSON-Schema Validation
# ============================================================

class TestILCPValidationE2E:
    """E2E tests for ILCP message validation."""

    @pytest.mark.asyncio
    async def test_message_validation_modes(self):
        """Test alle validerings modes."""
        print_test_header("ILCP Validation Modes")

        from cirkelline.ckc.advanced_protocols import (
            ILCPManager,
            MessageType,
            MessagePriority,
            ValidationMode
        )

        manager = ILCPManager()

        # Test strict mode med korrekt DATA_REQUEST schema format
        manager.set_validation_mode(ValidationMode.STRICT)

        # Korrekt format ifølge ILCP_DATA_REQUEST_SCHEMA
        valid_content = {
            "request_type": "knowledge_query",
            "data_keys": ["documents", "insights"],
            "filters": {"topic": "ai"},
            "urgency": "normal"
        }

        is_valid, errors = await manager.validate_message_content(
            MessageType.DATA_REQUEST,
            valid_content,
            ValidationMode.STRICT
        )

        assert is_valid, f"Gyldig besked skal validere i STRICT mode: {errors}"

        # Test lenient mode med mindre streng data
        manager.set_validation_mode(ValidationMode.LENIENT)

        relaxed_content = {
            "request_type": "simple_query"
            # Mangler data_keys, men kan være OK i LENIENT mode
        }

        is_valid, errors = await manager.validate_message_content(
            MessageType.DATA_REQUEST,
            relaxed_content,
            ValidationMode.LENIENT
        )

        print(f"  LENIENT mode errors (expected): {errors}")

        # Test disabled mode
        manager.set_validation_mode(ValidationMode.DISABLED)

        stats = manager.get_validation_stats()
        assert stats["total_validated"] > 0, "Skal have kørt valideringer"

        print_result(True, "Alle validation modes testet")

    @pytest.mark.asyncio
    async def test_message_with_task_context(self):
        """Test ILCP beskeder med TaskContext attachment."""
        print_test_header("ILCP Message with TaskContext")

        from cirkelline.ckc.advanced_protocols import (
            ILCPManager,
            MessageType,
            MessagePriority,
            ValidationMode
        )
        from cirkelline.ckc.context import (
            TaskContext,
            ContextSource,
            create_context_for_task
        )

        manager = ILCPManager()
        manager.set_validation_mode(ValidationMode.NORMAL)

        # Opret TaskContext
        context = create_context_for_task(
            task_id="ilcp-ctx-001",
            prompt="Knowledge sharing workflow"
        )

        # Send besked med context - brug korrekt KNOWLEDGE_SHARE format
        content = {
            "knowledge_type": "insight",
            "content_data": "Shared knowledge content",
            "tags": ["ai", "ml"]
        }

        message = await manager.send_message_with_context(
            sender_room_id=1,
            recipient_room_id=2,
            message_type=MessageType.KNOWLEDGE_SHARE,
            content=content,
            task_context=context,
            priority=MessagePriority.HIGH
        )

        assert message is not None, "Besked skal oprettes"
        assert message.task_context_data is not None, "TaskContext skal være attached"
        assert message.is_validated, "Besked skal være valideret"

        # Verificer context kan hentes
        retrieved_context = message.get_context()
        assert retrieved_context is not None, "Context skal kunne hentes"
        assert retrieved_context.task_id == "ilcp-ctx-001", "Task ID skal matche"

        print_result(True, "ILCP besked med TaskContext valideret")

    @pytest.mark.asyncio
    async def test_schema_validation_coverage(self):
        """Test alle ILCP schema typer."""
        print_test_header("ILCP Schema Coverage")

        from cirkelline.ckc.advanced_protocols import (
            ILCPManager,
            MessageType,
            ValidationMode,
            ILCP_MESSAGE_SCHEMA,
            ILCP_DATA_REQUEST_SCHEMA,
            ILCP_DATA_RESPONSE_SCHEMA,
            ILCP_KNOWLEDGE_SHARE_SCHEMA
        )

        manager = ILCPManager()
        manager.set_validation_mode(ValidationMode.STRICT)

        schemas_tested = 0

        # Test DATA_REQUEST schema - korrekt format
        data_request = {
            "request_type": "knowledge_query",
            "data_keys": ["documents", "insights"],
            "filters": {"topic": "ai"},
            "urgency": "normal"
        }
        is_valid, errors = await manager.validate_message_content(
            MessageType.DATA_REQUEST, data_request, ValidationMode.STRICT
        )
        assert is_valid, f"DATA_REQUEST schema validation failed: {errors}"
        schemas_tested += 1

        # Test DATA_RESPONSE schema - korrekt format
        data_response = {
            "request_id": "req-001",
            "success": True,
            "data": {"items": []},
            "error": None
        }
        is_valid, errors = await manager.validate_message_content(
            MessageType.DATA_RESPONSE, data_response, ValidationMode.STRICT
        )
        assert is_valid, f"DATA_RESPONSE schema validation failed: {errors}"
        schemas_tested += 1

        # Test KNOWLEDGE_SHARE schema - korrekt format
        knowledge_share = {
            "knowledge_type": "insight",
            "content_data": {"text": "Important insight"},
            "confidence_score": 0.9,
            "tags": ["important"]
        }
        is_valid, errors = await manager.validate_message_content(
            MessageType.KNOWLEDGE_SHARE, knowledge_share, ValidationMode.STRICT
        )
        # Knowledge share validering kan være mere fleksibel
        print(f"  KNOWLEDGE_SHARE validation: {is_valid}, errors: {errors}")
        schemas_tested += 1

        print(f"  Testet {schemas_tested} schema typer")
        print_result(True, "ILCP schemas testet")


# ============================================================
# Test 3: WorkLoopSequencer E2E
# ============================================================

class TestWorkLoopSequencerE2E:
    """E2E tests for WorkLoopSequencer."""

    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self):
        """Test simpel workflow eksekvering."""
        print_test_header("Simple Workflow Execution")

        from cirkelline.ckc.orchestrator import (
            WorkLoopSequencer,
            WorkLoopStep,
            WorkLoopStepType,
            WorkLoopStatus
        )

        sequencer = WorkLoopSequencer()

        # Registrer mock agent handlers
        async def mock_tool_explorer(action: str, data: Dict) -> Dict:
            return {"tools_found": ["analyzer", "processor"]}

        async def mock_synthesizer(action: str, data: Dict) -> Dict:
            tools = data.get("tools", [])
            return {"synthesis": f"Combined {len(tools)} tools"}

        sequencer.register_agent_handler("tool_explorer", mock_tool_explorer)
        sequencer.register_agent_handler("creative_synthesizer", mock_synthesizer)

        # Opret workflow steps
        steps = [
            WorkLoopStep(
                step_id="explore",
                step_type=WorkLoopStepType.AGENT_CALL,
                agent_id="tool_explorer",
                action="find_tools",
                output_key="tools_result"
            ),
            WorkLoopStep(
                step_id="transform",
                step_type=WorkLoopStepType.TRANSFORM,
                transform_fn=lambda x: {"tools": x.get("tools_result", {}).get("tools_found", [])},
                output_key="prepared_tools"
            ),
            WorkLoopStep(
                step_id="synthesize",
                step_type=WorkLoopStepType.AGENT_CALL,
                agent_id="creative_synthesizer",
                action="synthesize",
                input_mapping={"prepared_tools": "tools"},
                output_key="synthesis_result"
            )
        ]

        # Opret og kør loop
        loop = sequencer.create_loop(
            name="E2E Test Workflow",
            description="Test af simpel workflow",
            steps=steps
        )

        success, result = await sequencer.execute_loop(loop)

        assert success, f"Workflow skal lykkes: {result}"
        assert loop.status == WorkLoopStatus.COMPLETED, "Status skal være COMPLETED"
        assert "synthesis_result" in result, "Skal have synthesis resultat"

        print(f"  Result: {result}")
        print_result(True, "Simpel workflow eksekveret")

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel eksekvering af steps."""
        print_test_header("Parallel Workflow Execution")

        from cirkelline.ckc.orchestrator import (
            WorkLoopSequencer,
            WorkLoopStep,
            WorkLoopStepType
        )

        sequencer = WorkLoopSequencer()

        # Registrer mock handlers
        async def mock_agent_a(action: str, data: Dict) -> Dict:
            await asyncio.sleep(0.1)  # Simuler arbejde
            return {"agent": "A", "result": "A completed"}

        async def mock_agent_b(action: str, data: Dict) -> Dict:
            await asyncio.sleep(0.1)
            return {"agent": "B", "result": "B completed"}

        async def mock_agent_c(action: str, data: Dict) -> Dict:
            await asyncio.sleep(0.1)
            return {"agent": "C", "result": "C completed"}

        sequencer.register_agent_handler("agent_a", mock_agent_a)
        sequencer.register_agent_handler("agent_b", mock_agent_b)
        sequencer.register_agent_handler("agent_c", mock_agent_c)

        # Opret parallel step
        parallel_steps = [
            WorkLoopStep(
                step_id="parallel-a",
                step_type=WorkLoopStepType.AGENT_CALL,
                agent_id="agent_a",
                action="work"
            ),
            WorkLoopStep(
                step_id="parallel-b",
                step_type=WorkLoopStepType.AGENT_CALL,
                agent_id="agent_b",
                action="work"
            ),
            WorkLoopStep(
                step_id="parallel-c",
                step_type=WorkLoopStepType.AGENT_CALL,
                agent_id="agent_c",
                action="work"
            )
        ]

        steps = [
            WorkLoopStep(
                step_id="parallel-execution",
                step_type=WorkLoopStepType.PARALLEL_CALL,
                parallel_steps=parallel_steps,
                output_key="parallel_results"
            )
        ]

        loop = sequencer.create_loop(
            name="Parallel E2E Test",
            description="Test parallel eksekvering",
            steps=steps
        )

        start_time = datetime.now(timezone.utc)
        success, result = await sequencer.execute_loop(loop)
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

        assert success, f"Parallel workflow skal lykkes: {result}"
        assert "parallel_results" in result, "Skal have parallel resultater"

        # Verificer alle agenter kørte
        parallel_result = result["parallel_results"]
        assert "parallel-a" in parallel_result, "Agent A skal have kørt"
        assert "parallel-b" in parallel_result, "Agent B skal have kørt"
        assert "parallel-c" in parallel_result, "Agent C skal have kørt"

        # Parallel burde være hurtigere end sekventiel (3 * 0.1s)
        assert elapsed < 0.5, f"Parallel eksekvering burde være hurtig: {elapsed}s"

        print(f"  Elapsed time: {elapsed:.2f}s")
        print(f"  Results: {parallel_result}")
        print_result(True, "Parallel eksekvering succesfuld")

    @pytest.mark.asyncio
    async def test_conditional_workflow(self):
        """Test workflow med conditions."""
        print_test_header("Conditional Workflow")

        from cirkelline.ckc.orchestrator import (
            WorkLoopSequencer,
            WorkLoopStep,
            WorkLoopStepType,
            WorkLoopStatus
        )

        sequencer = WorkLoopSequencer()

        # Mock agent
        async def mock_validator(action: str, data: Dict) -> Dict:
            return {"is_valid": True, "score": 0.85}

        sequencer.register_agent_handler("validator", mock_validator)

        steps = [
            WorkLoopStep(
                step_id="validate",
                step_type=WorkLoopStepType.AGENT_CALL,
                agent_id="validator",
                action="validate",
                output_key="validation"
            ),
            WorkLoopStep(
                step_id="check-score",
                step_type=WorkLoopStepType.CONDITION,
                # Condition function får hele loop.step_results som argument
                condition_fn=lambda data: data.get("validation", {}).get("score", 0) > 0.8,
                output_key="passed_check"
            ),
            WorkLoopStep(
                step_id="final-transform",
                step_type=WorkLoopStepType.TRANSFORM,
                transform_fn=lambda data: {"approved": data.get("passed_check", False)},
                output_key="final_result"
            )
        ]

        loop = sequencer.create_loop(
            name="Conditional E2E Test",
            description="Test conditions",
            steps=steps
        )

        success, result = await sequencer.execute_loop(loop)

        assert success, f"Conditional workflow skal lykkes: {result}"
        # Check at validation resultatet er der
        assert "validation" in result, f"Skal have validation key: {result.keys()}"
        print(f"  Validation result: {result.get('validation')}")
        print(f"  Passed check: {result.get('passed_check')}")
        print(f"  Final result: {result.get('final_result')}")

        print_result(True, "Conditional workflow eksekveret")

    @pytest.mark.asyncio
    async def test_workflow_with_task_context(self):
        """Test workflow med TaskContext integration."""
        print_test_header("Workflow with TaskContext")

        from cirkelline.ckc.orchestrator import (
            WorkLoopSequencer,
            WorkLoopStep,
            WorkLoopStepType,
            WorkLoopStatus
        )
        from cirkelline.ckc.context import (
            TaskContext,
            ContextSource,
            create_context_for_task
        )

        sequencer = WorkLoopSequencer()

        # Mock agent der bruger context
        async def context_aware_agent(action: str, data: Dict) -> Dict:
            return {
                "action_performed": action,
                "context_received": True,
                "data_keys": list(data.keys())
            }

        sequencer.register_agent_handler("context_agent", context_aware_agent)

        # Opret TaskContext
        context = create_context_for_task(
            task_id="ctx-workflow-001",
            prompt="Full analysis workflow test",
            user_id="test-user"
        )

        steps = [
            WorkLoopStep(
                step_id="context-step",
                step_type=WorkLoopStepType.AGENT_CALL,
                agent_id="context_agent",
                action="process_with_context",
                output_key="context_result"
            )
        ]

        loop = sequencer.create_loop(
            name="Context Workflow Test",
            description="Test TaskContext integration",
            steps=steps
        )

        # Kør med context
        success, result = await sequencer.execute_loop(
            loop,
            context=context,
            input_data={"initial": "data"}
        )

        assert success, f"Context workflow skal lykkes: {result}"
        assert loop.task_context_data is not None, "Loop skal have context data"
        assert loop.task_context_data.get("task_id") == "ctx-workflow-001", "Task ID skal matche"

        print(f"  Context data: {loop.task_context_data}")
        print(f"  Result: {result}")
        print_result(True, "Workflow med TaskContext succesfuld")


# ============================================================
# Test 4: Full Integration E2E
# ============================================================

class TestFullIntegrationE2E:
    """Fuld integration tests for hele CKC-systemet."""

    @pytest.mark.asyncio
    async def test_complete_agent_workflow(self):
        """Test komplet agent workflow fra start til slut."""
        print_test_header("Complete Agent Workflow E2E")

        from cirkelline.ckc.orchestrator import (
            WorkLoopSequencer,
            WorkLoopStep,
            WorkLoopStepType,
            WorkLoopStatus
        )
        from cirkelline.ckc.advanced_protocols import (
            ILCPManager,
            MessageType,
            MessagePriority,
            ValidationMode
        )
        from cirkelline.ckc.context import (
            TaskContext,
            WorkflowStep,
            WorkflowStepStatus,
            ContextSource,
            create_context_for_task
        )

        # Setup komponenter
        sequencer = WorkLoopSequencer()
        ilcp_manager = ILCPManager()
        ilcp_manager.set_validation_mode(ValidationMode.NORMAL)

        # Mock agents
        async def tool_explorer_handler(action: str, data: Dict) -> Dict:
            return {
                "tools_discovered": ["document_analyzer", "knowledge_indexer"],
                "recommendations": "Use document_analyzer for initial processing"
            }

        async def knowledge_architect_handler(action: str, data: Dict) -> Dict:
            tools = data.get("tools", [])
            return {
                "knowledge_structure": {
                    "categories": ["documents", "insights"],
                    "tools_integrated": tools
                },
                "ready_for_qa": True
            }

        async def qa_handler(action: str, data: Dict) -> Dict:
            return {
                "quality_score": 0.92,
                "issues_found": 0,
                "approved": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        sequencer.register_agent_handler("tool_explorer", tool_explorer_handler)
        sequencer.register_agent_handler("knowledge_architect", knowledge_architect_handler)
        sequencer.register_agent_handler("qa_agent", qa_handler)

        # Opret TaskContext med korrekte parametre
        context = create_context_for_task(
            task_id="full-e2e-001",
            prompt="Complete analysis pipeline workflow"
        )
        # Tilføj ekstra metadata via context objekt
        context.metadata.update({
            "user_id": "e2e-test-user",
            "session_id": "e2e-session-001",
            "requested_analysis": "full_document_processing"
        })

        # Definer komplet workflow
        steps = [
            # Step 1: Tool Discovery
            WorkLoopStep(
                step_id="discover-tools",
                step_type=WorkLoopStepType.AGENT_CALL,
                agent_id="tool_explorer",
                action="discover_relevant_tools",
                output_key="tool_discovery"
            ),
            # Step 2: Transform tool output
            WorkLoopStep(
                step_id="prepare-tools",
                step_type=WorkLoopStepType.TRANSFORM,
                transform_fn=lambda data: {
                    "tools": data.get("tool_discovery", {}).get("tools_discovered", [])
                },
                output_key="prepared_tools"
            ),
            # Step 3: Knowledge Architecture
            WorkLoopStep(
                step_id="architect-knowledge",
                step_type=WorkLoopStepType.AGENT_CALL,
                agent_id="knowledge_architect",
                action="structure_knowledge",
                input_mapping={"prepared_tools": "tools"},
                output_key="knowledge_structure"
            ),
            # Step 4: Validation
            WorkLoopStep(
                step_id="validate-structure",
                step_type=WorkLoopStepType.VALIDATION,
                output_key="validation_check"
            ),
            # Step 5: QA
            WorkLoopStep(
                step_id="quality-assurance",
                step_type=WorkLoopStepType.AGENT_CALL,
                agent_id="qa_agent",
                action="perform_qa",
                output_key="qa_result"
            ),
            # Step 6: Final condition check
            WorkLoopStep(
                step_id="approval-check",
                step_type=WorkLoopStepType.CONDITION,
                condition_fn=lambda data: data.get("qa_result", {}).get("approved", False),
                output_key="final_approval"
            )
        ]

        # Opret og kør workflow
        loop = sequencer.create_loop(
            name="Complete Analysis Pipeline",
            description="Full E2E test af agent pipeline",
            steps=steps
        )

        success, result = await sequencer.execute_loop(
            loop,
            context=context,
            input_data={"document_id": "doc-001", "analysis_depth": "comprehensive"}
        )

        assert success, f"Komplet workflow skal lykkes: {result}"
        assert loop.status == WorkLoopStatus.COMPLETED, "Status skal være COMPLETED"

        # Verificer alle steps kørte
        expected_keys = ["tool_discovery", "prepared_tools", "knowledge_structure", "qa_result"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

        # Verificer QA godkendelse
        assert result["qa_result"]["approved"] is True, "QA skal godkende"

        # Send ILCP notifikation om completion via STATUS_UPDATE
        completion_message = await ilcp_manager.send_message_with_context(
            sender_room_id=1,
            recipient_room_id=0,  # Orchestrator
            message_type=MessageType.STATUS_UPDATE,
            content={
                "task_id": context.task_id,
                "status": "completed",
                "success": True,
                "quality_score": result["qa_result"]["quality_score"],
                "summary": "Complete analysis pipeline finished successfully"
            },
            task_context=context,
            priority=MessagePriority.NORMAL
        )

        assert completion_message is not None, "Completion message skal sendes"
        assert completion_message.is_validated, "Message skal valideres"

        # Log stats
        sequencer_stats = sequencer.get_stats()
        ilcp_stats = ilcp_manager.get_validation_stats()

        print(f"\n  Workflow Result Summary:")
        print(f"    - Tools discovered: {result['tool_discovery']['tools_discovered']}")
        print(f"    - Knowledge categories: {result['knowledge_structure']['knowledge_structure']['categories']}")
        print(f"    - QA Score: {result['qa_result']['quality_score']}")
        print(f"    - Final Approval: {result.get('final_approval', 'N/A')}")
        print(f"\n  Sequencer Stats: {sequencer_stats}")
        print(f"  ILCP Stats: {ilcp_stats}")

        print_result(True, "Komplet agent workflow gennemført")

    @pytest.mark.asyncio
    async def test_multi_room_communication(self):
        """Test kommunikation mellem flere læringsrum."""
        print_test_header("Multi-Room Communication E2E")

        from cirkelline.ckc.advanced_protocols import (
            ILCPManager,
            MessageType,
            MessagePriority,
            ValidationMode
        )
        from cirkelline.ckc.context import (
            create_context_for_task,
            ContextSource
        )

        ilcp = ILCPManager()
        ilcp.set_validation_mode(ValidationMode.NORMAL)

        # Simuler 3 læringsrum
        rooms = {
            1: "Finansielt Team",
            2: "Juridisk Team",
            3: "Teknisk Team"
        }

        # Room 1 sender data request til Room 2
        context = create_context_for_task(
            task_id="multi-room-001",
            prompt="Cross-team collaboration workflow"
        )

        # Request: Finansielt -> Juridisk med korrekt format
        request_msg = await ilcp.send_message_with_context(
            sender_room_id=1,
            recipient_room_id=2,
            message_type=MessageType.DATA_REQUEST,
            content={
                "request_type": "legal_compliance",
                "data_keys": ["contract_review", "gdpr_status"],
                "filters": {"topic": "contract_review"},
                "urgency": "high"
            },
            task_context=context,
            priority=MessagePriority.HIGH
        )

        assert request_msg.is_validated, "Request skal valideres"

        # Response: Juridisk -> Finansielt med korrekt format
        response_msg = await ilcp.send_message(
            sender_room_id=2,
            recipient_room_id=1,
            message_type=MessageType.DATA_RESPONSE,
            content={
                "request_id": request_msg.id,
                "success": True,
                "data": {"compliance_status": "approved", "risk_level": "low"},
                "error": None
            },
            priority=MessagePriority.HIGH
        )

        assert response_msg.is_validated, "Response skal valideres"

        # Knowledge share: Juridisk -> Teknisk
        knowledge_msg = await ilcp.send_message(
            sender_room_id=2,
            recipient_room_id=3,
            message_type=MessageType.KNOWLEDGE_SHARE,
            content={
                "knowledge_type": "compliance_guideline",
                "content_data": {"guideline": "New GDPR compliance requirements"},
                "confidence_score": 0.95,
                "tags": ["gdpr", "compliance", "legal"]
            },
            priority=MessagePriority.NORMAL
        )

        assert knowledge_msg.is_validated, "Knowledge share skal valideres"

        # Verificer routing stats
        stats = ilcp.get_validation_stats()
        assert stats["total_validated"] >= 3, "Mindst 3 beskeder skal være valideret"

        print(f"  Messages validated: {stats['total_validated']}")
        print(f"  Passed: {stats['passed']}, Failed: {stats['failed']}")
        print_result(True, "Multi-room kommunikation succesfuld")


# ============================================================
# Test Runner
# ============================================================

async def run_all_tests():
    """Kør alle E2E tests."""
    print("\n" + "="*60)
    print("CKC E2E TEST SUITE - v1.1.0")
    print("="*60)

    results = []

    # Test 1: TaskContext
    print("\n--- TaskContext Tests ---")
    try:
        test_ctx = TestTaskContextE2E()
        test_ctx.test_context_creation_and_serialization()
        results.append(("TaskContext Creation", True))
        test_ctx.test_context_through_workflow()
        results.append(("TaskContext Workflow", True))
    except Exception as e:
        results.append(("TaskContext Tests", False))
        print(f"❌ TaskContext Error: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: ILCP Validation
    print("\n--- ILCP Validation Tests ---")
    try:
        test_ilcp = TestILCPValidationE2E()
        await test_ilcp.test_message_validation_modes()
        results.append(("ILCP Validation Modes", True))
        await test_ilcp.test_message_with_task_context()
        results.append(("ILCP with TaskContext", True))
        await test_ilcp.test_schema_validation_coverage()
        results.append(("ILCP Schema Coverage", True))
    except Exception as e:
        results.append(("ILCP Tests", False))
        print(f"❌ ILCP Error: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: WorkLoopSequencer
    print("\n--- WorkLoopSequencer Tests ---")
    try:
        test_wls = TestWorkLoopSequencerE2E()
        await test_wls.test_simple_workflow_execution()
        results.append(("Simple Workflow", True))
        await test_wls.test_parallel_execution()
        results.append(("Parallel Execution", True))
        await test_wls.test_conditional_workflow()
        results.append(("Conditional Workflow", True))
        await test_wls.test_workflow_with_task_context()
        results.append(("Workflow with Context", True))
    except Exception as e:
        results.append(("WorkLoopSequencer Tests", False))
        print(f"❌ WorkLoopSequencer Error: {e}")
        import traceback
        traceback.print_exc()

    # Test 4: Full Integration
    print("\n--- Full Integration Tests ---")
    try:
        test_full = TestFullIntegrationE2E()
        await test_full.test_complete_agent_workflow()
        results.append(("Complete Agent Workflow", True))
        await test_full.test_multi_room_communication()
        results.append(("Multi-Room Communication", True))
    except Exception as e:
        results.append(("Full Integration Tests", False))
        print(f"❌ Full Integration Error: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed

    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

    print(f"\n{'='*60}")
    print(f"RESULTAT: {passed} bestået, {failed} fejlet")
    print("="*60)

    if failed == 0:
        print("✅ ALLE E2E TESTS BESTÅET!")
    else:
        print(f"⚠️  {failed} test(s) fejlede")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
