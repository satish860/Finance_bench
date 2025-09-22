import asyncio
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
    from datetime import datetime

    options = ClaudeCodeOptions(
        cwd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )

    # Load questions from JSONL file
    questions_file = os.path.join(os.path.dirname(__file__), "financebench_open_source.jsonl")
    questions = []

    with open(questions_file, 'r', encoding='utf-8') as f:
        for line in f:
            question_data = json.loads(line.strip())
            questions.append(question_data)

    # Initialize results storage
    results = []
    total_cost = 0.0

    # Process all questions
    total_questions = len(questions)
    print(f"Found {total_questions} questions to process...")

    for i, question_data in enumerate(questions):
        try:
            print(f"\n{'='*80}")
            print(f"PROCESSING QUESTION {i+1}/{total_questions}")
            print(f"Company: {question_data['company']}")
            print(f"Question: {question_data['question']}")
            print(f"Expected Answer: {question_data['answer']}")
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

            # Store result for evaluation
            result = {
                "financebench_id": question_data.get("financebench_id", f"question_{i+1}"),
                "company": question_data["company"],
                "question": question_data["question"],
                "expected_answer": question_data["answer"],
                "actual_answer": actual_answer.strip(),
                "question_cost_usd": question_cost,
                "question_type": question_data.get("question_type", "unknown"),
                "doc_name": question_data.get("doc_name", "unknown"),
                "status": "completed"
            }
            results.append(result)

            # Progress update and save every 10 questions
            if (i + 1) % 10 == 0:
                print(f"\n[PROGRESS] Completed {i+1}/{total_questions} questions. Running cost: ${total_cost:.4f}")

                # Save intermediate results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                intermediate_file = os.path.join(os.path.dirname(__file__), f"evaluation_results_intermediate_{timestamp}.json")

                intermediate_data = {
                    "timestamp": timestamp,
                    "status": "in_progress",
                    "completed_questions": i + 1,
                    "total_questions": total_questions,
                    "total_cost_usd": total_cost,
                    "results": results
                }

                with open(intermediate_file, 'w', encoding='utf-8') as f:
                    json.dump(intermediate_data, f, indent=2, ensure_ascii=False)

                print(f"[BACKUP] Intermediate results saved to: {intermediate_file}")

        except Exception as e:
            print(f"\n[ERROR] Question {i+1} failed: {str(e)}")
            # Store error result
            error_result = {
                "financebench_id": question_data.get("financebench_id", f"question_{i+1}"),
                "company": question_data["company"],
                "question": question_data["question"],
                "expected_answer": question_data["answer"],
                "actual_answer": f"ERROR: {str(e)}",
                "question_cost_usd": 0.0,
                "question_type": question_data.get("question_type", "unknown"),
                "doc_name": question_data.get("doc_name", "unknown"),
                "status": "error"
            }
            results.append(error_result)
            continue

    # Save results to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(os.path.dirname(__file__), f"evaluation_results_{timestamp}.json")

    evaluation_data = {
        "timestamp": timestamp,
        "status": "completed",
        "total_questions": len(results),
        "completed_questions": len([r for r in results if r.get("status") == "completed"]),
        "error_questions": len([r for r in results if r.get("status") == "error"]),
        "total_cost_usd": total_cost,
        "results": results
    }

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"EVALUATION COMPLETE")
    print(f"Results saved to: {results_file}")
    print(f"Total questions processed: {len(results)}")
    print(f"Total cost: ${total_cost:.6f}")
    print('='*80)



if __name__ == "__main__":
    asyncio.run(main())
