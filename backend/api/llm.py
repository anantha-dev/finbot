import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

# ── Initialize Anthropic client ────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL  = "claude-opus-4-6"

def build_prompt(query: str, chunks: list[dict], user_role: str) -> str:
    """Build a prompt from retrieved chunks."""
    context_parts = []
    for i, chunk in enumerate(chunks):
        context_parts.append(
            f"[Source {i+1}]: {chunk['source_document']} "
            f"(Page {chunk['page_number']}, Section: {chunk['section_title']})\n"
            f"{chunk['text']}"
        )
    context = "\n\n".join(context_parts)

    return f"""You are FinBot, an internal AI assistant for FinSolve Technologies.
You answer questions based ONLY on the provided context documents.
The user has the role: {user_role}

RULES:
1. Only use information from the provided context below.
2. Always cite your sources using the format: (Source: filename, Page X)
3. If the answer is not in the context, say "I could not find this information in your accessible documents."
4. Never reveal information from documents the user is not authorized to access.
5. Be concise and professional.

CONTEXT:
{context}

QUESTION: {query}

ANSWER:"""


def generate_response(query: str, chunks: list[dict], user_role: str) -> dict:
    """Generate a response using Claude based on retrieved chunks."""

    if not chunks:
        return {
            "response": "I could not find any relevant information in your "
                        "accessible documents for this query.",
            "model":    MODEL,
            "chunks":   [],
        }

    prompt = build_prompt(query, chunks, user_role)

    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    response_text = message.content[0].text

    return {
        "response": response_text,
        "model":    MODEL,
        "chunks":   chunks,
    }


def test_llm():
    """Test the LLM with a sample query and fake chunks."""
    print("=" * 50)
    print("Testing LLM Response Layer")
    print("=" * 50)

    # Fake chunks simulating what retriever would return
    sample_chunks = [
        {
            "text":            "Employees are entitled to 20 days of annual leave per calendar year. Sick leave is capped at 10 days per year with a valid medical certificate.",
            "source_document": "employee_handbook.pdf",
            "section_title":   "Leave Policy",
            "page_number":     12,
            "chunk_type":      "text",
            "score":           0.92,
        },
        {
            "text":            "Maternity leave is 26 weeks as per statutory guidelines. Paternity leave is 2 weeks.",
            "source_document": "employee_handbook.pdf",
            "section_title":   "Leave Policy",
            "page_number":     12,
            "chunk_type":      "text",
            "score":           0.88,
        },
    ]

    query    = "How many days of annual leave do I get?"
    user_role = "employee"

    print(f"\nQuery: {query}")
    print(f"Role:  {user_role}")
    print("\nGenerating response...")

    result = generate_response(query, sample_chunks, user_role)

    print(f"\nModel: {result['model']}")
    print(f"\nResponse:\n{result['response']}")


if __name__ == "__main__":
    test_llm()
