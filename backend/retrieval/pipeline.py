import logging
import sys
import os

sys.path.append(os.path.dirname(__file__))

from retriever import retrieve
from router import route_query
from query_expander import expand_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_pipeline(query: str, user_role: str) -> dict:
    """
    Full retrieval pipeline:
    1. Expand query for better retrieval
    2. Route the query to the correct collection
    3. Check role-based access
    4. Retrieve relevant chunks filtered by collection
    """
    logger.info(f"Query: '{query}' | Role: '{user_role}'")

    # Step 1 — Expand query
    expanded_query = expand_query(query)
    logger.info(f"Expanded query: '{expanded_query}'")

    # Step 2 — Route the query
    route_result = route_query(expanded_query, user_role)

    # Step 3 — Check access
    if not route_result["allowed"]:
        return {
            "success":        False,
            "message":        route_result["message"],
            "detected_route": route_result["detected_route"],
            "user_role":      user_role,
            "chunks":         [],
        }

    # Step 4 — Retrieve chunks filtered by BOTH role AND collection
    collections = route_result["collections"]
    all_chunks  = []

    for collection in collections:
        chunks = retrieve(
            query      = expanded_query,
            user_role  = user_role,
            collection = collection,
        )
        all_chunks.extend(chunks)

    # Sort by score and take top 5
    all_chunks = sorted(all_chunks, key=lambda x: x["score"], reverse=True)[:5]

    return {
        "success":        True,
        "message":        "OK",
        "detected_route": route_result["detected_route"],
        "collections":    collections,
        "user_role":      user_role,
        "expanded_query": expanded_query,
        "chunks":         all_chunks,
    }
