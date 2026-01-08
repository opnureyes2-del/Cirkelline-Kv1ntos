# Chat Message Flow - Complete Reference

**Last Updated:** 2025-10-28
**Status:** ✅ Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Flow](#data-flow)
4. [Streaming Messages](#streaming-messages)
5. [Session Reload](#session-reload)
6. [Behind the Scenes Feature](#behind-the-scenes-feature)
7. [Data Structures](#data-structures)
8. [Common Pitfalls](#common-pitfalls)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The chat message system in Cirkelline displays conversations between users and AI teams/agents. Messages flow through two distinct paths:

1. **Real-time Streaming**: During active conversations (WebSocket-like SSE streaming)
2. **Session Reload**: When loading historical conversations from the database

Both paths must produce **identical results** with the same message order, timestamps, and content.

---

## Architecture

### Frontend Components

- **[`useAIStreamHandler.tsx`](../cirkelline-ui/src/hooks/useAIStreamHandler.tsx)**: Handles real-time streaming
- **[`useSessionLoader.tsx`](../cirkelline-ui/src/hooks/useSessionLoader.tsx)**: Loads historical sessions
- **[`store.ts`](../cirkelline-ui/src/store.ts)**: Zustand store for message state

### Backend (AGNO Framework)

- Processes user messages through teams/agents
- Generates SSE events during streaming
- Stores runs, events, and responses in PostgreSQL
- Returns historical data via `/sessions/{session_id}` endpoint

---

## Data Flow

### 1. User Sends Message

```
User Input → Frontend → POST /teams/{team_id}/run
                        ↓
                   Backend processes with AGNO
                        ↓
                   SSE Stream Events → Frontend displays in real-time
                        ↓
                   Data stored in PostgreSQL
```

### 2. User Refreshes Page

```
Page Load → Frontend → GET /sessions/{session_id}
                       ↓
                  PostgreSQL returns historical data
                       ↓
                  Frontend reconstructs messages
                       ↓
                  Display (must match streaming exactly!)
```

---

## Streaming Messages

### How It Works

1. User sends message via [`handleStreamResponse()`](../cirkelline-ui/src/hooks/useAIStreamHandler.tsx:140)
2. Backend streams SSE events in real-time
3. Frontend processes each event and updates UI

### Event Types

| Event | Description | Contains |
|-------|-------------|----------|
| `TeamToolCallStarted` | Team delegates to member | Tool call details, member_id |
| `TeamToolCallCompleted` | Member finishes work | Tool result with member's response |
| `RunContent` | Agent generates content | Partial or full response text |
| `TeamRunContent` | Team generates content | Partial or full response text |
| `TeamRunCompleted` | Team finishes entire run | Final content, completion time |

### Processing Events

**Key Code: [`useAIStreamHandler.tsx:212`](../cirkelline-ui/src/hooks/useAIStreamHandler.tsx:212)**

```typescript
onChunk: (chunk: RunResponse) => {
  // Handle delegations
  if (chunk.event === RunEvent.TeamToolCallStarted) {
    // Create delegation message
    const taskDescription = chunk.tool.tool_args?.task_description;
    const memberId = chunk.tool.tool_args?.member_id;
    
    addMessage({
      role: 'delegation',
      content: `**Delegating to ${memberName}:**\n\n${taskDescription}`,
      created_at: Math.floor(Date.now() / 1000),  // ✅ UNIX SECONDS!
      isDelegation: true,
      delegatedTo: memberName,
      teamName: chunk.team_name,
      runId: chunk.run_id
    });
  }
  
  // Handle content
  if (chunk.event === RunEvent.TeamRunContent) {
    addMessage({
      role: 'agent',
      content: chunk.content,
      created_at: Math.floor(Date.now() / 1000),  // ✅ UNIX SECONDS!
      teamName: chunk.team_name,
      runId: chunk.run_id
    });
  }
}
```

### Critical Rules for Streaming

1. **ALWAYS use `Math.floor(Date.now() / 1000)` for timestamps** (Unix seconds, not milliseconds)
2. **Extract member_id from `chunk.tool.tool_args.member_id`** (not `chunk.member_id`)
3. **Filter out internal tools** (think, analyze, delegate_task_to_member badges)
4. **Show delegation banners separately** from tool call badges

---

## Session Reload

### How It Works

When user refreshes or opens a historical session:

1. Frontend calls [`getSession()`](../cirkelline-ui/src/hooks/useSessionLoader.tsx:72)
2. Backend returns array of `runs[]` from PostgreSQL
3. Frontend extracts messages from run data
4. Messages sorted by `created_at` timestamp

### API Response Structure

```typescript
// GET /sessions/{session_id} returns:
[
  {
    run_id: "69c0486f-cd29-4843-b703-52c391604ecf",
    parent_run_id: "",  // Empty string for top-level runs
    team_id: "cirkelline",
    content: "Final response text...",
    run_input: "User's message",
    created_at: "2025-10-28T15:11:09Z",  // ISO 8601 string
    events: [
      {
        event: "TeamToolCallStarted",
        created_at: 1761664275,  // Unix seconds
        tool: {
          tool_name: "delegate_task_to_member",
          tool_args: {
            member_id: "research-team",
            task_description: "Research about..."
          }
        }
      },
      {
        event: "TeamToolCallCompleted",
        created_at: 1761664301,  // Unix seconds
        tool: {
          tool_name: "delegate_task_to_member",
          tool_args: {
            member_id: "web-researcher",
            task_description: "Research..."
          },
          result: "Here's what I found..."  // ← MEMBER'S RESPONSE!
        }
      },
      {
        event: "TeamRunCompleted",
        created_at: 1761664352  // ← ACTUAL COMPLETION TIME!
      }
    ]
  }
]
```

### Extracting Messages

**Key Code: [`useSessionLoader.tsx:121`](../cirkelline-ui/src/hooks/useSessionLoader.tsx:121)**

```typescript
sortedRuns.forEach((run) => {
  const allEvents = run.events ?? [];
  
  // 1. Convert timestamps from ISO to Unix seconds
  let runTimestamp: number;
  if (typeof run.created_at === 'string') {
    runTimestamp = new Date(run.created_at).getTime() / 1000;
  }
  
  // 2. Add user message (once)
  if (!userMessageAdded) {
    allMessages.push({
      role: 'user',
      content: run.run_input,
      created_at: runTimestamp
    });
    userMessageAdded = true;
  }
  
  // 3. Extract delegations from events[]
  const delegationEvents = allEvents.filter(event =>
    event.event === 'TeamToolCallStarted' && 
    event.tool?.tool_args?.member_id  // ✅ Correct path!
  );
  
  delegationEvents.forEach(event => {
    const memberId = event.tool.tool_args.member_id;
    const taskDescription = event.tool.tool_args.task_description;
    
    allMessages.push({
      role: 'delegation',
      content: `**Delegating to ${memberName}:**\n\n${taskDescription}`,
      created_at: event.created_at,  // ✅ Use event's timestamp!
      delegatedTo: memberName
    });
  });
  
  // 4. Extract member responses from TeamToolCallCompleted events
  const completedEvents = allEvents.filter(event => 
    event.event === 'TeamToolCallCompleted' && 
    event.tool?.result &&
    event.tool?.tool_args?.member_id
  );
  
  completedEvents.forEach(event => {
    const memberId = event.tool.tool_args.member_id;
    const response = event.tool.result;
    
    allMessages.push({
      role: 'agent',
      content: response,  // ✅ Full response text!
      created_at: event.created_at,  // ✅ Actual completion time!
      agentName: memberName,
      runId: event.child_run_id
    });
  });
  
  // 5. Add run's main content (team's final synthesis)
  if (run.content && run.content.trim()) {
    // Use TeamRunCompleted event for accurate timestamp
    const completedEvent = allEvents.find(e => 
      e.event === 'TeamRunCompleted'
    );
    const contentTimestamp = completedEvent?.created_at || runTimestamp;
    
    allMessages.push({
      role: 'agent',
      content: run.content,
      created_at: contentTimestamp,  // ✅ When content was FINISHED!
      teamName: teamName
    });
  }
});

// 6. Sort all messages by timestamp
const sortedMessages = allMessages.sort((a, b) => 
  a.created_at - b.created_at
);
```

### Critical Rules for Reload

1. **Convert ISO timestamps to Unix seconds**: `new Date(iso).getTime() / 1000`
2. **Extract delegations from `events[]` array** (not `tools[]`)
3. **Member responses are in `TeamToolCallCompleted.tool.result`** (not a separate field)
4. **Use event timestamps, not run timestamp** for accurate timing
5. **Always sort by `created_at` before displaying**

---

## Behind the Scenes Feature

### Overview

The "Behind the Scenes" feature provides a collapsible view of intermediate AI work, showing delegations and agent responses in a clean, unobtrusive way.

### User Experience

**Default (Collapsed):**
```
User: "research about AI news"  Just now
┌──────────────────────────────────┐
│ ▶ Show Behind the Scenes (7 steps) │
└──────────────────────────────────┘
Cirkelline: Here's what I found...  5s ago
```

**Expanded:**
```
User: "research about AI news"  Just now
┌──────────────────────────────────────────────┐
│ ▼ Hide Behind the Scenes (7 steps)           │
│                                               │
│ Cirkelline is delegating to Research Team  5s ago
│ Research Team is delegating to Web Researcher  6s ago
│                                               │
│ Web Researcher  12min ago                     │
│ Here's what I found about AI...              │
│                                               │
│ Research Analyst  15min ago                   │
│ After analyzing the data...                  │
│                                               │
│ Research Team  20min ago                      │
│ Based on our research...                     │
└──────────────────────────────────────────────┘
Cirkelline: Here's what I found...  5s ago
```

### Implementation

**Components:**
- **[`BehindTheScenes.tsx`](../cirkelline-ui/src/components/chat/ChatArea/Messages/BehindTheScenes.tsx)** - Collapsible container
- **[`Messages.tsx`](../cirkelline-ui/src/components/chat/ChatArea/Messages/Messages.tsx)** - Message grouping

**Grouping Logic:**
```typescript
interface ConversationTurn {
  userMessage: ChatMessage;
  intermediateWork: ChatMessage[];  // Delegations + agent responses
  finalAnswer: ChatMessage | null;  // Cirkelline's response
}
```

Messages are grouped into turns where each turn contains:
1. User's question
2. All intermediate work (collapsed in Behind the Scenes)
3. Cirkelline's final answer

**Extraction from Events:**

Delegations extracted from `TeamToolCallStarted` events:
```typescript
const delegationEvents = allEvents.filter(event =>
  event.event === 'TeamToolCallStarted' &&
  event.tool?.tool_args?.member_id
);
```

Member responses extracted from `TeamToolCallCompleted` events:
```typescript
const completedEvents = allEvents.filter(event =>
  event.event === 'TeamToolCallCompleted' &&
  event.tool?.result &&
  event.tool?.tool_args?.member_id
);

// Response is in: event.tool.result
```

### Relative Timestamps

All timestamps use friendly relative format:

```typescript
const formatRelativeTime = (timestamp: number) => {
  const now = Math.floor(Date.now() / 1000);
  const diff = now - timestamp;
  
  if (diff < 10) return 'Just now';
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return `${Math.floor(diff / 604800)}w ago`;
}
```

Applied to all message types for consistency.

### Design Specifications

**Button:**
- Border: `border-border-primary` (matches ChatInput)
- Background: `bg-light-bg dark:bg-dark-bg`
- Text: 12px secondary color
- Chevron icon only (no sparkles)

**Delegation Banners:**
- Format: "{TeamName} is delegating to {MemberName}"
- Size: 12px
- Color: Secondary text
- Border: Left border (border-primary)

**Agent Messages:**
- Header: Name + timestamp (inline, baseline)
- Content: 12px secondary color
- No colored badges
- Minimal, clean design

---

## Data Structures

### Message Interface

```typescript
interface ChatMessage {
  role: 'user' | 'agent' | 'delegation';
  content: string;
  created_at: number;  // Unix seconds (NOT milliseconds!)
  
  // For agent messages
  agentName?: string;
  agentId?: string;
  teamName?: string;
  teamId?: string;
  runId?: string;
  parentRunId?: string;
  tool_calls?: ToolCall[];
  
  // For delegation messages
  isDelegation?: boolean;
  delegatedTo?: string;
  delegationTask?: string;
}
```

### AGNO Event Structure

```typescript
interface AGNOEvent {
  event: 'TeamToolCallStarted' | 'TeamToolCallCompleted' | 'TeamRunCompleted';
  created_at: number;  // Unix seconds
  run_id: string;
  parent_run_id: string;
  session_id: string;
  team_id: string;
  team_name: string;
  
  // For tool events
  tool?: {
    tool_name: string;
    tool_args: {
      member_id?: string;  // ← WHO is being called
      member_name?: string;
      task_description?: string;  // ← WHAT task
    };
    result?: string;  // ← RESPONSE from member (in Completed events)
    child_run_id?: string;  // Run ID of the delegated member
  };
}
```

### Run Hierarchy

```
Cirkelline Run (parent_run_id: "")
├── events: [
│   ├── TeamToolCallStarted (delegate to Research Team)
│   ├── TeamToolCallCompleted (Research Team finished)
│   └── TeamRunCompleted (Cirkelline finished)
│   ]
└── content: "Cirkelline's final answer"

Research Team Run (parent_run_id: "69c0486f...")
├── events: [
│   ├── TeamToolCallStarted (delegate to Web Researcher)
│   ├── TeamToolCallCompleted (Web Researcher result HERE!)
│   ├── TeamToolCallStarted (delegate to Research Analyst)
│   ├── TeamToolCallCompleted (Research Analyst result HERE!)
│   └── TeamRunCompleted (Research Team finished)
│   ]
└── content: "Research Team's synthesis"
```

---

## Common Pitfalls

### ❌ Using Milliseconds Instead of Seconds

**WRONG:**
```typescript
created_at: Date.now()  // 1730125457000 (milliseconds)
```

**CORRECT:**
```typescript
created_at: Math.floor(Date.now() / 1000)  // 1730125457 (seconds)
```

**Why:** AGNO uses Unix seconds for all timestamps. Mixing units causes messages to appear at wrong times.

---

### ❌ Wrong Path to member_id

**WRONG:**
```typescript
const memberId = event.member_id;  // undefined!
```

**CORRECT:**
```typescript
const memberId = event.tool?.tool_args?.member_id;  // "web-researcher"
```

**Why:** AGNO stores member_id inside the tool's arguments, not at the top level.

---

### ❌ Looking for member_responses Field

**WRONG:**
```typescript
const responses = run.member_responses;  // undefined!
```

**CORRECT:**
```typescript
const completedEvents = run.events.filter(e => 
  e.event === 'TeamToolCallCompleted' && e.tool?.result
);
const responses = completedEvents.map(e => e.tool.result);
```

**Why:** Member responses are stored in `TeamToolCallCompleted` events, not a separate field.

---

### ❌ Using run.created_at for Content Timestamp

**WRONG:**
```typescript
const timestamp = runTimestamp;  // When run STARTED
```

**CORRECT:**
```typescript
const completedEvent = events.find(e => e.event === 'TeamRunCompleted');
const timestamp = completedEvent?.created_at || runTimestamp;  // When run FINISHED
```

**Why:** Content is generated when the run completes, not when it starts. Using start time puts messages out of order.

---

### ❌ Not Filtering Out Internal Tools

**WRONG:**
```typescript
// Shows all tools including internal coordination tools
tool_calls: run.tools
```

**CORRECT:**
```typescript
const shouldDisplayTool = (toolName: string) => {
  const hiddenTools = ['think', 'analyze', 'delegate_task_to_member', 'reasoning_step'];
  return !hiddenTools.includes(toolName);
};

tool_calls: run.tools.filter(tool => shouldDisplayTool(tool.tool_name))
```

**Why:** Internal tools clutter the UI. Only show user-relevant tools (web search, code execution, etc.).

---

## Troubleshooting

### Messages Appear Out of Order

**Symptoms:**
- Final message appears first
- Delegation after response
- Timestamps don't match streaming

**Diagnosis:**
```typescript
// Add logging to check timestamps
allMessages.forEach(msg => {
  console.log(msg.created_at, msg.role, msg.content.substring(0, 50));
});
```

**Fixes:**
1. Ensure all timestamps are Unix seconds (not milliseconds)
2. Use event timestamps, not run timestamp
3. Sort messages before displaying: `messages.sort((a, b) => a.created_at - b.created_at)`

---

### Missing Member Responses

**Symptoms:**
- Streaming shows Web Researcher, but reload doesn't
- Only see team synthesis, not individual agent work

**Diagnosis:**
```typescript
// Check if TeamToolCallCompleted events exist
console.log('Completed events:', 
  run.events.filter(e => e.event === 'TeamToolCallCompleted')
);
```

**Fixes:**
1. Extract from `TeamToolCallCompleted` events (not `member_responses` field)
2. Check `event.tool?.result` for response content
3. Use `event.tool.tool_args.member_id` to identify which agent

---

### Wrong Delegation Names

**Symptoms:**
- Shows "Web Researcher" instead of "Research Team"
- Nested delegations appear at wrong level

**Diagnosis:**
```typescript
// Check which run the delegation belongs to
console.log('Run team:', run.team_name);
console.log('Delegation member_id:', event.tool.tool_args.member_id);
```

**Fixes:**
1. Top-level teams (Cirkelline): Infer delegation from child runs
2. Sub-teams (Research Team): Extract from events[] array
3. Map member_id to display names consistently

---

### Timestamps Show Wrong Time

**Symptoms:**
- Messages show times from year 56795
- Or messages show times from 1970

**Diagnosis:**
```typescript
// Check if using milliseconds vs seconds
console.log('Timestamp:', msg.created_at);
console.log('As date:', new Date(msg.created_at * 1000));  // Multiply by 1000 for display
```

**Fixes:**
1. Frontend always stores Unix SECONDS
2. For display, multiply by 1000: `new Date(timestamp * 1000)`
3. Never use `Date.now()` directly - always `Math.floor(Date.now() / 1000)`

---

## Testing Checklist

### ✅ Streaming Test

1. Send a message that triggers delegations (e.g., "research about...")
2. Watch messages appear in real-time
3. Verify:
   - [ ] User message shows current time
   - [ ] Delegations show current time (not hours in past/future)
   - [ ] Agent responses show current time
   - [ ] All messages in chronological order
   - [ ] Final answer appears last

### ✅ Reload Test

1. Refresh the page
2. Wait for session to load
3. Verify:
   - [ ] Same messages as during streaming
   - [ ] Same order as during streaming
   - [ ] Same timestamps as during streaming
   - [ ] All delegations visible
   - [ ] All agent responses visible
   - [ ] No duplicates
   - [ ] No missing messages

### ✅ Consistency Test

1. Take screenshot during streaming
2. Refresh page
3. Take screenshot after reload
4. Compare:
   - [ ] Message order identical
   - [ ] Timestamps identical
   - [ ] Content identical
   - [ ] Delegations identical

---

## Code References

### Key Files

- **Streaming Handler**: [`cirkelline-ui/src/hooks/useAIStreamHandler.tsx`](../cirkelline-ui/src/hooks/useAIStreamHandler.tsx)
- **Session Loader**: [`cirkelline-ui/src/hooks/useSessionLoader.tsx`](../cirkelline-ui/src/hooks/useSessionLoader.tsx)
- **Message Store**: [`cirkelline-ui/src/store.ts`](../cirkelline-ui/src/store.ts)

### Key Functions

- **Send Message**: [`handleStreamResponse()`](../cirkelline-ui/src/hooks/useAIStreamHandler.tsx:140)
- **Load Session**: [`getSession()`](../cirkelline-ui/src/hooks/useSessionLoader.tsx:72)
- **Process Event**: [`onChunk()`](../cirkelline-ui/src/hooks/useAIStreamHandler.tsx:212)

---

## Future Improvements

### Potential Enhancements

1. **Real member_responses field**: Ask AGNO to add `store_member_responses=True` to store member responses separately
2. **Optimistic updates**: Show user message immediately before backend responds
3. **Message caching**: Cache messages in IndexedDB for offline viewing
4. **Diff visualization**: Highlight changes between streaming and reload for debugging

### Known Limitations

1. Individual agent tool calls not visible after reload (only final responses)
2. Nested team hierarchies beyond 2 levels may need additional handling
3. Very long conversations (1000+ messages) may have performance issues

---

## Change Log

### 2025-10-28: Major Overhaul

- Fixed timestamp format (milliseconds → seconds)
- Fixed delegation extraction (tools[] → events[])
- Fixed member response extraction (member_responses → TeamToolCallCompleted.tool.result)
- Fixed content timestamps (run.created_at → TeamRunCompleted.created_at)
- Added comprehensive documentation

### Previous Implementations

See `progress.md` for full history of attempts and fixes.

---

**For questions or issues, refer to this document first. It contains everything we learned from 24+ hours of debugging!**