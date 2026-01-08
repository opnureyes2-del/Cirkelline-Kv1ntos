# Basic Agent Usage

**Last Updated:** 2025-11-26
**AGNO Version:** v2.2.13
**Document Purpose:** Complete guide to basic agent usage patterns in AGNO

---

## Table of Contents

1. [Overview](#overview)
2. [Your First Agent](#your-first-agent)
3. [Basic Patterns](#basic-patterns)
4. [Agent Responses](#agent-responses)
5. [Common Use Cases](#common-use-cases)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Basic Agent Usage?

Basic agent usage covers the fundamental patterns for creating and running agents in AGNO:
- Creating a simple agent
- Executing single interactions
- Handling responses
- Common usage patterns

### Prerequisites

Before starting, ensure you have:
- AGNO installed: `pip install -U agno`
- Model provider library: `pip install openai` (or `anthropic`, `google-generativeai`)
- API key configured in environment

---

## Your First Agent

### Minimal Example

The simplest possible agent:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="You are a helpful assistant."
)

# Execute and print response
agent.print_response("What is 2+2?")
```

**Output:**
```
2 + 2 equals 4.
```

### Breaking it Down

**1. Import Required Classes**

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
```

- `Agent`: Core agent class
- `OpenAIChat`: OpenAI model wrapper

**2. Create Agent Instance**

```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="You are a helpful assistant."
)
```

Required parameters:
- `model`: Language model to use
- `instructions`: System instructions defining behavior

**3. Execute Request**

```python
agent.print_response("What is 2+2?")
```

- Sends message to agent
- Prints response to console
- Blocks until complete

---

## Basic Patterns

### Pattern 1: Print Response

Most direct way to use an agent:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="You are a helpful assistant. Keep responses brief."
)

agent.print_response("What healthy dinner can I have today?")
```

**When to Use:**
- Testing and debugging
- Quick prototypes
- Simple CLI tools
- Learning AGNO basics

**Limitations:**
- No access to response data
- No programmatic handling
- Console output only
- Blocking execution

### Pattern 2: Get Response Object

When you need to work with the response:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="You are a helpful assistant."
)

# Get response object
response = agent.run("What is the capital of France?")

# Access response content
print(response.content)

# Access metadata
print(f"Tokens: {response.metrics.get('response_tokens', 0)}")
```

**When to Use:**
- Production applications
- Need response metadata
- Multiple processing steps
- Error handling required

### Pattern 3: Streaming Responses

For real-time output:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="You are a helpful assistant."
)

# Stream response chunks
for chunk in agent.run("Tell me a story", stream=True):
    print(chunk.content, end="", flush=True)

print()  # New line after complete
```

**When to Use:**
- Chat interfaces
- Long-form content
- Better UX (shows progress)
- Real-time applications

### Pattern 4: Session-Based Conversations

For multi-turn conversations:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="You are a helpful assistant."
)

# Single session for conversation context
session_id = "user-123-session"

# First message
response1 = agent.run(
    "My name is Alice",
    session_id=session_id
)
print(response1.content)

# Second message - agent remembers context
response2 = agent.run(
    "What's my name?",
    session_id=session_id
)
print(response2.content)  # "Your name is Alice"
```

**When to Use:**
- Chat applications
- Multi-turn interactions
- Context-dependent tasks
- User conversations

---

## Agent Responses

### Understanding Response Objects

When you call `agent.run()`, you get a `RunResponse` object:

```python
response = agent.run("Hello")

# Access different parts
response.content          # Main response text
response.messages         # Message history
response.metrics          # Performance data
response.session_id       # Session identifier
response.run_id           # Unique run ID
```

### Response Content Types

**1. Text Response (Most Common)**

```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="You are a helpful assistant."
)

response = agent.run("What is Python?")
print(response.content)  # String with answer
```

**2. Structured Data (With JSON Mode)**

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="You extract user information as JSON.",
    response_model=UserInfo  # Pydantic model
)

response = agent.run("My name is John, I'm 30 years old")
print(response.content)  # UserInfo object
```

**3. Tool Call Results**

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[DuckDuckGoTools()],
    instructions="You are a helpful assistant."
)

response = agent.run("What's the weather in Paris?")
# Agent calls tool, synthesizes result
print(response.content)  # Natural language response with tool data
```

### Response Metrics

Understanding performance:

```python
response = agent.run("Hello")

# Access metrics
metrics = response.metrics

print(f"Input tokens: {metrics.get('input_tokens', 0)}")
print(f"Output tokens: {metrics.get('output_tokens', 0)}")
print(f"Total tokens: {metrics.get('total_tokens', 0)}")
print(f"Time taken: {metrics.get('time_to_first_token', 0)}s")
```

**Common Metrics:**
- `input_tokens`: Tokens in user message + context
- `output_tokens`: Tokens in agent response
- `total_tokens`: Sum of input + output
- `time_to_first_token`: Latency to start responding
- `total_time`: Complete execution time

---

## Common Use Cases

### Use Case 1: Simple Q&A Bot

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def create_qa_bot():
    """Create a simple question-answering bot"""
    return Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions="""You are a helpful Q&A assistant.
        Provide accurate, concise answers to user questions.
        If you don't know, say so."""
    )

