# Behind the Scenes Feature - Design Document

**Date:** 2025-10-28 (Updated: 2025-11-26)
**Status:** ✅ IMPLEMENTED

---

## Objective

Hide intermediate work (delegations and agent responses) in a collapsible section, showing only:
- User's question
- Cirkelline's final answer

This keeps the UI clean while allowing curious users to explore the reasoning process.

---

## User Experience

### Default View (Collapsed)

```
┌─────────────────────────────────────┐
│ 👤 User                             │
│ research about latest AI news       │
│                             4:11 PM │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🔍 Show Behind the Scenes (4 steps) │  ← Clickable button
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🤖 Cirkelline                       │
│ Here's what I found about AI...     │
│                             4:12 PM │
└─────────────────────────────────────┘
```

### Expanded View

```
┌─────────────────────────────────────┐
│ 👤 User                             │
│ research about latest AI news       │
│                             4:11 PM │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🔍 Hide Behind the Scenes           │  ← Clickable button
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ → Delegation to Research Team   │ │
│ │                         4:11 PM │ │
│ └─────────────────────────────────┘ │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ → Delegation to Web Researcher  │ │
│ │                         4:11 PM │ │
│ └─────────────────────────────────┘ │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ 📰 Web Researcher               │ │
│ │ Here's what I found...          │ │
│ │                         4:11 PM │ │
│ └─────────────────────────────────┘ │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ → Delegation to Research Analyst│ │
│ │                         4:11 PM │ │
│ └─────────────────────────────────┘ │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ 📊 Research Analyst             │ │
│ │ After analyzing...              │ │
│ │                         4:12 PM │ │
│ └─────────────────────────────────┘ │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ 🔬 Research Team                │ │
│ │ Based on our research...        │ │
│ │                         4:12 PM │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🤖 Cirkelline                       │
│ Here's what I found about AI...     │
│                             4:12 PM │
└─────────────────────────────────────┘
```

---

## Implementation Strategy

### 1. Message Grouping Logic

Messages need to be grouped into "conversation turns":

```typescript
interface ConversationTurn {
  userMessage: ChatMessage;
  intermediateWork: ChatMessage[];  // Delegations + agent responses
  finalAnswer: ChatMessage;  // Cirkelline's response
}
```

**Grouping Algorithm:**
```typescript
function groupMessagesIntoTurns(messages: ChatMessage[]): ConversationTurn[] {
  const turns: ConversationTurn[] = [];
  let currentTurn: Partial<ConversationTurn> = {};
  
  for (const message of messages) {
    if (message.role === 'user') {
      // Start new turn
      if (currentTurn.finalAnswer) {
        turns.push(currentTurn as ConversationTurn);
        currentTurn = {};
      }
      currentTurn.userMessage = message;
      currentTurn.intermediateWork = [];
    }
    else if (message.role === 'delegation' || 
             (message.role === 'agent' && message.teamName !== 'Cirkelline')) {
      // Add to intermediate work
      currentTurn.intermediateWork?.push(message);
    }
    else if (message.role === 'agent' && message.teamName === 'Cirkelline') {
      // Final answer
      currentTurn.finalAnswer = message;
      turns.push(currentTurn as ConversationTurn);
      currentTurn = {};
    }
  }
  
  return turns;
}
```

### 2. Component Structure

```
Messages.tsx
  ├─ ConversationTurn (for each turn)
  │  ├─ UserMessage
  │  ├─ BehindTheScenes (collapsible)
  │  │  ├─ DelegationMessage
  │  │  ├─ AgentMessage (Web Researcher)
  │  │  ├─ DelegationMessage
  │  │  ├─ AgentMessage (Research Analyst)
  │  │  └─ AgentMessage (Research Team)
  │  └─ AgentMessage (Cirkelline final)
```

### 3. New Component: BehindTheScenes.tsx

