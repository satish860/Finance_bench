import asyncio
from typing import Any
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server
import os
from financial_calculators import (
    calculate_dpo, calculate_roa, calculate_inventory_turnover,
    calculate_quick_ratio, calculate_margins, calculate_effective_tax_rate,
    calculate_working_capital, calculate_capex_metrics
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

async def main():
    import json
    from datetime import datetime

    # Create financial calculator MCP server
    financial_server = create_sdk_mcp_server(
        name="financebench-calculators",
        version="1.0.0",
        tools=[
            calculate_dpo, calculate_roa, calculate_inventory_turnover,
            calculate_quick_ratio, calculate_margins, calculate_effective_tax_rate,
            calculate_working_capital, calculate_capex_metrics
        ]
    )

    options = ClaudeAgentOptions(
        cwd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        mcp_servers=[financial_server],
        allowed_tools=[
            "Read", "Write", "Glob", "Grep", "Bash",
            "mcp__financebench-calculators__calculate_dpo",
            "mcp__financebench-calculators__calculate_roa",
            "mcp__financebench-calculators__calculate_inventory_turnover",
            "mcp__financebench-calculators__calculate_quick_ratio",
            "mcp__financebench-calculators__calculate_margins",
            "mcp__financebench-calculators__calculate_effective_tax_rate",
            "mcp__financebench-calculators__calculate_working_capital",
            "mcp__financebench-calculators__calculate_capex_metrics"
        ],
        system_prompt="""You are a financial analysis expert with access to specialized financial calculation tools.

When answering questions that involve financial calculations, you should:
1. Use the appropriate calculator tools for complex financial metrics (DPO, ROA, inventory turnover, quick ratio, margins, tax rates, working capital, capex)
2. For simple arithmetic, you can calculate manually
3. Always validate results using the tool's built-in sanity checks
4. Use the standardized interpretations provided by the tools

Available financial calculator tools:
- calculate_dpo: For Days Payable Outstanding calculations
- calculate_roa: For Return on Assets calculations
- calculate_inventory_turnover: For inventory turnover ratios
- calculate_quick_ratio: For liquidity analysis with health assessment
- calculate_margins: For margin trend analysis
- calculate_effective_tax_rate: For tax rate calculations handling negative income
- calculate_working_capital: For working capital analysis
- calculate_capex_metrics: For capital expenditure analysis and averages

Use these tools when the question involves these specific metrics to ensure accuracy and consistency."""
    )

    # Test specific calculation questions
    test_questions = [
        {
            "financebench_id": "test_amazon_dpo",
            "company": "Amazon",
            "question": "What is Amazon's FY2017 days payable outstanding (DPO)? DPO is defined as: 365 * (average accounts payable between FY2016 and FY2017) / (FY2017 COGS + change in inventory between FY2016 and FY2017). Round your answer to two decimal places.",
            "expected_answer": "93.86"
        },
        {
            "financebench_id": "test_3m_quick_ratio",
            "company": "3M",
            "question": "Does 3M have a reasonably healthy liquidity profile based on its quick ratio for Q2 of FY2023?",
            "expected_answer": "No. The quick ratio for 3M was 0.96 by Jun'23 close, which needs a bit of an improvement to touch the 1x mark"
        }
    ]

    # Initialize results storage
    results = []
    total_cost = 0.0

    # Process test questions
    for i, question_data in enumerate(test_questions):
        try:
            print(f"\n{'='*80}")
            print(f"TESTING QUESTION {i+1}/{len(test_questions)}")
            print(f"Company: {question_data['company']}")
            print(f"Question: {question_data['question']}")
            print(f"Expected Answer: {question_data['expected_answer']}")
            print('='*80)

            # Collect Claude's response
            actual_answer = ""
            question_cost = 0.0

            async with ClaudeSDKClient(options) as client:
                await client.query(question_data['question'])

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

            # Store result
            result = {
                "financebench_id": question_data["financebench_id"],
                "company": question_data["company"],
                "question": question_data["question"],
                "expected_answer": question_data["expected_answer"],
                "actual_answer": actual_answer.strip(),
                "question_cost_usd": question_cost,
                "status": "completed"
            }
            results.append(result)

        except Exception as e:
            print(f"\n[ERROR] Question {i+1} failed: {str(e)}")
            continue

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(os.path.dirname(__file__), f"calculator_test_results_{timestamp}.json")

    test_data = {
        "timestamp": timestamp,
        "status": "completed",
        "total_questions": len(results),
        "total_cost_usd": total_cost,
        "results": results
    }

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"CALCULATOR TOOL TEST COMPLETE")
    print(f"Results saved to: {results_file}")
    print(f"Total questions tested: {len(results)}")
    print(f"Total cost: ${total_cost:.6f}")
    print('='*80)


if __name__ == "__main__":
    asyncio.run(main())