import { useCallback } from 'react'
import { getSessionAPI, getAllSessionsAPI } from '@/api/os'
import { useStore } from '../store'
import { toast } from 'sonner'
import { ChatMessage, ToolCall, ReasoningMessage, ChatEntry } from '@/types/os'
import { getJsonMarkdown } from '@/lib/utils'
import { useAuth } from '@/contexts/AuthContext'

interface SessionResponse {
  session_id: string
  agent_id: string
  user_id: string | null
  runs?: ChatEntry[]
  memory: {
    runs?: ChatEntry[]
    chats?: ChatEntry[]
  }
  agent_data: Record<string, unknown>
}

interface LoaderArgs {
  entityType: 'agent' | 'team' | null
  agentId?: string | null
  teamId?: string | null
  dbId: string | null
}

const useSessionLoader = () => {
  const { getUserId } = useAuth()
  const setMessages = useStore((state) => state.setMessages)
  const selectedEndpoint = useStore((state) => state.selectedEndpoint)
  const setIsSessionsLoading = useStore((state) => state.setIsSessionsLoading)
  const setSessionsData = useStore((state) => state.setSessionsData)

  const getSessions = useCallback(
    async ({ entityType, agentId, teamId, dbId }: LoaderArgs) => {
      const selectedId = entityType === 'agent' ? agentId : teamId
      if (!selectedEndpoint || !entityType || !selectedId || !dbId) return

      try {
        setIsSessionsLoading(true)

        const userId = getUserId()
        console.log('🔑 getUserId() returned:', userId)
        console.log('📡 Calling API with:', {
          endpoint: selectedEndpoint,
          type: entityType,
          componentId: selectedId,
          dbId: dbId,
          userId: userId
        })

        const sessions = await getAllSessionsAPI(
          selectedEndpoint,
          entityType,
          selectedId,
          dbId,
          userId
        )
        console.log('Fetched sessions:', sessions)

        // ✅ CRITICAL: Merge fetched sessions with optimistically added ones
        // This prevents sessions from disappearing before database save completes
        setSessionsData((prevSessions) => {
          // ✅ CRITICAL FIX: Convert ISO date strings to Unix timestamps for sidebar display
          const fetchedSessions = (sessions.data ?? []).map(session => {
            // Convert created_at from ISO string to Unix timestamp (seconds)
            const created_at = typeof session.created_at === 'string'
              ? new Date(session.created_at).getTime() / 1000
              : session.created_at

            // Convert updated_at if present
            const updated_at = session.updated_at
              ? (typeof session.updated_at === 'string'
                  ? new Date(session.updated_at).getTime() / 1000
                  : session.updated_at)
              : undefined

            return {
              ...session,
              created_at,
              updated_at
            }
          })

          const fetchedSessionIds = new Set(fetchedSessions.map(s => s.session_id))

          // Keep optimistically added sessions that aren't in database yet
          const optimisticSessions = prevSessions?.filter(
            s => !fetchedSessionIds.has(s.session_id)
          ) ?? []

          // Combine optimistic + fetched sessions
          return [...optimisticSessions, ...fetchedSessions]
        })
      } catch {
        toast.error('Error loading sessions')
        setSessionsData([])
      } finally {
        setIsSessionsLoading(false)
      }
    },
    [selectedEndpoint, setSessionsData, setIsSessionsLoading, getUserId]
  )

  const getSession = useCallback(
    async (
      { entityType, agentId, teamId, dbId }: LoaderArgs,
      sessionId: string
    ) => {
      const selectedId = entityType === 'agent' ? agentId : teamId
      if (
        !selectedEndpoint ||
        !sessionId ||
        !entityType ||
        !selectedId ||
        !dbId
      )
        return
      console.log(entityType)

      try {
        const response: SessionResponse = await getSessionAPI(
          selectedEndpoint,
          entityType,
          sessionId,
          dbId
        )
        console.log('Fetched session:', response)
        console.log('=== SESSION DEBUG ===')
        console.log('Full response:', response)
        if (Array.isArray(response)) {
          console.log('Number of runs:', response.length)
          console.log('First run keys:', Object.keys(response[0] || {}))
          console.log('First run created_at:', response[0]?.created_at)
          console.log('First run updated_at:', response[0]?.updated_at)
          console.log('Second run:', response[1])
        } else {
          console.log('Number of runs:', response?.runs?.length || response?.memory?.runs?.length)
        }
        console.log('===================')
        if (response) {
          if (Array.isArray(response)) {
            const allMessages: ChatMessage[] = []

            // ✅ CRITICAL FIX: Sort runs by created_at timestamp FIRST!
            // API returns ISO strings like '2025-10-28T12:26:59Z', convert and compare
            const sortedRuns = [...response].sort((a, b) => {
              const timeA = typeof a.created_at === 'string' ? new Date(a.created_at).getTime() : a.created_at * 1000;
              const timeB = typeof b.created_at === 'string' ? new Date(b.created_at).getTime() : b.created_at * 1000;
              return timeA - timeB;
            })

            sortedRuns.forEach((run, runIndex) => {
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              const anyRun = run as any

              // Extract team_name and agent_name from events
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              const teamNameFromEvents = anyRun.events?.find((e: any) => e.team_name)?.team_name
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              const agentNameFromEvents = anyRun.events?.find((e: any) => e.agent_name)?.agent_name

              console.log(`🔍 RUN ${runIndex}:`, {
                run_input: (run.run_input as string)?.substring(0, 100),
                content: (run.content as string)?.substring(0, 100),
                team_name: teamNameFromEvents,
                agent_name: agentNameFromEvents,
                run_id: anyRun.run_id || anyRun.id,
                tools_count: run.tools?.length ?? 0,
                created_at: run.created_at,
                has_member_responses: !!anyRun.member_responses,
                member_responses_count: anyRun.member_responses?.length ?? 0,
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                delegation_tools: run.tools?.filter((t: any) => t.tool_name === 'delegate_task_to_member').map((t: any) => ({
                  member_id: t.tool_args?.member_id,
                  member_name: t.tool_args?.member_name,
                  task_description: t.tool_args?.task_description?.substring(0, 50)
                }))
              })

              if (run) {
                // ✅ CRITICAL FIX: API returns ISO string '2025-10-28T12:26:59Z', convert to Unix seconds!
                let runTimestamp: number;
                if (typeof run.created_at === 'string') {
                  // Convert ISO string to Unix seconds
                  runTimestamp = new Date(run.created_at).getTime() / 1000;
                  console.log(`🔍 Run ${runIndex}: Converted '${run.created_at}' → ${runTimestamp} Unix seconds`);
                } else {
                  // Already a number (Unix seconds)
                  runTimestamp = run.created_at || Date.now() / 1000;
                  console.log(`🔍 Run ${runIndex}: Already Unix seconds: ${runTimestamp}`);
                }

                // ✅ CRITICAL FIX: Only add user messages from TOP-LEVEL runs (parent_run_id is null/empty)
                // Child runs are delegations and should NOT appear as user messages
                const isTopLevelRun = !anyRun.parent_run_id || anyRun.parent_run_id === null || anyRun.parent_run_id === '';
                const userContent = run.run_input ?? '';

                if (isTopLevelRun && userContent) {
                  allMessages.push({
                    role: 'user',
                    content: userContent,
                    created_at: runTimestamp
                  })
                  console.log(`  → Added user message from TOP-LEVEL run ${runIndex}: "${userContent.substring(0, 50)}..."`)
                } else if (!isTopLevelRun) {
                  console.log(`  ⏭️  Skipped child run ${runIndex} (parent: ${anyRun.parent_run_id})`)
                }

                // ✅ FIXED: Handle delegations based on team hierarchy
                // Top-level teams (Cirkelline) don't have their delegations in events[]
                // Sub-teams (Research Team) have their delegations in events[]
                
                const allEvents = anyRun.events ?? [];
                
                console.log(`  🔍 DELEGATION LOGIC:`, {
                  teamName: teamNameFromEvents,
                  parent_run_id: anyRun.parent_run_id,
                  events_count: allEvents.length
                });
                
                const isTopLevelTeam = teamNameFromEvents === 'Cirkelline';
                
                console.log(`  🔍 isTopLevelTeam:`, isTopLevelTeam);
                console.log(`  🔍 parent_run_id value:`, anyRun.parent_run_id);
                console.log(`  🔍 parent_run_id is empty:`, !anyRun.parent_run_id);
                
                // Check for both null AND empty string
                if (isTopLevelTeam && !anyRun.parent_run_id) {
                  // ✅ For Cirkelline (top-level team), infer delegation from the existence of child runs
                  // Don't extract from events[] as those contain nested sub-delegations
                  console.log(`  🔍 Top-level team detected: ${teamNameFromEvents}`);
                  
                  // Check if there are other runs with this run as parent
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const hasChildRuns = response.some((r: any) =>
                    r.parent_run_id === (anyRun.run_id || anyRun.id)
                  );
                  
                  if (hasChildRuns) {
                    // Cirkelline delegated to a sub-team, show this delegation
                    // We know it's Research Team from the context
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    const childRun = response.find((r: any) =>
                      r.parent_run_id === (anyRun.run_id || anyRun.id)
                    );
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    const childTeamName = (childRun as any)?.events?.find((e: any) => e.team_name)?.team_name || 'sub-team';
                    
                    allMessages.push({
                      role: 'delegation',
                      content: `**Delegating to ${childTeamName}:**\n\n${(run.run_input as string) || 'Complete the task'}`,
                      created_at: runTimestamp + 1, // Slightly after run starts
                      isDelegation: true,
                      delegatedTo: childTeamName,
                      delegationTask: (run.run_input as string) || 'Complete the task',
                      teamName: teamNameFromEvents,
                      teamId: anyRun.team_id,
                      runId: anyRun.run_id || anyRun.id,
                      parentRunId: anyRun.parent_run_id
                    });
                    
                    console.log(`  → Added top-level delegation to ${childTeamName}`);
                  }
                } else {
                  // ✅ For sub-teams (Research Team), extract delegations from events[]
                  console.log(`  🔍 Sub-team detected: ${teamNameFromEvents}, extracting delegations from events...`);
                  console.log(`  🔍 All events sample:`, allEvents.slice(0, 2));
                  
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const delegationEvents = allEvents.filter((event: any) => {
                    // member_id is inside tool.tool_args, not at top level!
                    const memberId = event.tool?.tool_args?.member_id;
                    const isDelegation = event.event === 'TeamToolCallStarted' && !!memberId;
                    if (event.event === 'TeamToolCallStarted') {
                      console.log(`  🔍 TeamToolCallStarted event:`, {
                        event: event.event,
                        member_id_path: 'tool.tool_args.member_id',
                        member_id: memberId,
                        isDelegation,
                        full_tool: event.tool
                      });
                    }
                    return isDelegation;
                  });
                  
                  console.log(`  🔍 Found ${delegationEvents.length} delegation events`);

                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  delegationEvents.forEach((event: any) => {
                    // Extract member_id from tool.tool_args
                    const memberId = event.tool?.tool_args?.member_id;
                    
                    // Map member IDs to display names
                    const memberNameMap: Record<string, string> = {
                      'research-team': 'Research Team',
                      'law-team': 'Law Team',
                      'web-researcher': 'Web Researcher',
                      'research-analyst': 'Research Analyst',
                      'legal-researcher': 'Legal Researcher',
                      'legal-analyst': 'Legal Analyst'
                    };
                    const memberName = memberNameMap[memberId] || memberId;

                    // Task description is in the run_input of this run
                    const taskDescription = `Working on: ${(run.run_input as string)?.substring(0, 100) || 'task'}...`;

                    allMessages.push({
                      role: 'delegation',
                      content: `**Delegating to ${memberName}:**\n\n${taskDescription}`,
                      created_at: event.created_at || runTimestamp,
                      isDelegation: true,
                      delegatedTo: memberName,
                      delegationTask: taskDescription,
                      teamName: teamNameFromEvents,
                      teamId: anyRun.team_id,
                      runId: anyRun.run_id || anyRun.id,
                      parentRunId: anyRun.parent_run_id
                    });

                    console.log(`  → Added delegation to ${memberName} at ${event.created_at}`);
                  });
                  
                  // ✅ Extract member agent RESPONSES from TeamToolCallCompleted events
                  // The response is in tool.result field!
                  console.log(`  🔍 Extracting member responses from TeamToolCallCompleted events...`);
                  
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const completedEvents = allEvents.filter((event: any) =>
                    event.event === 'TeamToolCallCompleted' &&
                    event.tool?.result &&
                    event.tool?.tool_args?.member_id  // ← member_id is in tool_args!
                  );
                  
                  console.log(`  🔍 Found ${completedEvents.length} TeamToolCallCompleted events with results`);
                  
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  completedEvents.forEach((event: any) => {
                    // member_id is in tool.tool_args, not at tool level!
                    const memberId = event.tool.tool_args.member_id;
                    const response = event.tool.result;
                    
                    // Map member IDs to display names
                    const memberNameMap: Record<string, string> = {
                      'research-team': 'Research Team',
                      'law-team': 'Law Team',
                      'web-researcher': 'Web Researcher',
                      'research-analyst': 'Research Analyst',
                      'legal-researcher': 'Legal Researcher',
                      'legal-analyst': 'Legal Analyst'
                    };
                    const memberName = memberNameMap[memberId] || memberId;
                    
                    allMessages.push({
                      role: 'agent',
                      content: typeof response === 'string' ? response : getJsonMarkdown(response),
                      created_at: event.created_at || runTimestamp,
                      agentName: memberName,
                      agentId: memberId,
                      teamName: teamNameFromEvents,
                      teamId: anyRun.team_id,
                      runId: event.child_run_id || anyRun.run_id || anyRun.id,
                      parentRunId: anyRun.run_id || anyRun.id
                    });
                    
                    console.log(`  → Added member response from ${memberName} at ${event.created_at}`);
                  });
                }

                // ✅ NEW: Extract member responses from member_responses[] field (AGNO official storage)
                // This is where AGNO stores member agent responses when store_member_responses=True
                console.log(`  🔍 DEBUG: Checking for member_responses field...`);
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const memberResponses = (anyRun as any).member_responses;
                console.log(`  🔍 member_responses exists:`, !!memberResponses);
                console.log(`  🔍 member_responses is array:`, Array.isArray(memberResponses));
                console.log(`  🔍 member_responses length:`, memberResponses?.length || 0);
                console.log(`  🔍 member_responses data:`, memberResponses);
                
                if (memberResponses && Array.isArray(memberResponses)) {
                  console.log(`  ✅ Found ${memberResponses.length} member responses in member_responses field`);

                  // Map agent_id to display names
                  const agentIdToNameMap: Record<string, string> = {
                    'web-researcher': 'Web Researcher',
                    'research-analyst': 'Research Analyst',
                    'legal-researcher': 'Legal Researcher',
                    'legal-analyst': 'Legal Analyst'
                  };

                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  memberResponses.forEach((memberResponse: any, idx: number) => {
                    console.log(`  🔍 MEMBER RESPONSE ${idx}:`, {
                      agent_id: memberResponse.agent_id,
                      agent_name: memberResponse.agent_name,
                      created_at: memberResponse.created_at,
                      has_content: !!memberResponse.content,
                      content_length: memberResponse.content?.length || 0
                    });
                    
                    // Database stores agent_id (NOT agent_name)
                    const agentId = memberResponse.agent_id || memberResponse.agent_name || 'unknown';
                    const agentName = agentIdToNameMap[agentId] || agentId;
                    const responseContent = memberResponse.content || memberResponse.response || '';

                    console.log(`  🔍 Extracted agentId: "${agentId}", agentName: "${agentName}"`);

                    if (responseContent) {
                      // ✅ FIXED: Use member response's ACTUAL timestamp (when agent actually responded!)
                      const memberResponseTimestamp = memberResponse.created_at || runTimestamp;

                      console.log(`  🔍 Adding member response with timestamp: ${memberResponseTimestamp}`);

                      allMessages.push({
                        role: 'agent',
                        content: responseContent,
                        created_at: memberResponseTimestamp,
                        agentName: agentName,
                        agentId: agentId,
                        teamName: teamNameFromEvents,
                        teamId: anyRun.team_id,
                        runId: memberResponse.run_id || anyRun.run_id || anyRun.id,
                        parentRunId: anyRun.run_id || anyRun.id
                      });
                      console.log(`  → Added member response from ${agentName} at ${memberResponseTimestamp}`);
                    } else {
                      console.log(`  ⚠️ SKIPPED: No content for ${agentName}`);
                    }
                  });
                } else {
                  console.log(`  ⚠️ No member_responses found in this run`);
                }

                // ✅ Add the run's main content (team response)
                if (run.content && (run.content as string).trim()) {
                  console.log(`  🔍 DEBUG: Processing run.content...`);
                  console.log(`  🔍 Content length:`, (run.content as string).length);
                  console.log(`  🔍 Team name:`, teamNameFromEvents);
                  
                  // Filter out internal tool calls that shouldn't be displayed as badges
                  const shouldDisplayTool = (toolName: string) => {
                    const hiddenTools = [
                      'think',
                      'analyze',
                      'delegate_task_to_member',
                      'reasoning_step'
                    ];
                    return !hiddenTools.includes(toolName);
                  };

                  const toolCalls = [
                    ...(run.tools ?? []).filter((tool: ToolCall) =>
                      tool.tool_name && shouldDisplayTool(tool.tool_name)
                    ),
                    ...(run.extra_data?.reasoning_messages ?? []).reduce(
                      (acc: ToolCall[], msg: ReasoningMessage) => {
                        if (msg.role === 'tool' && msg.tool_name && shouldDisplayTool(msg.tool_name)) {
                          acc.push({
                            role: msg.role,
                            content: msg.content,
                            tool_call_id: msg.tool_call_id ?? '',
                            tool_name: msg.tool_name ?? '',
                            tool_args: msg.tool_args ?? {},
                            tool_call_error: msg.tool_call_error ?? false,
                            metrics: msg.metrics ?? { time: 0 },
                            created_at: msg.created_at ?? Math.floor(Date.now() / 1000)
                          })
                        }
                        return acc
                      },
                      []
                    )
                  ]

                  // ✅ FIXED: Use TeamRunCompleted event for content timestamp (when content was FINISHED)
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  const completedEvent = allEvents.find((e: any) =>
                    e.event === 'TeamRunCompleted' || e.event === 'RunCompleted'
                  );
                  const contentTimestamp = completedEvent?.created_at || runTimestamp;

                  console.log(`  🔍 Completed event found:`, !!completedEvent);
                  console.log(`  🔍 Completed event created_at:`, completedEvent?.created_at);
                  console.log(`  🔍 Using content timestamp: ${contentTimestamp} (vs run timestamp: ${runTimestamp})`);

                  const content = (run.content as string);

                  allMessages.push({
                    role: 'agent',
                    content: content,
                    tool_calls: toolCalls.length > 0 ? toolCalls : undefined,
                    extra_data: run.extra_data,
                    images: run.images,
                    videos: run.videos,
                    audio: run.audio,
                    response_audio: run.response_audio,
                    created_at: contentTimestamp,
                    teamName: teamNameFromEvents,
                    teamId: anyRun.team_id,
                    agentName: agentNameFromEvents,
                    agentId: anyRun.agent_id,
                    runId: anyRun.run_id || anyRun.id,
                    parentRunId: anyRun.parent_run_id
                  });
                  
                  console.log(`  → Added content from ${teamNameFromEvents || agentNameFromEvents} at ${contentTimestamp}`);
                }
              }
            })

            // ✅ SIMPLE: Just use all messages, no reordering!
            const messagesFor = allMessages;

            const processedMessages = messagesFor.map(
              (message: ChatMessage) => {
                if (Array.isArray(message.content)) {
                  const textContent = message.content
                    .filter((item: { type: string }) => item.type === 'text')
                    .map((item) => item.text)
                    .join(' ')

                  return {
                    ...message,
                    content: textContent
                  }
                }
                if (typeof message.content !== 'string') {
                  return {
                    ...message,
                    content: getJsonMarkdown(message.content)
                  }
                }
                return message
              }
            )

            // Sort by numeric timestamp
            const sortedMessages = processedMessages.sort((a, b) =>
              a.created_at - b.created_at
            );

            setMessages(sortedMessages)
            return sortedMessages
          }
        }
      } catch {
        return null
      }
    },
    [selectedEndpoint, setMessages]
  )

  return { getSession, getSessions }
}

export default useSessionLoader
