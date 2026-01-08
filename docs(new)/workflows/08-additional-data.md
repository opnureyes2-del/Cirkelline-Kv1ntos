# Passing Additional Data to Workflows

**AGNO Version:** 2.3.4
**Source:** https://docs.agno.com/basics/workflows/additional-data

---

## Introduction

The `additional_data` parameter allows you to pass extra information to workflow steps beyond the primary input message. This is useful for:

- Passing metadata (user preferences, context)
- Providing configuration options
- Sharing data that doesn't belong in the main message
- Implementing feature flags or conditional behavior

---

## Core Concept

```python
from agno.workflow import Workflow

workflow = Workflow(
    name="My Workflow",
    steps=[...],
)

# Pass additional data when running
response = workflow.run(
    input="Your message",
    additional_data={"key": "value", "config": {...}},
)
```

---

## How It Works

1. Pass `additional_data` dict when calling `run()` or `arun()`
2. Data is available in `StepInput.additional_data`
3. All steps in the workflow can access this data
4. Data persists throughout the workflow execution

---

## Basic Example

### Passing User Context

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput

# Define a custom function that uses additional data
def personalized_processor(step_input: StepInput) -> StepOutput:
    """Process with user context from additional_data"""
    message = step_input.input

    # Access additional data
    user_data = step_input.additional_data or {}
    user_name = user_data.get("user_name", "User")
    preferences = user_data.get("preferences", {})
    language = preferences.get("language", "en")

    # Use the data in processing
    response = f"""
    ## Personalized Response for {user_name}

    **Language:** {language}
    **Request:** {message}

    Processing your request with your preferences...
    """

    return StepOutput(content=response)


# Create workflow
workflow = Workflow(
    name="Personalized Workflow",
    steps=[
        Step(
            name="Personalized Processing",
            executor=personalized_processor,
        ),
    ],
)

# Run with additional data
response = workflow.run(
    input="Help me with my task",
    additional_data={
        "user_name": "Alice",
        "preferences": {
            "language": "en",
            "tone": "formal",
            "detail_level": "high",
        },
        "user_tier": "premium",
    },
)

print(response.content)
```

---

## Using Additional Data with Agents

### Injecting Context into Agent Instructions

```python
from agno.agent import Agent
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput

# Agent that will be called with context
content_writer = Agent(
    name="Content Writer",
    instructions="Write content based on the provided context.",
)


def context_aware_writer(step_input: StepInput) -> StepOutput:
    """Use additional_data to customize agent behavior"""
    message = step_input.input
    additional = step_input.additional_data or {}

    # Extract context
    target_audience = additional.get("audience", "general")
    content_style = additional.get("style", "informative")
    word_limit = additional.get("word_limit", 500)

    # Build enhanced prompt with context
    enhanced_prompt = f"""
    Write content for the following request:

    REQUEST: {message}

    CONTEXT:
    - Target Audience: {target_audience}
    - Content Style: {content_style}
    - Word Limit: {word_limit} words

    Create content that matches these specifications.
    """

    # Call agent with enhanced prompt
    response = content_writer.run(enhanced_prompt)

    return StepOutput(content=response.content)


workflow = Workflow(
    name="Context-Aware Content",
    steps=[
        Step(name="Write Content", executor=context_aware_writer),
    ],
)

# Run with audience context
response = workflow.run(
    input="Explain machine learning",
    additional_data={
        "audience": "beginners",
        "style": "friendly and approachable",
        "word_limit": 300,
    },
)
```

---

## Feature Flags Pattern

Use additional_data for feature flags and conditional behavior:

```python
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput

def feature_controlled_step(step_input: StepInput) -> StepOutput:
    """Execute different logic based on feature flags"""
    additional = step_input.additional_data or {}
    features = additional.get("features", {})

    result_parts = []

    # Check feature flags
    if features.get("enhanced_analysis", False):
        result_parts.append("Enhanced analysis enabled")
        # Do enhanced processing
    else:
        result_parts.append("Standard analysis")
        # Do standard processing

    if features.get("include_sources", False):
        result_parts.append("Sources will be included")
        # Add source citations

    if features.get("summary_mode", False):
        result_parts.append("Summary mode active")
        # Generate concise summary

    return StepOutput(content="\n".join(result_parts))


workflow = Workflow(
    name="Feature-Controlled Workflow",
    steps=[
        Step(name="Process", executor=feature_controlled_step),
    ],
)

# Premium user with all features
premium_response = workflow.run(
    input="Analyze this data",
    additional_data={
        "features": {
            "enhanced_analysis": True,
            "include_sources": True,
            "summary_mode": False,
        },
        "user_tier": "premium",
    },
)

