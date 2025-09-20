# Claude Code SDK for Python - Complete Usage Guide

## Overview

The Claude Code SDK for Python provides a programmatic interface to interact with Claude Code, enabling developers to build applications that leverage Claude's code generation and interaction capabilities. This SDK supports async operations, custom tool creation, hooks for advanced control, and flexible configuration options.

## Prerequisites

- **Python**: 3.10+
- **Node.js**: Required for Claude Code CLI
- **Claude Code CLI**: Install with `npm install -g @anthropic-ai/claude-code`

## Installation

```bash
pip install claude-code-sdk
# or using uv
uv add claude-code-sdk
```

## Core Concepts

### 1. Basic Query Interface
The `query()` function is the primary entry point for interacting with Claude Code.

### 2. Message Types
- **AssistantMessage**: Messages from Claude containing text blocks
- **ResultMessage**: Contains metadata like cost information
- **TextBlock**: Text content within messages

### 3. Options Configuration
`ClaudeCodeOptions` allows you to customize Claude's behavior, including system prompts, tool permissions, and hooks.

## Basic Usage Examples

### Simple Query
```python
import anyio
from claude_code_sdk import query

async def basic_query():
    async for message in query(prompt="What is 2 + 2?"):
        print(message)

anyio.run(basic_query)
```

### Query with Message Type Handling
```python
import anyio
from claude_code_sdk import (
    AssistantMessage,
    TextBlock,
    ResultMessage,
    query
)

async def formatted_query():
    async for message in query(prompt="Explain Python in one sentence"):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
        elif isinstance(message, ResultMessage):
            if message.total_cost_usd > 0:
                print(f"Cost: ${message.total_cost_usd:.4f}")

anyio.run(formatted_query)
```

### Using Options
```python
from claude_code_sdk import ClaudeCodeOptions

options = ClaudeCodeOptions(
    system_prompt="You are a helpful coding assistant.",
    max_turns=1,
    allowed_tools=["Read", "Write", "Bash"]
)

async for message in query(
    prompt="Create a simple Python script",
    options=options
):
    # Handle messages...
```

## Custom Tools Creation

### Basic Tool Definition
```python
from claude_code_sdk import tool, create_sdk_mcp_server

@tool("greet", "Greet a user by name", {"name": str})
async def greet_user(args):
    """Greet a user with their name."""
    name = args.get("name", "World")
    return {
        "content": [
            {"type": "text", "text": f"Hello, {name}! Nice to meet you."}
        ]
    }
```

### Mathematical Calculator Tools
```python
@tool("add", "Add two numbers", {"a": float, "b": float})
async def add_numbers(args):
    """Add two numbers together."""
    result = args["a"] + args["b"]
    return {
        "content": [
            {"type": "text", "text": f"{args['a']} + {args['b']} = {result}"}
        ]
    }

@tool("divide", "Divide two numbers", {"a": float, "b": float})
async def divide_numbers(args):
    """Divide two numbers with error handling."""
    if args["b"] == 0:
        return {
            "content": [
                {"type": "text", "text": "Error: Cannot divide by zero"}
            ],
            "isError": True
        }

    result = args["a"] / args["b"]
    return {
        "content": [
            {"type": "text", "text": f"{args['a']} ÷ {args['b']} = {result}"}
        ]
    }
```

### Creating MCP Server
```python
from claude_code_sdk import create_sdk_mcp_server, ClaudeCodeOptions

# Create server with your tools
server = create_sdk_mcp_server(
    name="my-calculator",
    version="1.0.0",
    tools=[add_numbers, divide_numbers, greet_user]
)

# Configure options to use your custom server
options = ClaudeCodeOptions(
    mcp_servers=[server],
    system_prompt="You are a helpful assistant with calculator capabilities."
)
```

## Advanced Features

### Hooks for Control Flow
```python
from claude_code_sdk import HookMatcher

async def validate_bash_command(input_data, tool_use_id, context):
    """Hook to validate bash commands before execution."""
    command = input_data.get("command", "")

    # Block dangerous commands
    dangerous_commands = ["rm -rf", "sudo", "chmod 777"]
    for dangerous in dangerous_commands:
        if dangerous in command:
            return {
                "action": "block",
                "reason": f"Blocked dangerous command: {dangerous}"
            }

    # Allow safe commands
    return {"action": "allow"}

async def log_tool_usage(input_data, tool_use_id, context):
    """Hook to log all tool usage."""
    print(f"Tool used: {context.get('tool_name')} with args: {input_data}")
    return {"action": "allow"}

options = ClaudeCodeOptions(
    allowed_tools=["Bash", "Read", "Write"],
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[validate_bash_command]),
            HookMatcher(matcher="*", hooks=[log_tool_usage]),
        ],
    }
)
```