```typescript
interface BehindTheScenesProps {
  messages: ChatMessage[];
  defaultExpanded?: boolean;
}

const BehindTheScenes: FC<BehindTheScenesProps> = ({ 
  messages, 
  defaultExpanded = false 
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  
  const stepCount = messages.length;
  
  return (
    <div className="my-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-3 rounded-lg border border-dashed border-light-border dark:border-dark-border hover:bg-light-surface dark:hover:bg-dark-surface transition-colors flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <Icon type={isExpanded ? "chevron-down" : "chevron-right"} size="sm" />
          <span className="text-sm font-medium text-light-text dark:text-dark-text">
            {isExpanded ? "Hide" : "Show"} Behind the Scenes
          </span>
          <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
            ({stepCount} {stepCount === 1 ? "step" : "steps"})
          </span>
        </div>
        <Icon type="sparkles" size="sm" className="text-accent" />
      </button>
      
      {isExpanded && (
        <div className="mt-3 pl-4 border-l-2 border-light-border dark:border-dark-border space-y-3">
          {messages.map((message, index) => {
            const key = `behind-${message.role}-${message.created_at}-${index}`;
            
            if (message.role === 'delegation') {
              return <DelegationMessage key={key} message={message} />;
            }
            
            if (message.role === 'agent') {
              return <AgentMessageWrapper key={key} message={message} isLastAgentMessage={false} isLastMessage={false} />;
            }
            
            return null;
          })}
        </div>
      )}
    </div>
  );
};
```

---

## Visual Design

### Collapsed State

- **Dashed border** to indicate it's special/expandable
- **Subtle hover effect** for interactivity
- **Step count** to show there's work hidden
- **Icon** (sparkles/magic wand) to indicate "AI magic happened here"

### Expanded State

- **Left border** to visually group the intermediate steps
- **Indentation** to show these are "inside" the main flow
- **Same styling** for delegation/agent messages as before
- **Smooth animation** when expanding/collapsing

### Color Scheme

```css
/* Collapsed button */
border: 1px dashed theme('colors.light.border');
background: transparent;
hover:background: theme('colors.light.surface');

/* Expanded container */
border-left: 2px solid theme('colors.light.border');
padding-left: 1rem;
```

---

## State Management

### Per-Turn State

Each conversation turn manages its own collapsed/expanded state:

```typescript
const [expandedTurns, setExpandedTurns] = useState<Set<number>>(new Set());

const toggleTurn = (turnIndex: number) => {
  setExpandedTurns(prev => {
    const next = new Set(prev);
    if (next.has(turnIndex)) {
      next.delete(turnIndex);
    } else {
      next.add(turnIndex);
    }
    return next;
  });
};
```

### Global Controls (Future)

Could add buttons to:
- "Expand All Behind the Scenes"
- "Collapse All Behind the Scenes"
- "Always Show Behind the Scenes" (user preference)

---

## Edge Cases

### 1. Single-Message Responses

If Cirkelline responds directly without delegating:
```
User message
→ Cirkelline answer (no intermediate work)
```

**Solution:** Don't show "Behind the Scenes" if there are no intermediate messages.

### 2. Streaming in Progress

While message is streaming, show all steps by default:
```
User message
→ Delegation (visible)
→ Web Researcher (visible, streaming...)
```

**Solution:** Only collapse after Cirkelline's final message arrives.

### 3. Multiple User Messages

If user sends another message before previous completes:
```
User message 1
→ (processing...)
User message 2
→ (processing...)
```

**Solution:** Group each user message with its corresponding Cirkelline answer.

---

## Accessibility

### Keyboard Navigation

- Tab to button
- Enter/Space to toggle
- Escape to collapse (if expanded)

### Screen Readers

```html
<button 
  aria-expanded={isExpanded}
  aria-controls="behind-scenes-content"
  aria-label={`${isExpanded ? "Hide" : "Show"} behind the scenes work (${stepCount} steps)`}
>
  ...
</button>

<div 
  id="behind-scenes-content" 
  role="region" 
  aria-labelledby="behind-scenes-button"
>
  ...
</div>
```

---

## Performance

### Considerations

- Large conversations may have many turns
- Each turn has intermediate messages
- Rendering all expanded could be slow

### Optimizations

1. **Lazy render**: Only render expanded content when opened
2. **Virtual scrolling**: For very long conversations
3. **Memoization**: Memo the BehindTheScenes component

```typescript
const BehindTheScenes = memo(({ messages, defaultExpanded }: BehindTheScenesProps) => {
  // Only render content if expanded
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  
  return (
    <>
      <ToggleButton ... />
      {isExpanded && <Content messages={messages} />}
    </>
  );
});
```

---

## Testing

### Test Cases

