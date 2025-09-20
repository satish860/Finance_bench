#!/usr/bin/env python3
"""
FinanceBench Agent - Main agent loop for answering financial questions.

This module implements the core agent that:
- Loads questions from FinanceBench dataset
- Uses custom tools to analyze financial documents
- Applies the "emergence over engineering" principle
- Provides accurate financial analysis responses
"""

import anyio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from claude_code_sdk import (
    AssistantMessage,
    TextBlock,
    ResultMessage,
    ClaudeCodeOptions,
    create_sdk_mcp_server,
    query
)

# Import our custom tools
try:
    from .tools import FINANCEBENCH_TOOLS
except ImportError:
    # For standalone execution
    from tools import FINANCEBENCH_TOOLS


# USD to INR conversion rate (approximate for 2025)
USD_TO_INR = 84.0


class FinanceBenchAgent:
    """Main agent for processing FinanceBench questions using Claude Code SDK."""

    def __init__(self, questions_file: str = "financebench_open_source.jsonl",
                 instructions_file: str = "FINANCEBENCH_CLAUDE.md"):
        """
        Initialize the FinanceBench agent.

        Args:
            questions_file: Path to the FinanceBench questions JSONL file
            instructions_file: Path to the Claude instructions markdown file
        """
        self.questions_file = Path(questions_file)
        self.instructions_file = Path(instructions_file)

        # Load system prompt from instructions file
        self.system_prompt = self._load_system_prompt()

        # Create MCP server with our custom tools
        self.mcp_server = create_sdk_mcp_server(
            name="financebench-tools",
            version="1.0.0",
            tools=FINANCEBENCH_TOOLS
        )

        # Configure Claude Code options
        self.claude_options = ClaudeCodeOptions(
            mcp_servers={"financebench": self.mcp_server},
            allowed_tools=[
                "mcp__financebench__load_document_info",
                "mcp__financebench__load_document_segments",
                "mcp__financebench__search_document_content",
                "mcp__financebench__extract_page_range",
                "Read"
            ],
            system_prompt=self.system_prompt,
            max_turns=10  # Allow multiple interactions for complex questions
        )

    def _load_system_prompt(self) -> str:
        """Load system prompt from the instructions file."""
        try:
            with open(self.instructions_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Could not load instructions from {self.instructions_file}: {e}")
            return "You are a financial analyst. Answer questions about financial documents using the provided tools."

    def load_questions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load questions from the FinanceBench dataset.

        Args:
            limit: Maximum number of questions to load (None for all)

        Returns:
            List of question dictionaries
        """
        questions = []

        try:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if limit and i >= limit:
                        break

                    if line.strip():
                        question = json.loads(line.strip())
                        questions.append(question)

        except Exception as e:
            print(f"Error loading questions from {self.questions_file}: {e}")

        return questions

    async def process_single_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single question using the Claude Code SDK.

        Args:
            question_data: Dictionary containing question information

        Returns:
            Dictionary containing the response and metadata
        """
        question_id = question_data.get("financebench_id", "unknown")
        question_text = question_data.get("question", "")
        doc_name = question_data.get("doc_name", "")
        expected_answer = question_data.get("answer", "")
        company = question_data.get("company", "")

        print(f"\nProcessing Question {question_id}")
        print(f"Company: {company}")
        print(f"Document: {doc_name}")
        print(f"Question: {question_text}")
        print("=" * 80)

        # Prepare the prompt with context
        prompt = f"""Question: {question_text}

Document to analyze: {doc_name}
Company: {company}

Please analyze this financial document to answer the question accurately."""

        response_data = {
            "question_id": question_id,
            "question": question_text,
            "doc_name": doc_name,
            "company": company,
            "expected_answer": expected_answer,
            "claude_response": "",
            "cost_usd": 0.0,
            "cost_inr": 0.0,
            "error": None
        }

        try:
            # Use the one-liner research agent pattern
            messages = []
            async for message in query(prompt=prompt, options=self.claude_options):
                messages.append(message)

                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"Claude: {block.text}")
                            response_data["claude_response"] += block.text + "\n"

                elif isinstance(message, ResultMessage):
                    if hasattr(message, 'total_cost_usd') and message.total_cost_usd > 0:
                        cost_usd = message.total_cost_usd
                        cost_inr = cost_usd * USD_TO_INR
                        response_data["cost_usd"] = cost_usd
                        response_data["cost_inr"] = cost_inr
                        print(f"Cost: ${cost_usd:.4f} USD (Rs.{cost_inr:.2f} INR)")

        except Exception as e:
            error_msg = f"Error processing question: {str(e)}"
            print(f"Error: {error_msg}")
            response_data["error"] = error_msg

        return response_data

    async def process_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple questions and return results.

        Args:
            questions: List of question dictionaries

        Returns:
            List of response dictionaries
        """
        results = []

        for i, question in enumerate(questions, 1):
            print(f"\nProcessing Question {i}/{len(questions)}")

            try:
                result = await self.process_single_question(question)
                results.append(result)

                # Brief pause between questions
                await anyio.sleep(1)

            except KeyboardInterrupt:
                print("\nProcessing interrupted by user")
                break
            except Exception as e:
                print(f"Error processing question {i}: {e}")
                error_result = {
                    "question_id": question.get("financebench_id", f"question_{i}"),
                    "error": str(e),
                    "question": question.get("question", ""),
                    "doc_name": question.get("doc_name", ""),
                    "company": question.get("company", "")
                }
                results.append(error_result)

        return results

    def save_results(self, results: List[Dict[str, Any]],
                    output_file: str = "financebench_agent_results.json"):
        """
        Save results to a JSON file.

        Args:
            results: List of result dictionaries
            output_file: Output file path
        """
        try:
            output_path = Path(output_file)

            # Add metadata to results
            output_data = {
                "metadata": {
                    "total_questions": len(results),
                    "successful_questions": len([r for r in results if not r.get("error")]),
                    "failed_questions": len([r for r in results if r.get("error")]),
                    "total_cost_usd": sum(r.get("cost_usd", 0) for r in results),
                    "total_cost_inr": sum(r.get("cost_inr", 0) for r in results)
                },
                "results": results
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"\nResults saved to {output_path}")
            print(f"Summary: {output_data['metadata']['successful_questions']}/{output_data['metadata']['total_questions']} successful")
            print(f"Total Cost: ${output_data['metadata']['total_cost_usd']:.4f} USD (Rs.{output_data['metadata']['total_cost_inr']:.2f} INR)")

        except Exception as e:
            print(f"Error saving results: {e}")


async def run_agent(num_questions: int = 5, output_file: str = "financebench_agent_results.json"):
    """
    Run the FinanceBench agent on a subset of questions.

    Args:
        num_questions: Number of questions to process
        output_file: Output file for results
    """
    print("Starting FinanceBench Agent")
    print("=" * 50)

    # Initialize agent
    agent = FinanceBenchAgent()

    # Load questions
    print(f"Loading {num_questions} questions...")
    questions = agent.load_questions(limit=num_questions)

    if not questions:
        print("No questions loaded. Check the questions file path.")
        return

    print(f"Loaded {len(questions)} questions")

    # Process questions
    print(f"\nProcessing questions with Claude Code SDK...")
    results = await agent.process_questions(questions)

    # Save results
    agent.save_results(results, output_file)

    print("\nAgent processing complete!")


async def test_single_question():
    """Test the agent with a single question."""
    print("Testing with a single question")

    agent = FinanceBenchAgent()
    questions = agent.load_questions(limit=1)

    if not questions:
        print("No questions available for testing")
        return

    result = await agent.process_single_question(questions[0])
    print("\nTest Result:")
    print(f"Question ID: {result['question_id']}")
    print(f"Success: {'Yes' if not result.get('error') else 'No'}")
    if result.get('error'):
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    import sys

    # Command line interface
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            anyio.run(test_single_question)
        elif sys.argv[1] == "run":
            num_questions = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            anyio.run(run_agent(num_questions))
        else:
            print("Usage: python financebench_agent.py [test|run] [num_questions]")
    else:
        # Default: run with 3 questions
        anyio.run(run_agent(3))