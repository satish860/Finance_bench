import asyncio
from typing import Any
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server
import os
import json
from datetime import datetime

# Import financial calculators
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'query'))
from financial_calculators import (
    calculate_dpo, calculate_roa, calculate_inventory_turnover,
    calculate_quick_ratio, calculate_margins, calculate_effective_tax_rate,
    calculate_working_capital, calculate_capex_metrics, find_company_documents
)

def display_message(msg):
    """Display message content in a clean format."""
    from claude_agent_sdk import (
        AssistantMessage,
        ResultMessage,
        SystemMessage,
        TextBlock,
        ToolResultBlock,
        ToolUseBlock,
        UserMessage,
    )

    if isinstance(msg, UserMessage):
        print("\n" + "="*60)
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"USER: {block.text}")
            elif isinstance(block, ToolResultBlock):
                print(f"TOOL RESULT:\n{block.content}")
        print("="*60)

    elif isinstance(msg, AssistantMessage):
        print("\n" + "-"*60)
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"CLAUDE: {block.text}")
            elif isinstance(block, ToolUseBlock):
                print(f"[TOOL: {block.name}]")
        print("-"*60)

    elif isinstance(msg, SystemMessage):
        # Skip system messages for cleaner output
        pass

    elif isinstance(msg, ResultMessage):
        print("\n" + "="*60)
        print("CONVERSATION COMPLETE")
        if msg.total_cost_usd:
            print(f"Cost: ${msg.total_cost_usd:.6f}")
        print("="*60 + "\n")

async def test_thinking_mode():
    # Create financial calculator MCP server
    financial_server = create_sdk_mcp_server(
        name="financebench-calculators",
        version="1.0.0",
        tools=[
            calculate_dpo, calculate_roa, calculate_inventory_turnover,
            calculate_quick_ratio, calculate_margins, calculate_effective_tax_rate,
            calculate_working_capital, calculate_capex_metrics, find_company_documents
        ]
    )

    options = ClaudeAgentOptions(
        cwd=os.path.dirname(os.path.abspath(__file__)),
        mcp_servers={"financebench-calculators": financial_server},
        thinking_mode="auto",  # Enable thinking mode for complex financial reasoning
        allowed_tools=[
            "Read", "Write", "Glob", "Grep", "Bash",
            "mcp__financebench-calculators__calculate_dpo",
            "mcp__financebench-calculators__calculate_roa",
            "mcp__financebench-calculators__calculate_inventory_turnover",
            "mcp__financebench-calculators__calculate_quick_ratio",
            "mcp__financebench-calculators__calculate_margins",
            "mcp__financebench-calculators__calculate_effective_tax_rate",
            "mcp__financebench-calculators__calculate_working_capital",
            "mcp__financebench-calculators__calculate_capex_metrics",
            "mcp__financebench-calculators__find_company_documents"
        ]
    )

    # Load first 3 questions from the dataset
    questions_file = os.path.join("src", "query", "financebench_open_source.jsonl")
    test_questions = []

    with open(questions_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 3:  # Only take first 3 questions
                break
            question_data = json.loads(line.strip())
            test_questions.append(question_data)

    # Process each test question
    results = []
    total_cost = 0.0

    PROMPT = """
You are a financial document analysis expert using a RAG system. Before answering the question, please think through your approach systematically.

**QUESTION:** {question}

**THINKING PROCESS:**
Please work through this step by step:

1. **Question Analysis**: What type of financial information is being requested? What specific metrics, calculations, or data points do I need to find?

2. **Search Strategy**: What documents should I search for? What financial terms, company names, years, or sections should I look for?

3. **Data Requirements**: What specific financial statement items, numbers, or calculations will I need to extract?

4. **Approach Planning**: What tools should I use (Glob for finding documents, Grep for searching content, financial calculators for computations)?

5. **Execution Plan**: In what order should I perform the searches and calculations to get the most accurate answer?

Now please execute your plan and provide a comprehensive answer with proper citations.
    """

    for i, question_data in enumerate(test_questions):
        try:
            print(f"\n{'='*80}")
            print(f"TESTING QUESTION {i+1}/3 WITH THINKING MODE")
            print(f"Company: {question_data['company']}")
            print(f"Question: {question_data['question']}")
            print(f"Expected Answer: {question_data['answer']}")
            print('='*80)

            # Collect Claude's response
            actual_answer = ""
            question_cost = 0.0

            enhanced_prompt = PROMPT.format(question=question_data['question'])

            async with ClaudeSDKClient(options) as client:
                await client.query(enhanced_prompt)

                async for msg in client.receive_response():
                    display_message(msg)

                    # Extract actual answer from Claude's response
                    if hasattr(msg, 'content') and msg.content:
                        for block in msg.content:
                            if hasattr(block, 'text'):
                                actual_answer += block.text + " "

                    # Extract cost information
                    if hasattr(msg, 'total_cost_usd') and msg.total_cost_usd:
                        question_cost = msg.total_cost_usd
                        total_cost += question_cost

            # Store result for comparison
            result = {
                "question_num": i + 1,
                "company": question_data["company"],
                "question": question_data["question"],
                "expected_answer": question_data["answer"],
                "actual_answer": actual_answer.strip(),
                "question_cost_usd": question_cost,
                "question_type": question_data.get("question_type", "unknown")
            }
            results.append(result)

            print(f"\n[RESULT {i+1}] Cost: ${question_cost:.4f}")
            print(f"Expected: {question_data['answer']}")
            print(f"Actual: {actual_answer.strip()[:200]}...")

        except Exception as e:
            print(f"\n[ERROR] Question {i+1} failed: {str(e)}")
            continue

    # Save test results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"thinking_mode_test_results_{timestamp}.json"

    test_data = {
        "timestamp": timestamp,
        "thinking_mode_enabled": True,
        "total_questions": len(test_questions),
        "completed_questions": len(results),
        "total_cost_usd": total_cost,
        "average_cost_per_question": total_cost / len(results) if results else 0,
        "results": results
    }

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"THINKING MODE TEST COMPLETE")
    print(f"Results saved to: {results_file}")
    print(f"Total questions tested: {len(results)}")
    print(f"Total cost: ${total_cost:.6f}")
    print(f"Average cost per question: ${total_cost / len(results) if results else 0:.6f}")
    print('='*80)

if __name__ == "__main__":
    asyncio.run(test_thinking_mode())