1. ✅ **Simple delegation**: User → Research Team → Cirkelline
2. ✅ **Nested delegation**: User → Research Team → Web Researcher + Research Analyst → Cirkelline
3. ✅ **Direct response**: User → Cirkelline (no intermediate work)
4. ✅ **Multiple turns**: Several user messages in one session
5. ✅ **Streaming**: Messages appearing in real-time
6. ✅ **Reload**: Collapsed state after page refresh

### Manual Testing

```
Test 1: Basic Functionality
- Send "research about AI news"
- Verify collapsed state shows
- Click to expand
- Verify all delegations and responses visible
- Click to collapse
- Verify only user + Cirkelline visible

Test 2: Multiple Turns
- Send 3 different research questions
- Verify each has its own "Behind the Scenes"
- Expand one, verify others stay collapsed
- Refresh page
- Verify all start collapsed
```

---

## Reasoning Content Display (v1.2.16)

### Overview

**Status:** ✅ **IMPLEMENTED**

Reasoning steps from agents using ReasoningTools are displayed within the Behind the Scenes panel, showing the agent's step-by-step thinking process.

### Event Types Displayed

**ReasoningStep / TeamReasoningStep:**
```typescript
{
  event: "ReasoningStep",
  agent_name: "Cirkelline",
  content: {
    title: "Planning response",
    reasoning: "To solve this problem, I need to...",
    action: "I will analyze...",
    confidence: 0.9
  },
  reasoning_content: "## Planning response\n\nTo solve this problem..." // Formatted markdown
}
```

### Visual Design

**Reasoning Display:**
```
┌─────────────────────────────────────┐
│ ▼ Hide Behind the Scenes            │
│ ┌─────────────────────────────────┐ │
│ │ Cirkelline: Planning response   │ │ ← Event title
│ │                                 │ │
│ │ To solve this problem, I need   │ │ ← reasoning_content
│ │ to consider multiple factors... │ │   (formatted text)
│ │                                 │ │
│ │ Step 1: Analyze requirements    │ │
│ │ Step 2: Consider constraints    │ │
│ │ Step 3: Optimize solution       │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Cirkelline: Planning complete   │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Implementation

**Component:** `BehindTheScenes.tsx` (lines 86-90)

```typescript
{event.details?.reasoningContent && (
  <div className="text-xs text-light-text dark:text-dark-text italic pl-4 py-2 border-l-2 border-border-primary">
    {event.details.reasoningContent}
  </div>
)}
```

**Event Parsing:** `useAIStreamHandler.tsx` (lines 277-291)

```typescript
case RunEvent.ReasoningStep:
case RunEvent.TeamReasoningStep:
  const reasoningStep = chunk.content as any
  if (reasoningStep && reasoningStep.title) {
    description = `${source}: ${reasoningStep.title}`
    details.reasoningContent = (chunk as any).reasoning_content || reasoningStep.reasoning
    details.action = reasoningStep.action
    details.confidence = reasoningStep.confidence
  }
  status = 'in_progress'
  break
```

### Styling

**Text Formatting:**
- `text-xs` - Small text to fit within collapsed space
- `italic` - Distinguishes reasoning from regular content
- `pl-4 py-2` - Padding for readability
- `border-l-2 border-border-primary` - Left border to indicate quoted/nested content

**Color Scheme:**
```css
/* Reasoning content */
color: theme('colors.light.text'); /* Main text */
color: theme('colors.dark.text');  /* Dark mode */
border-left: 2px solid theme('colors.border.primary');
```

### When Reasoning Appears

**Agents decide autonomously:**
- ✅ Complex queries → Reasoning shown
- ✅ Logic puzzles → Reasoning shown
- ✅ Optimization problems → Reasoning shown
- ❌ Simple queries → No reasoning (direct answer)

**Force reasoning:**
```
"Think step-by-step: [your question]"
```

### Example Workflows

**Workflow 1: Optimization Problem**
```
User: "I have 100 meters of fence. What dimensions maximize area?"
    ↓
Behind the Scenes:
  → Cirkelline: Planning response
     "This is an optimization problem. Given perimeter = 100m,
      I need to find dimensions that maximize area. For a
      rectangle with fixed perimeter, a square maximizes area.
      Therefore: 25m × 25m = 625m²"
  → Cirkelline: Planning complete
    ↓
