import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────────
QDRANT_HOST      = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT      = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME  = "finbot"
EMBEDDING_MODEL  = "all-MiniLM-L6-v2"
TOP_K            = 5  # number of chunks to retrieve

# ── Initialize clients ─────────────────────────────────────────────────────────
qdrant   = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedder = SentenceTransformer(EMBEDDING_MODEL)

def retrieve(query: str, user_role: str, collection: str = None) -> list[dict]:
    """
    Retrieve relevant chunks for a query, filtered by user role and collection.
    RBAC is enforced at the Qdrant query level.
    """
    # Step 1 — Embed the query
    query_vector = embedder.encode(query).tolist()

    # Step 2 — Build RBAC filter conditions
    filter_conditions = [
        FieldCondition(
            key="access_roles",
            match=MatchValue(value=user_role),
        )
    ]

    # Step 3 — Add collection filter if specified
    if collection:
        filter_conditions.append(
            FieldCondition(
                key="collection",
                match=MatchValue(value=collection),
            )
        )

    rbac_filter = Filter(must=filter_conditions)

    # Step 4 — Query Qdrant
    response = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=rbac_filter,
        limit=TOP_K,
        with_payload=True,
    )

    # Step 5 — Format results
    chunks = []
    for hit in response.points:
        chunks.append({
            "text":            hit.payload.get("text", ""),
            "source_document": hit.payload.get("source_document", ""),
            "collection":      hit.payload.get("collection", ""),
            "section_title":   hit.payload.get("section_title", ""),
            "page_number":     hit.payload.get("page_number", 1),
            "chunk_type":      hit.payload.get("chunk_type", "text"),
            "score":           round(hit.score, 4),
        })

    return chunks

def test_rbac():
    """
    Test that RBAC is working correctly.
    An engineering user should NOT see finance chunks.
    """
    print("=" * 50)
    print("Testing RBAC Enforcement")
    print("=" * 50)

    query = "What is the company revenue and financial projections?"

    for role in ["employee", "finance", "engineering", "marketing", "c_level"]:
        results = retrieve(query, role)
        collections_returned = list(set(r["collection"] for r in results))
        print(f"\nRole: {role}")
        print(f"  Collections returned: {collections_returned}")
        print(f"  Chunks returned: {len(results)}")
        if results:
            print(f"  Top result: {results[0]['source_document']} "
                  f"(score: {results[0]['score']})")


if __name__ == "__main__":
    test_rbac()
