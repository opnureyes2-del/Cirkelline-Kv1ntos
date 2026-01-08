# Visual Activity Indicator System

**Version:** 1.0.0
**Last Updated:** 2025-11-03
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Purpose & User Experience](#purpose--user-experience)
3. [Architecture](#architecture)
4. [Implementation Details](#implementation-details)
5. [File Structure](#file-structure)
6. [State Management](#state-management)
7. [Event Flow](#event-flow)
8. [Visual Behavior](#visual-behavior)
9. [Code Reference](#code-reference)
10. [Troubleshooting](#troubleshooting)
11. [Future Enhancements](#future-enhancements)

---

## Overview

The **Visual Activity Indicator** is an inline, real-time status display that shows users what Cirkelline is doing during background operations (delegation, research, analysis). It appears exactly where Cirkelline's response will eventually show, providing seamless visual feedback.

### Key Characteristics

- **Inline Display**: Appears in message flow, not as a fixed overlay
- **Real-time Updates**: Shows current activity status as it changes
- **Automatic Replacement**: Disappears when final response arrives
- **Detailed Information**: Shows specific actions like "Searching for '[query]'..."
- **No "Writing response..."**: User can already see content streaming

---

## Purpose & User Experience

### Problem Solved

Previously, users had no visibility into what Cirkelline was doing during:
- Task delegation to specialist teams
- Web searches by research agents
- Analysis by specialist agents
- Coordination between multiple agents

### User Flow

```
1. User sends message: "Research quantum computing breakthroughs"

2. Cirkelline responds: "On it! Let me consult my research specialists."

3. [Behind the Scenes section appears - collapsible]

4. VISUAL INDICATOR APPEARS:
   🔵 Consulting my research specialists...

5. Indicator updates in real-time:
   🔵 Searching for 'quantum computing breakthroughs'...

6. Continues updating:
   🔵 Searching the web...

7. Next phase:
   🔵 Analyzing the research findings...

8. INDICATOR DISAPPEARS, replaced by:
   Cirkelline: "Here's what I found about quantum computing..."
```

### Design Principles

1. **Inline, Not Overlay**: Shows in natural message position
2. **Contextual**: Only shows when background work is happening
3. **Detailed**: Specific action descriptions, not generic "loading"
4. **Non-intrusive**: Smooth animations, disappears when not needed
5. **Consistent**: Uses same styling as message area

---

## Architecture

### High-Level Flow

```
Backend (AGNO) → SSE Stream → Frontend Handler → Store → UI Component
```

### Component Hierarchy

```
ChatArea
└── MessageArea
    └── Messages.tsx
        └── ConversationTurn
            ├── UserMessage
            ├── BehindTheScenes (collapsible)
            └── InlineActivityIndicator ← THE INDICATOR
                └── [Replaced by Cirkelline's final message]
```

---

## Implementation Details

### Core Components

#### 1. InlineActivityIndicator Component
**Location**: `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/components/chat/ChatArea/Messages/Messages.tsx` (lines 206-239)

```tsx
const InlineActivityIndicator: FC<{ status: string }> = ({ status }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      transition={{ duration: 0.2 }}
      className="flex items-center gap-3 mb-4"
    >
      {/* Pulsing dot indicator */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 1, 0.5]
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: "easeInOut"
        }}
        className="w-2 h-2 rounded-full bg-accent flex-shrink-0"
      />

      {/* Status text */}
      <span className="text-sm text-light-text dark:text-dark-text font-medium">
        {status}
      </span>
    </motion.div>
  )
}
```

**Features**:
- Framer Motion animations for smooth entry/exit
- Pulsing dot to show activity
- Flexible text display for any status message
- Responsive to light/dark themes

#### 2. Integration in Message Flow
**Location**: Same file, lines 335-338

```tsx
{/* Inline Activity Indicator - Shows BELOW Behind the Scenes, BEFORE final answer */}
{isLastTurn && !turn.finalAnswer && isStreaming && activityStatus && (
  <InlineActivityIndicator status={activityStatus} />
)}
```

**Rendering Conditions** (ALL must be true):
1. `isLastTurn`: Only show for the current conversation turn
2. `!turn.finalAnswer`: Only while waiting for final answer
3. `isStreaming`: Backend is actively streaming
4. `activityStatus`: Status message exists

---

## File Structure

### Modified Files

#### 1. Messages.tsx
**Path**: `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/components/chat/ChatArea/Messages/Messages.tsx`

**Changes**:
- Added imports: `useStore`, `motion` from framer-motion
- Created `InlineActivityIndicator` component
- Integrated component into message rendering flow
- Positioned AFTER "Behind the Scenes", BEFORE final answer

#### 2. useAIStreamHandler.tsx
**Path**: `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useAIStreamHandler.tsx`

**Changes**:
- Filters out "Writing response..." status (lines 473-477 removed)
- Sets status for delegation events (lines 346-356)
- Sets status for member tool calls (lines 358-368)
- Sets status for agent-specific actions (lines 381-395)

**Key Status Setting Logic**:

```tsx
// Delegation events
if (toolName && delegationTools.includes(toolName)) {
  const status = getActivityStatus(toolName, toolArgs, agnoChunk.agent_name)
  if (status) {
    setActivityStatus(status)  // "Consulting my research specialists..."
  }
}

// Member agent tools (web search)
if (memberTools.includes(toolName)) {
  const status = getActivityStatus(toolName, toolArgs, agnoChunk.agent_name)
  if (status) {
    setActivityStatus(status)  // "Searching for '[query]'..."
  }
}

// RunContent events - agent-specific statuses
if (agentName) {
  const lowerAgentName = agentName.toLowerCase().trim()
  if (lowerAgentName.includes('web') || lowerAgentName.includes('research')) {
    if (lowerAgentName.includes('analyst')) {
      setActivityStatus('Analyzing the research findings...')
    } else if (lowerAgentName.includes('web')) {
      setActivityStatus('Searching the web...')
    }
  }
}
```

#### 3. ChatArea.tsx
**Path**: `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/components/chat/ChatArea/ChatArea.tsx`

**Changes**:
- Removed `ActivityStatusBar` import (old fixed-position version)
- Removed `<ActivityStatusBar />` component from layout
- Now using inline indicator in Messages.tsx instead

### Deleted Files

#### ActivityStatusBar.tsx
**Previous Path**: `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/components/chat/ChatArea/ActivityStatusBar.tsx`

**Reason for Deletion**:
- Was a fixed-position component (bottom of screen)
- Replaced by inline component in Messages.tsx
- New approach provides better UX (shows where message will appear)

---

## State Management

### Zustand Store
**Path**: `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/store.ts`

**Relevant State**:

```tsx
interface Store {
  // Streaming state
  isStreaming: boolean
  setIsStreaming: (isStreaming: boolean) => void

  // Activity status
  activityStatus: string | null
  setActivityStatus: (status: string | null) => void
}
```

### State Flow

```
Backend Event → useAIStreamHandler → Store → Messages.tsx → InlineActivityIndicator
```

1. **Backend sends SSE event**: `TeamToolCallStarted`, `ToolCallStarted`, `RunContent`
2. **useAIStreamHandler receives**: Parses event type and data
3. **Handler sets store state**: `setActivityStatus("message")`
4. **Messages.tsx reads state**: `const { isStreaming, activityStatus } = useStore()`
5. **Conditional render**: Shows indicator if conditions met
6. **Component displays**: Pulsing dot + status text

---

## Event Flow

### Detailed Event Sequence

#### Step 1: User Sends Message
```
User: "Research quantum computing"
Frontend: POST /api/teams/cirkelline/runs
```

#### Step 2: Cirkelline Acknowledges
```
Event: TeamRunContent (from Cirkelline)
Content: "On it! Let me consult my research specialists."
UI: Shows Cirkelline message
```

#### Step 3: Delegation Starts
```
Event: TeamToolCallStarted
Tool: delegate_task_to_member
Data: { member: "Research Team", task: "Research quantum computing" }

Handler: Sets activityStatus = "Consulting my research specialists..."
UI: Inline indicator appears with pulsing dot
```

#### Step 4: Web Search Begins
```
Event: ToolCallStarted (from Web Researcher)
Tool: duckduckgo_search / exa_search / tavily_search
Data: { query: "quantum computing breakthroughs 2024" }

Handler: Sets activityStatus = "Searching for 'quantum computing breakthroughs 2024'..."
UI: Indicator updates in place
```

#### Step 5: Researcher Working
```
Event: RunContent (from Web Researcher)
Agent: Web Researcher

Handler: Detects agent name contains "web"
Sets activityStatus = "Searching the web..."
UI: Indicator updates
```

#### Step 6: Analyst Working
```
Event: RunContent (from Research Analyst)
Agent: Research Analyst

Handler: Detects agent name contains "analyst"
Sets activityStatus = "Analyzing the research findings..."
UI: Indicator updates
```

#### Step 7: Final Response Arrives
```
Event: TeamRunContent (from Cirkelline)
Content: "Here's what I found..." (streaming)

Handler: Sets activityStatus = null (filtered out "Writing response...")
UI: Indicator disappears, content streams in its place
```

---

## Visual Behavior

### Animation Details

#### Entry Animation
```tsx
initial={{ opacity: 0, y: 10 }}
animate={{ opacity: 1, y: 0 }}
transition={{ duration: 0.2 }}
```
- Fades in from 0% to 100% opacity
- Slides up 10px
- Takes 200ms

#### Pulsing Dot
```tsx
animate={{
  scale: [1, 1.2, 1],      // Size pulses 20%
  opacity: [0.5, 1, 0.5]   // Opacity pulses
}}
transition={{
  duration: 1.5,            // Full cycle: 1.5 seconds
  repeat: Infinity,         // Never stops
  ease: "easeInOut"        // Smooth acceleration/deceleration
}}
```

#### Exit Animation
```tsx
exit={{ opacity: 0, y: 10 }}
transition={{ duration: 0.2 }}
```
- Fades out to 0% opacity
- Slides down 10px
- Takes 200ms

### Positioning

```
┌─────────────────────────────────────┐
│ User Message: "Research topic"      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Cirkelline: "On it!"                │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ [Behind the Scenes] ▼               │
│ • Research Team delegated           │
│ • Web Researcher: Search completed  │
└─────────────────────────────────────┘

🔵 Analyzing the research findings...  ← INDICATOR HERE
    ↓
    (Gets replaced by final answer)
    ↓
┌─────────────────────────────────────┐
│ Cirkelline: "Here's what I found..." │
└─────────────────────────────────────┘
```

---

## Code Reference

### Complete Integration Example

**Messages.tsx (simplified structure)**:

```tsx
import { useStore } from '@/store'
import { motion } from 'framer-motion'

const InlineActivityIndicator: FC<{ status: string }> = ({ status }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      transition={{ duration: 0.2 }}
      className="flex items-center gap-3 mb-4"
    >
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 1, 0.5]
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: "easeInOut"
        }}
        className="w-2 h-2 rounded-full bg-accent flex-shrink-0"
      />
      <span className="text-sm text-light-text dark:text-dark-text font-medium">
        {status}
      </span>
    </motion.div>
  )
}

const Messages = ({ messages }: MessageListProps) => {
  const { isStreaming, activityStatus } = useStore()

  return (
    <>
      {conversationTurns.map((turn, turnIndex) => {
        const isLastTurn = turnIndex === conversationTurns.length - 1

        return (
          <div key={turnKey} className="space-y-4">
            {/* User Message */}
            <UserMessage message={turn.userMessage} />

            {/* Behind the Scenes */}
            {!turn.finalAnswer && (
              <BehindTheScenes
                messages={turn.intermediateWork}
                turnIndex={turnIndex}
              />
            )}

            {/* Inline Activity Indicator */}
            {isLastTurn && !turn.finalAnswer && isStreaming && activityStatus && (
              <InlineActivityIndicator status={activityStatus} />
            )}

            {/* Final Answer (replaces indicator) */}
            {turn.finalAnswer && (
              <AgentMessageWrapper message={turn.finalAnswer} />
            )}
          </div>
        )
      })}
    </>
  )
}
```

### Activity Status Messages

All possible status messages set by `useAIStreamHandler.tsx`:

```tsx
// Delegation
"Consulting my research specialists..."
"Consulting my legal specialists..."
"Delegating task to specialist..."

// Web Search (with query)
"Searching for '[actual search query]'..."

// Agent Activity
"Searching the web..."              // Web Researcher
"Analyzing the research findings..." // Research Analyst
"Analyzing the information..."       // Coordination tools (think, analyze)
"Processing your request..."         // Fallback for other tools

// Document Processing
"Reading the document..."           // Document Specialist
"Analyzing the content..."          // Document Specialist

// Audio/Video
"Processing the audio..."           // Audio Specialist
"Analyzing the video..."            // Video Specialist
```

### Status Determination Logic

**getActivityStatus function** (in useAIStreamHandler.tsx):

```tsx
const getActivityStatus = (
  toolName: string,
  toolArgs: any,
  agentName?: string
): string | null => {
  // Delegation tools
  if (toolName === 'delegate_task_to_member') {
    const member = toolArgs?.member || 'specialist'
    if (member.toLowerCase().includes('research')) {
      return 'Consulting my research specialists...'
    }
    if (member.toLowerCase().includes('law')) {
      return 'Consulting my legal specialists...'
    }
    return 'Delegating task to specialist...'
  }

  // Search tools - show actual query
  if (toolName === 'duckduckgo_search' ||
      toolName === 'exa_search' ||
      toolName === 'tavily_search') {
    const query = toolArgs?.query || toolArgs?.q || ''
    if (query) {
      return `Searching for '${query}'...`
    }
    return 'Searching the web...'
  }

  // Coordination tools
  if (toolName === 'think' || toolName === 'analyze') {
    return 'Analyzing the information...'
  }

  // Fallback
  return 'Processing your request...'
}
```

---

## Troubleshooting

### Issue 1: Indicator Not Appearing

**Symptoms**: No indicator shows during delegation/research

**Debug Steps**:

1. Check browser console for state logs:
```javascript
console.log('isStreaming:', isStreaming)
console.log('activityStatus:', activityStatus)
console.log('isLastTurn:', isLastTurn)
console.log('turn.finalAnswer:', turn.finalAnswer)
```

2. Verify all conditions are true:
- `isLastTurn` = true
- `turn.finalAnswer` = null/undefined
- `isStreaming` = true
- `activityStatus` = string value

3. Check useAIStreamHandler is setting status:
```tsx
// Add temporary logging in useAIStreamHandler.tsx
console.log('🔥 SETTING ACTIVITY STATUS:', status)
setActivityStatus(status)
```

**Common Causes**:
- Simple questions don't trigger delegation (Cirkelline answers directly)
- Status is "Writing response..." (filtered out intentionally)
- Final answer already received (`turn.finalAnswer` exists)

### Issue 2: Indicator Stuck/Not Updating

**Symptoms**: Shows old status, doesn't update

**Debug Steps**:

1. Check if status is actually changing:
```tsx
useEffect(() => {
  console.log('Activity status changed:', activityStatus)
}, [activityStatus])
```

2. Verify streaming events are arriving:
- Open Network tab in DevTools
- Look for EventStream connection
- Check events are being sent

**Common Causes**:
- WebSocket/SSE connection dropped
- Backend not sending status updates
- React not re-rendering (state not updating)

### Issue 3: Indicator in Wrong Position

**Symptoms**: Shows at top of messages or wrong location

**Debug Steps**:

1. Check render order in Messages.tsx:
```tsx
// Should be:
<UserMessage />
<BehindTheScenes />
<InlineActivityIndicator />  ← After BehindTheScenes
<FinalAnswer />
```

2. Verify it's inside the correct turn:
```tsx
// Should be in isLastTurn check
{isLastTurn && ...}
```

**Fix**: Ensure indicator is positioned AFTER `<BehindTheScenes />` and BEFORE final answer check.

### Issue 4: Animation Not Smooth

**Symptoms**: Janky animations, stuttering

**Debug Steps**:

1. Check if Framer Motion is installed:
```bash
cd /home/eenvy/Desktop/cirkelline/cirkelline-ui
npm ls framer-motion
```

2. Verify AnimatePresence wrapping (if used):
```tsx
<AnimatePresence mode="wait">
  {condition && <InlineActivityIndicator />}
</AnimatePresence>
```

**Common Causes**:
- CSS conflicts with motion
- Too many animations running simultaneously
- Browser performance issues

---

## Future Enhancements

### Potential Improvements

#### 1. Progress Indicators
Add progress bars for long-running operations:
```tsx
<InlineActivityIndicator
  status={status}
  progress={75}  // 0-100
/>
```

#### 2. Action Icons
Show icons based on activity type:
```tsx
const getIcon = (status: string) => {
  if (status.includes('search')) return <SearchIcon />
  if (status.includes('analyz')) return <AnalyzeIcon />
  return <ProcessingIcon />
}
```

#### 3. Estimated Time
Display estimated completion time:
```tsx
<span className="text-xs text-secondary">
  ~{estimatedSeconds}s remaining
</span>
```

#### 4. Multiple Parallel Activities
Show multiple indicators if agents work in parallel:
```tsx
<div className="space-y-2">
  {activeStatuses.map(status => (
    <InlineActivityIndicator key={status} status={status} />
  ))}
</div>
```

#### 5. Audio Feedback
Optional sound when status changes:
```tsx
useEffect(() => {
  if (activityStatus && soundEnabled) {
    playStatusChangeSound()
  }
}, [activityStatus])
```

### Integration with Other Features

#### Notion Panel Integration
Show activity status in Notion panel when processing documents:
```tsx
{isProcessingNotionDoc && (
  <InlineActivityIndicator status="Analyzing Notion document..." />
)}
```

#### Upload Progress
Reuse component for file uploads:
```tsx
<InlineActivityIndicator
  status={`Uploading ${fileName}... ${uploadProgress}%`}
/>
```

---

## Testing Checklist

### Manual Testing

✅ **Basic Functionality**
- [ ] Indicator appears during delegation
- [ ] Shows correct status messages
- [ ] Updates in real-time
- [ ] Disappears when response arrives
- [ ] Pulsing animation works
- [ ] Smooth entry/exit animations

✅ **Positioning**
- [ ] Shows BELOW "Behind the Scenes"
- [ ] Shows ABOVE final answer
- [ ] Only shows on last turn
- [ ] Doesn't show on old turns

✅ **Status Messages**
- [ ] "Consulting my research specialists..." (delegation)
- [ ] "Searching for '[query]'..." (web search with actual query)
- [ ] "Searching the web..." (researcher working)
- [ ] "Analyzing the research findings..." (analyst working)
- [ ] Does NOT show "Writing response..."

✅ **Edge Cases**
- [ ] Simple questions (no delegation) - no indicator
- [ ] Multiple turns - only shows on latest
- [ ] Fast responses - indicator doesn't flicker
- [ ] Long operations - indicator stays visible
- [ ] Network issues - graceful degradation

✅ **Visual Polish**
- [ ] Light mode styling correct
- [ ] Dark mode styling correct
- [ ] Mobile responsive
- [ ] Accessible (screen readers)
- [ ] No layout shift when appearing/disappearing

### Test Queries

**Good test questions** (trigger delegation):
```
"Research the latest AI developments in 2024"
"What are recent breakthroughs in quantum computing?"
"Find information about new climate change policies"
"Search for updates on fusion energy progress"
```

**Bad test questions** (won't trigger delegation):
```
"What is 2+2?"
"What is the capital of France?"
"Hello"
"Tell me a joke"
```

---

## Performance Considerations

### Optimization Notes

1. **Component Memoization**: Not needed - renders only once per status change
2. **Animation Performance**: Uses CSS transforms (GPU accelerated)
3. **Re-render Impact**: Minimal - only re-renders when `activityStatus` changes
4. **Bundle Size**: +2KB (Framer Motion already included)

### Monitoring

Add performance tracking:
```tsx
useEffect(() => {
  const start = performance.now()
  return () => {
    const duration = performance.now() - start
    console.log('Indicator visible for:', duration, 'ms')
  }
}, [activityStatus])
```

---

## Summary

### What We Built

✅ **Inline activity indicator** that shows exactly where Cirkelline's response will appear
✅ **Real-time status updates** with detailed, contextual information
✅ **Smooth animations** using Framer Motion
✅ **Automatic lifecycle management** (appears/disappears correctly)
✅ **Clean integration** with existing message flow

### Key Files Modified

1. `Messages.tsx` - Added InlineActivityIndicator component + integration
2. `useAIStreamHandler.tsx` - Status detection and setting logic
3. `ChatArea.tsx` - Removed old fixed-position component
4. `store.ts` - Already had necessary state (no changes needed)

### Result

Users now have **clear, real-time visibility** into Cirkelline's background operations, showing:
- What specialist is working
- What searches are being performed
- What analysis is happening
- When response is coming

All displayed **inline in the natural message flow**, creating a seamless, professional UX.

---

**Document Status**: ✅ Complete
**Implementation Status**: ✅ Production Ready
**Last Verified**: 2025-11-03

**Questions or Issues?** Check:
- `/docs/15-STREAMING-EVENT-FILTERING.md` - Understanding AGNO events
- `/docs/06-FRONTEND-REFERENCE.md` - Frontend architecture
- Browser DevTools Console - Real-time debugging

---

*This documentation reflects the final, working implementation as of November 3, 2025.*