Cirkelline answer: "Use a square: 25m × 25m (625m²)"
```

**Workflow 2: Multi-Step Calculation**
```
User: "Think step-by-step: What is 15% of $250?"
    ↓
Behind the Scenes:
  → Cirkelline: Planning response
     "To calculate 15% of $250:
      Step 1: Convert 15% to decimal: 0.15
      Step 2: Multiply: $250 × 0.15 = $37.50
      Therefore, 15% of $250 is $37.50"
  → Cirkelline: Planning complete
    ↓
Cirkelline answer: "15% of $250 is $37.50"
```

### Data Flow

```
1. Agent calls think() tool
   ↓
2. AGNO emits ReasoningStep event
   ↓
3. Backend logs: "🧠 REASONING EVENT DETECTED"
   ↓
4. SSE stream sends to frontend
   ↓
5. useAIStreamHandler parses event
   ↓
6. Creates BehindTheScenesEvent with reasoning_content
   ↓
7. BehindTheScenes component displays reasoning
   ↓
8. User sees thinking process
```

### Backend Logging

**Location:** `my_os.py` (lines 2604-2619)

```python
if event_type in ['ReasoningStep', 'TeamReasoningStep', 'ReasoningStarted', 'ReasoningCompleted']:
    logger.info(f"🧠 REASONING EVENT DETECTED: {event_type}")
    logger.info(f"   Agent/Team: {agent_name or team_name}")
    logger.info(f"   Title: {event_data['content'].get('title')}")
    logger.info(f"   Reasoning: {event_data['content'].get('reasoning', '')[:200]}...")
```

**Log Output Example:**
```
INFO: 🧠 REASONING EVENT DETECTED: ReasoningStep
INFO:    Agent/Team: Cirkelline
INFO:    Title: Planning response
INFO:    Reasoning: To solve this problem, I need to consider...
```

### Configuration

**Enable reasoning in agents:** See [07-DEVELOPMENT-GUIDE.md](./07-DEVELOPMENT-GUIDE.md#step-6-adding-reasoningtools-optional)

**Required:**
1. `tools=[ReasoningTools(add_instructions=True)]`
2. `tool_choice="auto"`
3. Instructions for when to use think()

### Testing

**Test query:**
```
"Think step-by-step: What is 15% of $250?"
```

**Verification:**
1. Expand Behind the Scenes
2. Look for "Cirkelline: Planning response"
3. Verify reasoning steps are visible
4. Check backend logs for `🧠 REASONING EVENT DETECTED`

### Accessibility

**Screen reader support:**
```html
<div
  className="text-xs text-light-text dark:text-dark-text italic pl-4 py-2 border-l-2 border-border-primary"
  role="region"
  aria-label="Agent reasoning process"
>
  {event.details.reasoningContent}
</div>
```

**Keyboard navigation:**
- Tab to Behind the Scenes button
- Enter to expand
- Reasoning content is readable by screen readers

---

## Token Usage & Cost Metrics (v1.2.31)

### Overview

**Status:** ✅ **IMPLEMENTED**

Comprehensive token usage and cost metrics are displayed in the Behind the Scenes panel, showing token counts, costs, and running totals for every message with Cirkelline. When delegating to specialist teams, individual team costs are tracked separately.

### Event Types Displayed

**MetricsUpdate:**
```typescript
{
  event: "MetricsUpdate",
  metrics: {
    input_tokens: 1234,
    output_tokens: 567,
    total_tokens: 1801,
    input_cost: 0.00009255,
    output_cost: 0.0001701,
    total_cost: 0.00026265,
    model: "gemini-2.5-flash"
  },
  agent_name: "Cirkelline",
  team_name: "Research Team",
  created_at: 1700000000000
}
```

### Pricing Model

**Gemini 2.5 Flash Tier 1:**
- **Input tokens:** $0.075 per 1M tokens
- **Output tokens:** $0.30 per 1M tokens
- **Calculation example:**
  ```typescript
  // 1,234 input tokens, 567 output tokens
  input_cost = (1234 / 1_000_000) * 0.075 = $0.00009255
  output_cost = (567 / 1_000_000) * 0.30 = $0.0001701
  total_cost = $0.00026265
  ```

### Visual Design

**Collapsible Metrics Box:**
```
┌─────────────────────────────────────┐
│ ▼ Hide Behind the Scenes            │
│ ┌─────────────────────────────────┐ │
│ │ → Cirkelline: Planning          │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ → Research Team: Web search     │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ ► View Metrics  1,801 tokens · $0.0003 │ │ ← Collapsed state
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ▼ Hide Behind the Scenes            │
│ ┌─────────────────────────────────┐ │
│ │ ▼ Hide Metrics  1,801 tokens · $0.0003 │ │ ← Expanded state
│ │                                 │ │
│ │ ─ Cirkelline ─────────────────  │ │
│ │ Input Tokens:        1,234      │ │
│ │ Output Tokens:         567      │ │
│ │ Total Tokens:        1,801      │ │
│ │ Input Cost:     $0.00009255     │ │
│ │ Output Cost:    $0.0001701      │ │
│ │ Total Cost:     $0.00026265     │ │
│ │                                 │ │
│ │ ══ Conversation Summary ═══════  │ │
│ │ Total Input Tokens:    1,234    │ │
│ │ Total Output Tokens:     567    │ │
│ │ Total Tokens:          1,801    │ │
│ │ Total Cost:       $0.00026265   │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Implementation