# Free user with limited features
free_response = workflow.run(
    input="Analyze this data",
    additional_data={
        "features": {
            "enhanced_analysis": False,
            "include_sources": False,
            "summary_mode": True,
        },
        "user_tier": "free",
    },
)
```

---

## API Request Metadata

Pass request-level metadata through workflows:

```python
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput
import time

def audit_aware_step(step_input: StepInput) -> StepOutput:
    """Step that logs audit information"""
    additional = step_input.additional_data or {}

    # Extract audit metadata
    request_id = additional.get("request_id", "unknown")
    user_id = additional.get("user_id", "anonymous")
    client_ip = additional.get("client_ip", "unknown")
    timestamp = additional.get("timestamp", time.time())

    # Log for audit trail
    print(f"[AUDIT] Request: {request_id}")
    print(f"[AUDIT] User: {user_id}")
    print(f"[AUDIT] IP: {client_ip}")
    print(f"[AUDIT] Time: {timestamp}")

    # Process the request
    result = f"Processed request {request_id} for user {user_id}"

    return StepOutput(
        content=result,
        metadata={
            "request_id": request_id,
            "processed_at": time.time(),
        },
    )


workflow = Workflow(
    name="Audited Workflow",
    steps=[
        Step(name="Audit Step", executor=audit_aware_step),
    ],
)

# FastAPI integration example
# @app.post("/api/process")
# async def process_request(request: Request, body: ProcessRequest):
#     response = workflow.run(
#         input=body.message,
#         additional_data={
#             "request_id": str(uuid.uuid4()),
#             "user_id": request.state.user_id,
#             "client_ip": request.client.host,
#             "timestamp": time.time(),
#         },
#     )
#     return response
```

---

## Multi-Tenant Configuration

Support multiple tenants with different configurations:

```python
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput

# Tenant configurations
TENANT_CONFIGS = {
    "tenant_a": {
        "model": "gemini-2.5-flash",
        "max_tokens": 2000,
        "custom_instructions": "Be formal and professional.",
    },
    "tenant_b": {
        "model": "gemini-2.5-flash",
        "max_tokens": 4000,
        "custom_instructions": "Be friendly and casual.",
    },
}


def tenant_aware_step(step_input: StepInput) -> StepOutput:
    """Configure behavior based on tenant"""
    additional = step_input.additional_data or {}
    tenant_id = additional.get("tenant_id", "default")

    # Get tenant config
    config = TENANT_CONFIGS.get(tenant_id, {})

    model = config.get("model", "gemini-2.5-flash")
    max_tokens = config.get("max_tokens", 1000)
    instructions = config.get("custom_instructions", "")

    result = f"""
    Processing for Tenant: {tenant_id}
    Model: {model}
    Max Tokens: {max_tokens}
    Instructions: {instructions}
    """

    return StepOutput(content=result)


workflow = Workflow(
    name="Multi-Tenant Workflow",
    steps=[
        Step(name="Tenant Processing", executor=tenant_aware_step),
    ],
)

# Process for different tenants
response_a = workflow.run(
    input="Generate report",
    additional_data={"tenant_id": "tenant_a"},
)

response_b = workflow.run(
    input="Generate report",
    additional_data={"tenant_id": "tenant_b"},
)
```

---

## Using with Conditions and Routers

Additional data works with all workflow patterns:

```python
from agno.workflow import Workflow, Step
from agno.workflow.condition import Condition
from agno.workflow.router import Router
from agno.workflow.types import StepInput, StepOutput
from typing import List

# Condition using additional_data
def is_premium_user(step_input: StepInput) -> bool:
    """Check if user is premium from additional_data"""
    additional = step_input.additional_data or {}
    return additional.get("user_tier") == "premium"


# Router using additional_data
def route_by_department(step_input: StepInput) -> List[Step]:
    """Route based on department in additional_data"""
    additional = step_input.additional_data or {}
    department = additional.get("department", "general")

    if department == "sales":
        return [sales_step]
    elif department == "support":
        return [support_step]
    else:
        return [general_step]


# Define steps
premium_analysis_step = Step(name="Premium Analysis", agent=premium_agent)
sales_step = Step(name="Sales Handler", agent=sales_agent)
support_step = Step(name="Support Handler", agent=support_agent)
general_step = Step(name="General Handler", agent=general_agent)

# Workflow with conditional premium features
workflow = Workflow(
    name="Department Workflow",
    steps=[
        Router(
            name="Department Router",
            selector=route_by_department,
            choices=[sales_step, support_step, general_step],
        ),
        Condition(
            name="Premium Features",
            evaluator=is_premium_user,
            steps=[premium_analysis_step],
        ),
    ],
)

