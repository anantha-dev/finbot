import os
import sys
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def expand_query(query: str) -> str:
    """
    Rewrite the user query to better match document wording
    for improved retrieval.
    """
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": f"""Rewrite this query to better match HR/Finance/Engineering 
document wording. Return ONLY the rewritten query, nothing else.

Original query: {query}

Rewritten query:"""
            }
        ],
    )
    expanded = message.content[0].text.strip()
    return expanded


if __name__ == "__main__":
    test_queries = [
        "What is the annual leave policy?",
        "What is the annual revenue for FY2024?",
        "How do I fix high API latency?",
    ]
    for q in test_queries:
        expanded = expand_query(q)
        print(f"Original:  {q}")
        print(f"Expanded:  {expanded}")
        print()
