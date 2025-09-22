import asyncio
from cmd import PROMPT
from typing import Any
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
import os

def display_message(msg):
    """Display message content in a clean format."""
    from claude_code_sdk import (
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

    # Load the latest evaluation JSON - now using the new results from failed tests
    with open('src/query/evaluation_results_20250922_173925.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['results']

    print(f"Loaded {len(results)} evaluation results")

    # Count existing evaluations
    already_evaluated = sum(1 for r in results if 'evaluation' in r and r['evaluation'].get('score'))
    remaining = len(results) - already_evaluated

    print(f"Already evaluated: {already_evaluated}/{len(results)}")
    print(f"Remaining to evaluate: {remaining}")
    print("="*80)

    evaluated_count = 0
    for i, result in enumerate(results, 1):  # Process all 27 previously failed questions
        # Skip if evaluation already exists
        if 'evaluation' in result and result['evaluation'].get('score'):
            continue

        PROMPT = f"""
        Please evaluate if the actual answer matches the expected answer for this financial question.

        Question: {result.get('question', 'N/A')}

        Expected Answer: {result.get('expected_answer', 'N/A')}

        Actual Answer: {result.get('actual_answer', 'N/A')}

        Please provide:
        1. Score: "correct", "partial", or "incorrect"
        2. Brief reasoning (1-2 sentences)

        Focus on whether the factual content and key financial data match, allowing for minor formatting differences.

        Return your response in this exact format:
        SCORE: [correct/partial/incorrect]
        REASONING: [your reasoning]

        Dont redo the question or answer. Just evaluate the actual answer against the expected answer.
        """

        evaluation_response = ""
        async with ClaudeSDKClient() as client:
            await client.query(PROMPT)
            async for message in client.receive_response():
                display_message(message)
                from claude_code_sdk import AssistantMessage, TextBlock
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            evaluation_response += block.text

        # Parse the evaluation response
        score = None
        reasoning = None

        if "SCORE:" in evaluation_response:
            score_line = [line for line in evaluation_response.split('\n') if 'SCORE:' in line][0]
            score = score_line.split('SCORE:')[1].strip().lower()

        if "REASONING:" in evaluation_response:
            reasoning_line = [line for line in evaluation_response.split('\n') if 'REASONING:' in line][0]
            reasoning = reasoning_line.split('REASONING:')[1].strip()

        # Store evaluation in the result
        result['evaluation'] = {
            'score': score,
            'reasoning': reasoning
        }

        evaluated_count += 1
        total_evaluated = already_evaluated + evaluated_count
        print(f"\nStored evaluation for question {result.get('financebench_id')}: {score}")
        print(f"Progress: {total_evaluated}/{len(results)} total evaluated ({evaluated_count} new this session)")

        # Save updated data back to JSON after each evaluation
        with open('src/query/evaluation_results_20250922_173925.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Saved to JSON file")

    print("All evaluation results completed and saved")
        

if __name__ == "__main__":
    asyncio.run(main())
    