# Run with department and tier info
response = workflow.run(
    input="I need help with my order",
    additional_data={
        "department": "sales",
        "user_tier": "premium",
        "user_id": "user-123",
    },
)
```

---

## Async Execution with Additional Data

Works the same way in async contexts:

```python
import asyncio
from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput

async def async_processor(step_input: StepInput) -> StepOutput:
    """Async step using additional_data"""
    additional = step_input.additional_data or {}
    timeout = additional.get("timeout", 30)
    priority = additional.get("priority", "normal")

    # Simulate async processing
    await asyncio.sleep(0.1)

    return StepOutput(
        content=f"Processed with timeout={timeout}s, priority={priority}"
    )


workflow = Workflow(
    name="Async Workflow",
    steps=[
        Step(name="Async Process", executor=async_processor),
    ],
)


async def main():
    response = await workflow.arun(
        input="Process this",
        additional_data={
            "timeout": 60,
            "priority": "high",
            "async_context": True,
        },
    )
    print(response.content)


asyncio.run(main())
```

---

## Streaming with Additional Data

Additional data is available throughout streaming:

```python
from agno.workflow import Workflow, Step
from agno.run.workflow import WorkflowRunEvent

async def process_with_streaming():
    response_stream = workflow.arun(
        input="Generate report",
        stream=True,
        stream_events=True,
        additional_data={
            "include_charts": True,
            "format": "detailed",
            "user_preferences": {"theme": "dark"},
        },
    )

    async for event in response_stream:
        if event.event == WorkflowRunEvent.step_started.value:
            print(f"Step started: {event.step_id}")
        elif event.content:
            print(event.content, end="")
```

---

## StepInput.additional_data Reference

The `additional_data` field in StepInput:

```python
@dataclass
class StepInput:
    input: str                              # Primary input message
    previous_step_content: Optional[str]    # Previous step output
    previous_step_outputs: Dict[str, StepOutput]  # All outputs by name
    additional_data: Optional[Dict[str, Any]]     # Extra data passed in
```

### Accessing Safely

```python
def safe_access_step(step_input: StepInput) -> StepOutput:
    """Safe pattern for accessing additional_data"""

    # Always default to empty dict
    additional = step_input.additional_data or {}

    # Use .get() with defaults
    user_id = additional.get("user_id", "anonymous")
    config = additional.get("config", {})
    features = additional.get("features", [])

    # Nested access with defaults
    theme = config.get("theme", "light")

    return StepOutput(content=f"User: {user_id}, Theme: {theme}")
```

---

## Best Practices

### Do's

1. **Always provide defaults**
   ```python
   additional = step_input.additional_data or {}
   value = additional.get("key", "default")
   ```

2. **Use meaningful keys**
   ```python
   # Good
   additional_data={"user_tier": "premium", "request_id": "abc123"}

   # Bad
   additional_data={"t": "p", "r": "abc123"}
   ```

3. **Document expected structure**
   ```python
   def my_step(step_input: StepInput) -> StepOutput:
       """
       Expected additional_data:
       - user_id: str (required)
       - preferences: dict (optional)
       - features: list[str] (optional)
       """
   ```

4. **Keep data serializable**
   ```python
   # Good - JSON-serializable
   additional_data={"count": 5, "name": "test", "enabled": True}

   # Bad - not serializable
   additional_data={"callback": lambda x: x, "object": SomeClass()}
   ```

### Don'ts

1. **Don't put sensitive data directly**
   ```python
   # Bad - secrets in data
   additional_data={"api_key": "sk-xxx", "password": "123"}

   # Better - reference to secrets
   additional_data={"secret_ref": "vault://api-key"}
   ```

2. **Don't use for primary input**
   ```python
   # Bad - message in additional_data
   workflow.run(input="", additional_data={"message": "actual input"})

   # Good - message in input
   workflow.run(input="actual input", additional_data={"context": "extra"})
   ```

3. **Don't assume data exists**
   ```python
   # Bad - will crash if missing
   user_id = step_input.additional_data["user_id"]

   # Good - safe access
   user_id = (step_input.additional_data or {}).get("user_id")
   ```

---

## Summary

| Use Case | Pattern |
|----------|---------|
| **User Context** | Pass user info for personalization |
| **Feature Flags** | Control behavior based on flags |
| **Audit Metadata** | Include request_id, user_id, timestamps |
| **Multi-Tenant** | Tenant-specific configurations |
| **API Integration** | Pass request context through workflow |

---

## Related Documentation

- **Building Workflows:** `docs(new)/workflows/02-building-workflows.md`
- **Running Workflows:** `docs(new)/workflows/03-running-workflows.md`
- **Conditional Patterns:** `docs(new)/workflows/05-conditional-parallel.md`

---

*Last Updated: December 2025 | AGNO 2.3.4*