### Interactive Client
```python
from claude_code_sdk import ClaudeSDKClient

async def interactive_session():
    client = ClaudeSDKClient()

    # Start conversation
    await client.start_conversation()

    # Send multiple messages
    response1 = await client.send_message("What is Python?")
    response2 = await client.send_message("Give me a simple Python example")

    # Process responses
    for message in [response1, response2]:
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
```

## Complete Example: Financial Document Analyzer

Here's a practical example for our FinanceBench use case:

```python
import anyio
from claude_code_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeCodeOptions,
    query,
    AssistantMessage,
    TextBlock
)
import json
from pathlib import Path

@tool("load_document_segments", "Load financial document segments", {
    "doc_name": str
})
async def load_document_segments(args):
    """Load segments for a financial document."""
    doc_name = args["doc_name"]
    segment_file = Path(f".finance/segments/{doc_name}.json")

    if not segment_file.exists():
        return {
            "content": [{"type": "text", "text": f"Document {doc_name} not found"}],
            "isError": True
        }

    with open(segment_file, 'r') as f:
        segments = json.load(f)

    return {
        "content": [
            {"type": "text", "text": f"Loaded {len(segments.get('segments', []))} segments for {doc_name}"}
        ]
    }

@tool("search_segments", "Search within document segments", {
    "doc_name": str,
    "query": str
})
async def search_segments(args):
    """Search for specific content within document segments."""
    doc_name = args["doc_name"]
    search_query = args["query"].lower()

    segment_file = Path(f".finance/segments/{doc_name}.json")
    if not segment_file.exists():
        return {
            "content": [{"type": "text", "text": f"Document {doc_name} not found"}],
            "isError": True
        }

    with open(segment_file, 'r') as f:
        data = json.load(f)

    matching_segments = []
    for segment in data.get("segments", []):
        if search_query in segment.get("heading", "").lower() or \
           search_query in segment.get("description", "").lower():
            matching_segments.append(segment)

    result_text = f"Found {len(matching_segments)} segments matching '{search_query}' in {doc_name}\\n"
    for seg in matching_segments[:3]:  # Show first 3 matches
        result_text += f"- {seg.get('heading', 'N/A')}: {seg.get('description', 'N/A')[:100]}...\\n"

    return {
        "content": [{"type": "text", "text": result_text}]
    }

async def financial_analysis_agent():
    """Example of using Claude Code SDK for financial document analysis."""

    # Create custom MCP server with financial tools
    financial_server = create_sdk_mcp_server(
        name="financebench-tools",
        version="1.0.0",
        tools=[load_document_segments, search_segments]
    )

    # Configure options
    options = ClaudeCodeOptions(
        mcp_servers=[financial_server],
        allowed_tools=["Read", "Write"],
        system_prompt="""You are a financial analyst assistant with access to
        segmented financial documents. Use the provided tools to analyze
        financial documents and answer questions about company performance.""",
        max_turns=5
    )

    # Example queries
    queries = [
        "Load the segments for document 3M_2018_10K and tell me about capital expenditure",
        "Search for 'revenue' in the 3M_2018_10K document and summarize the findings"
    ]

    for query_text in queries:
        print(f"\\n=== Query: {query_text} ===")

        async for message in query(prompt=query_text, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

# Run the example
anyio.run(financial_analysis_agent)
```

## Error Handling

```python
from claude_code_sdk import ClaudeCodeError

async def robust_query():
    try:
        async for message in query(prompt="Analyze this data"):
            # Process messages
            pass
    except ClaudeCodeError as e:
        print(f"Claude Code error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Best Practices

1. **Use Type Hints**: Define clear parameter types for your custom tools
2. **Error Handling**: Always handle potential errors in custom tools
3. **Resource Management**: Use async context managers when appropriate
4. **Tool Validation**: Implement input validation in custom tools
5. **Performance**: Consider caching for frequently accessed data
6. **Security**: Use hooks to validate and sanitize inputs

## Configuration Options

### ClaudeCodeOptions Parameters
- `system_prompt`: Custom system prompt for Claude
- `max_turns`: Maximum conversation turns
- `allowed_tools`: List of allowed tool names
- `mcp_servers`: List of custom MCP servers
- `hooks`: Dictionary of hooks for different events
- `temperature`: Sampling temperature (0.0 to 1.0)
- `max_tokens`: Maximum tokens in response

This guide provides a comprehensive foundation for using the Claude Code SDK in your applications, particularly for building intelligent document analysis systems like our FinanceBench project.