**Component:** `BehindTheScenes.tsx` (lines 240-397)

```typescript
// Single collapsible metrics box
const [isMetricsExpanded, setIsMetricsExpanded] = useState(false)

// Calculate running totals
let totalTokens = 0
let totalInputTokens = 0
let totalOutputTokens = 0
let totalInputCost = 0
let totalOutputCost = 0
let totalCost = 0
const eventsWithMetrics: BehindTheScenesEvent[] = []

events.forEach(event => {
  if (event.details?.tokenUsage) {
    totalInputTokens += event.details.tokenUsage.input
    totalOutputTokens += event.details.tokenUsage.output
    totalTokens += event.details.tokenUsage.total
    eventsWithMetrics.push(event)
  }
  if (event.details?.costs) {
    totalInputCost += event.details.costs.input
    totalOutputCost += event.details.costs.output
    totalCost += event.details.costs.total
  }
})

// Display collapsible box
<button
  onClick={() => setIsMetricsExpanded(!isMetricsExpanded)}
  className="w-full p-3 rounded-lg bg-light-bg dark:bg-dark-bg hover:bg-light-surface dark:hover:bg-dark-surface transition-colors flex items-center justify-between group"
>
  <div className="flex items-center gap-3">
    <ChevronRight className={`w-4 h-4 transition-transform ${isMetricsExpanded ? 'rotate-90' : ''}`} />
    <span className="text-sm font-bold text-white">
      {isMetricsExpanded ? 'Hide' : 'View'} Metrics
    </span>
  </div>
  <span className="text-xs text-light-text-secondary">
    {totalTokens.toLocaleString()} tokens · ${totalCost.toFixed(4)}
  </span>
</button>
```

**Backend Extraction:** `custom_cirkelline.py` (lines 586-635)

```python
# Extract metrics FROM completion events DURING streaming
if event_type in ['TeamRunCompleted', 'RunCompleted', 'run_completed', 'team_run_completed']:
    if 'metrics' in event_data and event_data['metrics']:
        metrics_data = event_data['metrics']

        # Extract token counts
        input_tokens = metrics_data.get('input_tokens', 0) or 0
        output_tokens = metrics_data.get('output_tokens', 0) or 0
        total_tokens = metrics_data.get('total_tokens', 0) or (input_tokens + output_tokens)
        model = metrics_data.get('model', 'gemini-2.5-flash') or 'gemini-2.5-flash'

        # Calculate costs using Gemini 2.5 Flash Tier 1 pricing
        costs = calculate_token_costs(input_tokens, output_tokens)

        # Create MetricsUpdate event
        metrics_event = {
            'event': 'MetricsUpdate',
            'metrics': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'input_cost': costs['input_cost'],
                'output_cost': costs['output_cost'],
                'total_cost': costs['total_cost'],
                'model': model
            },
            'agent_name': event_data.get('agent_name', team_name or agent_name or 'Cirkelline'),
            'created_at': int(time.time() * 1000)
        }

        # Yield metrics event to frontend
        serialized_metrics = serialize_event_data(metrics_event)
        yield f"event: MetricsUpdate\ndata: {json.dumps(serialized_metrics)}\n\n"
```

**Event Parsing:** `useAIStreamHandler.tsx` (lines 359-382)