# Use it
bot = create_qa_bot()
bot.print_response("What is machine learning?")
```

**Key Features:**
- Single interaction
- No tools needed
- Clear instructions
- Straightforward use case

### Use Case 2: Text Summarizer

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def create_summarizer():
    """Create a text summarization agent"""
    return Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions="""You are a text summarization expert.
        Provide concise summaries that capture key points.
        Use bullet points for clarity.
        Keep summaries under 100 words."""
    )

# Use it
summarizer = create_summarizer()

long_text = """
[Your long article text here...]
"""

response = summarizer.run(f"Summarize this: {long_text}")
print(response.content)
```

**Key Features:**
- Domain-specific instructions
- Input transformation
- Output formatting guidance
- Reusable pattern

### Use Case 3: Code Explainer

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def create_code_explainer():
    """Create a code explanation agent"""
    return Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions="""You are a code explanation expert.
        Explain code clearly for beginners.
        Break down complex logic step-by-step.
        Use analogies when helpful.""",
        markdown=True  # Enable markdown formatting
    )

# Use it
explainer = create_code_explainer()

code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''

response = explainer.run(f"Explain this code:\n```python\n{code}\n```")
print(response.content)
```

**Key Features:**
- Technical domain
- Markdown output
- Educational focus
- Code understanding

### Use Case 4: Interactive Chat

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def create_chatbot():
    """Create an interactive chatbot"""
    return Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions="""You are a friendly chat assistant.
        Engage naturally in conversation.
        Remember context from previous messages.
        Be helpful and personable."""
    )

def chat_loop():
    """Run interactive chat loop"""
    chatbot = create_chatbot()
    session_id = "interactive-session"

    print("Chatbot ready! (Type 'quit' to exit)")

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ['quit', 'exit']:
            print("Goodbye!")
            break

        if not user_input:
            continue

        # Get response with session context
        response = chatbot.run(user_input, session_id=session_id)
        print(f"\nBot: {response.content}")

# Run it
if __name__ == "__main__":
    chat_loop()
```

**Key Features:**
- Multi-turn conversation
- Session persistence
- User interaction loop
- Context awareness

### Use Case 5: Data Analyzer

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def create_data_analyzer():
    """Create a data analysis agent"""
    return Agent(
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions="""You are a data analysis expert.
        Analyze data patterns and provide insights.
        Present findings clearly with examples.
        Suggest actionable recommendations."""
    )

# Use it
analyzer = create_data_analyzer()

data = {
    "sales": [1000, 1200, 950, 1500, 1800],
    "months": ["Jan", "Feb", "Mar", "Apr", "May"]
}

prompt = f"""
Analyze this sales data:
{data}

Provide:
1. Trend analysis
2. Key insights
3. Recommendations
"""

response = analyzer.run(prompt)
print(response.content)
```

**Key Features:**
- Structured data input
- Analytical focus
- Multi-part response
- Business context

---

## Best Practices

### 1. Clear Instructions

**❌ Vague:**
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="Help users"
)
```

**✅ Specific:**
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="""You are a customer support assistant.
    - Be polite and professional
    - Provide accurate information
    - If unsure, escalate to human support
    - Keep responses under 3 sentences"""
)
```

**Why:** Specific instructions lead to consistent, predictable behavior.

### 2. Choose Right Model

**For Simple Tasks:**
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),  # Fast, cheap
    instructions="Translate to Spanish"
)
```

**For Complex Tasks:**
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),  # More capable
    instructions="Analyze code architecture and suggest improvements"
)
```

**Why:** Balance cost, speed, and capability based on task complexity.

### 3. Handle Errors

**❌ No Error Handling:**
```python
response = agent.run("Hello")
print(response.content)
```

**✅ With Error Handling:**
```python
try:
    response = agent.run("Hello")
    print(response.content)
except Exception as e:
    print(f"Error: {e}")
    # Log error, retry, or fallback
