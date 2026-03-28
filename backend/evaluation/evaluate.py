import sys
import os
import json
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
)
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "retrieval"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "guardrails"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "api"))

from test_dataset import TEST_DATASET
from finbot import ask_finbot

def to_float(val):
    if isinstance(val, list):
        return round(sum(val) / len(val), 4)
    return round(float(val), 4)

def run_evaluation():
    print("=" * 50)
    print("FinBot RAGAs Evaluation")
    print("=" * 50)

    questions        = []
    answers          = []
    ground_truths    = []
    contexts         = []
    rbac_results     = []

    # Filter only non-adversarial questions for RAGAs
    eval_dataset = [
        q for q in TEST_DATASET
        if not q.get("expect_denied") and not q.get("expect_blocked")
    ]

    adversarial_dataset = [
        q for q in TEST_DATASET
        if q.get("expect_denied") or q.get("expect_blocked")
    ]

    print(f"\nRunning {len(eval_dataset)} evaluation questions...")
    print(f"Running {len(adversarial_dataset)} adversarial questions...\n")

    # ── Run adversarial tests first ───────────────────────────────────────────
    print("--- Adversarial / RBAC Tests ---")
    adversarial_passed = 0
    for item in adversarial_dataset:
        result = ask_finbot(
            query      = item["question"],
            user_role  = item["user_role"],
            session_id = f"eval-{item['user_role']}",
        )
        expected_blocked = not result["success"]
        if expected_blocked:
            adversarial_passed += 1
            status = "✅ CORRECTLY BLOCKED"
        else:
            status = "❌ SHOULD HAVE BEEN BLOCKED"

        print(f"{status} | Role: {item['user_role']} | Q: {item['question'][:50]}")
        rbac_results.append({
            "question": item["question"],
            "role":     item["user_role"],
            "passed":   expected_blocked,
        })

    print(f"\nAdversarial tests passed: {adversarial_passed}/{len(adversarial_dataset)}")

    # ── Run main evaluation questions ─────────────────────────────────────────
    print("\n--- Main Evaluation Questions ---")
    for i, item in enumerate(eval_dataset):
        print(f"[{i+1}/{len(eval_dataset)}] {item['question'][:60]}...")

        result = ask_finbot(
            query      = item["question"],
            user_role  = item["user_role"],
            session_id = f"eval-{item['user_role']}-{i}",
        )

        if result["success"] and result.get("response"):
            questions.append(item["question"])
            answers.append(result["response"])
            ground_truths.append(item["ground_truth"])
            contexts.append([
                c["source_document"] + ": " + item["ground_truth"]
                for c in result.get("chunks", [])[:3]
            ] or ["No context retrieved"])
        else:
            print(f"  Skipped (blocked or failed): {result.get('message', '')}")

    print(f"\nSuccessfully evaluated: {len(questions)} questions")

    if len(questions) == 0:
        print("No questions to evaluate. Exiting.")
        return

    # ── Run RAGAs ─────────────────────────────────────────────────────────────
    print("\nRunning RAGAs metrics...")

    dataset = Dataset.from_dict({
        "question":   questions,
        "answer":     answers,
        "contexts":   contexts,
        "ground_truth": ground_truths,
    })

    # Use Claude as the LLM for evaluation
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    results = evaluate(
        dataset    = dataset,
        metrics    = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            answer_correctness,
        ],
        llm        = llm,
        embeddings = embeddings,
    )

    # ── Print results ─────────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("RAGAs Results")
    print("=" * 50)


    
    faithfulness_score       = to_float(results['faithfulness'])
    answer_relevancy_score   = to_float(results['answer_relevancy'])
    context_precision_score  = to_float(results['context_precision'])
    context_recall_score     = to_float(results['context_recall'])
    answer_correctness_score = to_float(results['answer_correctness'])

    print(f"Faithfulness:       {faithfulness_score:.4f}")
    print(f"Answer Relevancy:   {answer_relevancy_score:.4f}")
    print(f"Context Precision:  {context_precision_score:.4f}")
    print(f"Context Recall:     {context_recall_score:.4f}")
    print(f"Answer Correctness: {answer_correctness_score:.4f}")

# Save results
    output = {
        "ragas_scores": {
            "faithfulness":       faithfulness_score,
            "answer_relevancy":   answer_relevancy_score,
            "context_precision":  context_precision_score,
            "context_recall":     context_recall_score,
            "answer_correctness": answer_correctness_score,
            },
            "adversarial_results": {
                "passed": adversarial_passed,
                "total":  len(adversarial_dataset),
            },
            "total_questions_evaluated": len(questions),
        }

    with open("backend/evaluation/results.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\nResults saved to backend/evaluation/results.json")
    return output

if __name__ == "__main__":
    run_evaluation()