```typescript
case RunEvent.MetricsUpdate: // Token usage and cost metrics
  const metricsData = chunk.metrics
  if (metricsData) {
    const formattedCost = metricsData.total_cost < 0.01
      ? `${metricsData.total_cost.toFixed(6)}`
      : `${metricsData.total_cost.toFixed(4)}`
    description = `${source}: ${metricsData.total_tokens.toLocaleString()} tokens used (${formattedCost})`
    status = 'completed'
    details.metrics = metricsData
    details.tokenUsage = {
      input: metricsData.input_tokens,
      output: metricsData.output_tokens,
      total: metricsData.total_tokens
    }
    details.costs = {
      input: metricsData.input_cost,
      output: metricsData.output_cost,
      total: metricsData.total_cost
    }
  }
  break
```

### Styling

**Collapsible Button:**
- `bg-light-bg dark:bg-dark-bg` - Matches main Behind the Scenes button
- `hover:bg-light-surface dark:hover:bg-dark-surface` - Subtle hover effect
- `border-border-primary` - Consistent with existing borders
- No accent colors - maintains visual hierarchy

**Expanded Content:**
- `border-l-2 border-border-primary` - Left border to indicate nested content
- `pl-4` - Padding to separate from border
- `font-bold text-white` - Bold white titles for section headers
- No background color - clean, minimal design

**Typography:**
```css
/* Section headers */
font-weight: bold;
color: white;

/* Metric labels */
font-size: 0.75rem; /* text-xs */
color: theme('colors.light.text.secondary');

/* Metric values */
font-size: 0.875rem; /* text-sm */
color: theme('colors.light.text');
font-family: monospace;
```

### Data Flow

```
1. Agent/Team completes run
   ↓
2. AGNO emits RunCompletedEvent with metrics attribute
   ↓
3. Backend extracts metrics from event_data['metrics']
   ↓
4. Backend calculates costs using Tier 1 pricing
   ↓
5. Backend creates MetricsUpdate event
   ↓
6. SSE stream sends to frontend
   ↓
7. useAIStreamHandler parses event
   ↓
8. Creates BehindTheScenesEvent with metrics/tokenUsage/costs
   ↓
9. Events filtered from main timeline (no duplicates)
   ↓
10. BehindTheScenes component aggregates all metrics
   ↓
11. Single collapsible box displays individual + total metrics
```

### Critical Implementation Details