```

**Why:** Production systems must handle failures gracefully.

### 4. Use Sessions Appropriately

**❌ No Session for Chat:**
```python
# Each call loses context
agent.run("My name is Alice")
agent.run("What's my name?")  # Agent doesn't know
```

**✅ With Session:**
```python
session_id = "user-123"
agent.run("My name is Alice", session_id=session_id)
agent.run("What's my name?", session_id=session_id)  # Works!
```

**Why:** Sessions maintain conversation context across multiple interactions.

### 5. Efficient Prompting

**❌ Inefficient:**
```python
# Repeating instructions in every message
agent.run("Translate this to Spanish: Hello")
agent.run("Translate this to Spanish: Goodbye")
agent.run("Translate this to Spanish: Thank you")
```

**✅ Efficient:**
```python
# Instructions in agent definition
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="You translate English to Spanish"
)

agent.run("Hello")
agent.run("Goodbye")
agent.run("Thank you")
```

**Why:** Reduces token usage and improves consistency.

### 6. Validate Responses

**❌ Blind Trust:**
```python
response = agent.run("Is 2+2=5?")
# Assume response is correct
```

**✅ With Validation:**
```python
response = agent.run("Calculate: 2+2")

# Validate critical responses
if "4" in response.content:
    print("Correct!")
else:
    print("Warning: Unexpected response")
    # Log for review
```

**Why:** LLMs can make mistakes; validate critical information.

### 7. Monitor Token Usage

**Track Usage:**
```python
response = agent.run("Hello")

tokens_used = response.metrics.get('total_tokens', 0)

if tokens_used > 1000:
    print(f"Warning: High token usage ({tokens_used})")
    # Investigate why
```

**Why:** Control costs and identify inefficiencies.

### 8. Use Markdown When Needed

**For Formatted Output:**
```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="Explain technical concepts clearly",
    markdown=True  # Enable markdown formatting
)

response = agent.run("Explain HTTP methods")
# Response will use markdown formatting
```

**Why:** Better readability for technical or structured content.

---

## Troubleshooting

### Common Issues

#### Issue 1: API Key Not Found

**Error:**
```
openai.AuthenticationError: Invalid API key
```

**Solution:**
```bash
# Set environment variable
export OPENAI_API_KEY="sk-..."

# Or in Python
import os
os.environ["OPENAI_API_KEY"] = "sk-..."
```

#### Issue 2: Model Not Found

**Error:**
```
openai.NotFoundError: Model 'gpt-5-mini' not found
```

**Solution:**
```python
# Use correct model ID
agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),  # Correct
    instructions="You are a helpful assistant."
)
```

#### Issue 3: Rate Limit Exceeded

**Error:**
```
openai.RateLimitError: Rate limit exceeded
```

**Solution:**
```python
import time

def run_with_retry(agent, message, max_retries=3):
    """Run with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return agent.run(message)
        except RateLimitError:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
```

#### Issue 4: Empty Response

**Problem:**
```python
response = agent.run("Hello")
print(response.content)  # Empty or None
```

**Solution:**
```python
# Check if response has content
if response and response.content:
    print(response.content)
else:
    print("No response received")
    # Check logs for errors
```

#### Issue 5: Context Lost Between Messages

**Problem:**
```python
agent.run("My name is Alice")
agent.run("What's my name?")  # Doesn't know
```

**Solution:**
```python
# Use session_id
session_id = "user-session"
agent.run("My name is Alice", session_id=session_id)
agent.run("What's my name?", session_id=session_id)  # Works!
```

#### Issue 6: Slow Response Time

**Diagnosis:**
```python
import time

start = time.time()
response = agent.run("Hello")
elapsed = time.time() - start

print(f"Response time: {elapsed:.2f}s")
```

**Solutions:**
- Use faster model (gpt-4o-mini vs gpt-4o)
- Reduce context size
- Enable streaming for better UX
- Check network connection
- Monitor API status

---

## Next Steps

After mastering basic usage:

1. **Learn Advanced Patterns:**
   - Async execution
   - Batch processing
   - Custom tools
   - Response models

2. **Explore Agent Features:**
   - Memory management
   - Tool integration
   - Knowledge bases
   - Team coordination

3. **Production Considerations:**
   - Error handling
   - Rate limiting
   - Monitoring
   - Cost optimization

4. **Read More:**
   - `02-running-agents.md` - Advanced execution patterns
   - `03-debugging-agents.md` - Debug and troubleshoot
   - Official AGNO docs: https://docs.agno.com

---

## Summary

**Basic agent usage covers:**
- Creating simple agents
- Executing requests
- Handling responses
- Common patterns
- Best practices

**Key Takeaways:**
1. Start simple with `Agent` + `model` + `instructions`
2. Use `print_response()` for testing, `run()` for production
3. Always handle errors in production
4. Use sessions for multi-turn conversations
5. Monitor token usage and costs

**Remember:** Master these basics before moving to advanced features!

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-11-26
**Next:** Advanced usage patterns and features