**❌ Wrong Approach (Doesn't Work):**
```python
# Trying to access metrics AFTER streaming completes
if hasattr(cirkelline, 'last_run') and cirkelline.last_run:
    metrics = cirkelline.last_run.metrics  # ⚠️ This is None during streaming!
```

**✅ Correct Approach (Works):**
```python
# Extract metrics FROM completion events DURING streaming
for chunk in cirkelline.run(...):
    if event_type in ['RunCompleted', 'TeamRunCompleted']:
        if 'metrics' in event_data and event_data['metrics']:
            metrics_data = event_data['metrics']  # ✅ Extract from event itself
```

**Reason:** AGNO doesn't populate `last_run.metrics` until the generator function returns control, which happens AFTER all SSE events are yielded. Metrics must be extracted from the completion events themselves during streaming.

### Multi-Agent Tracking

**Delegation Flow:**
```
User: "Research the latest AI news"
    ↓
Behind the Scenes Metrics:
  ─ Cirkelline ─────────────────
  Input Tokens:         234
  Output Tokens:         89
  Total Tokens:        323
  Total Cost:      $0.0000444

  ─ Research Team ──────────────
  Input Tokens:       1,567
  Output Tokens:        892
  Total Tokens:      2,459
  Total Cost:      $0.0003851

  ══ Conversation Summary ═══════
  Total Input Tokens:  1,801
  Total Output Tokens:   981
  Total Tokens:        2,782
  Total Cost:      $0.0004295
```

**Each agent/team gets separate metrics:**
- Cirkelline's delegation decision: ~300-500 tokens
- Research Team's work: ~2,000-3,000 tokens
- Individual specialists tracked separately

### Testing

**Test Query:**
```
"Research the latest AI news"
```

**Verification:**
1. Send message to Cirkelline
2. Expand Behind the Scenes
3. Scroll to bottom
4. Click "View Metrics"
5. Verify individual agent metrics show
6. Verify Conversation Summary shows totals
7. Check backend logs for `📊 METRICS FOUND IN COMPLETION EVENT`

**Backend Log Output:**
```
INFO: 🔍 COMPLETION EVENT DETECTED: RunCompleted
INFO: 📊 METRICS FOUND IN COMPLETION EVENT
INFO: 📊 Sent MetricsUpdate: 1801 tokens
```

### Edge Cases

**1. No Metrics Available**
- If no completion events contain metrics, box doesn't appear
- `if (totalTokens > 0)` prevents empty box

**2. Multiple Teams**
- Each team's metrics tracked separately
- Running total sums all teams
- Individual breakdowns show which team used what

**3. Cost Formatting**
- Costs < $0.01: Show 6 decimal places
- Costs >= $0.01: Show 4 decimal places
- Consistent thousand separators for token counts

**4. Streaming in Progress**
- Metrics appear only after completion events
- Box updates reactively as new metrics arrive
- No partial/incomplete metrics shown

### Configuration

**Backend Pricing Constants:** `custom_cirkelline.py`

```python
def calculate_token_costs(input_tokens: int, output_tokens: int) -> dict:
    """
    Calculate costs based on Gemini 2.5 Flash Tier 1 pricing.
    Input: $0.075 per 1M tokens
    Output: $0.30 per 1M tokens
    """
    INPUT_COST_PER_MILLION = 0.075
    OUTPUT_COST_PER_MILLION = 0.30

    input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_MILLION
    output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_MILLION

    return {
        'input_cost': input_cost,
        'output_cost': output_cost,
        'total_cost': input_cost + output_cost
    }
```

### Accessibility

**Screen reader support:**
```html
<button
  aria-expanded={isMetricsExpanded}
  aria-label={`${isMetricsExpanded ? 'Hide' : 'View'} token usage metrics (${totalTokens.toLocaleString()} tokens, ${totalCost.toFixed(4)} dollars)`}
>
  ...
</button>
```

**Keyboard navigation:**
- Tab to metrics button
- Enter/Space to toggle expand/collapse
- All metrics readable by screen readers

### Future Enhancements

**Phase 2 Features:**
1. **Cost breakdown by model**: Show which models were used
2. **Historical trends**: Track cost over time
3. **Budget alerts**: Warn when approaching limits
4. **Export**: Download metrics as CSV/JSON
5. **Comparison**: Compare costs between different queries

---

## Future Enhancements

### Phase 2 Features

1. **Timing visualization**: Show how long each step took
2. **Dependency graph**: Visual tree of delegation flow
3. **Step-by-step replay**: Animate the process
4. **Export**: Download the behind-the-scenes work
5. **Search**: Find specific steps in long conversations

### User Preferences

```typescript
interface UserPreferences {
  alwaysShowBehindTheScenes: boolean;
  defaultExpanded: boolean;
  showTimings: boolean;
  showRunIds: boolean;
}
```

---

## Implementation Checklist

**Core Features:**
- [x] Create `BehindTheScenes.tsx` component
- [x] Create message grouping logic in `Messages.tsx`
- [x] Add expand/collapse state management
- [x] Style collapsed and expanded states
- [x] Add icons (chevron, sparkles)
- [x] Test with real conversations
- [x] Add keyboard navigation
- [x] Add screen reader support
- [x] Document usage in main docs
- [x] Test performance with long conversations

**Reasoning Display (v1.2.16):**
- [x] Parse ReasoningStep/TeamReasoningStep events
- [x] Display reasoning content in Behind the Scenes
- [x] Style reasoning content (italic, left border)
- [x] Test with complex queries
- [x] Document reasoning feature

**Token Usage & Cost Metrics (v1.2.31):**
- [x] Add MetricsUpdate event type to RunEvent enum
- [x] Extract metrics from completion events during streaming
- [x] Calculate costs using Gemini 2.5 Flash Tier 1 pricing
- [x] Create BehindTheScenesEvent with metrics data
- [x] Filter metric events from main timeline (no duplicates)
- [x] Create single collapsible metrics box
- [x] Display individual agent/team metrics
- [x] Calculate and display conversation summary totals
- [x] Style metrics box (consistent borders, bold white titles)
- [x] Test with delegation flow
- [x] Document metrics feature

---

**Status:** ✅ **ALL FEATURES IMPLEMENTED AND DOCUMENTED**