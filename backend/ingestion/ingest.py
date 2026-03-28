import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from docling.document_converter import DocumentConverter
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from sentence_transformers import SentenceTransformer

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────────
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "finbot"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DATA_DIR = Path("data")

# ── Access roles per collection ────────────────────────────────────────────────
ACCESS_MATRIX = {
    "general":     ["employee", "finance", "engineering", "marketing", "c_level"],
    "finance":     ["finance", "c_level"],
    "engineering": ["engineering", "c_level"],
    "marketing":   ["marketing", "c_level"],
}

# ── Initialize clients ─────────────────────────────────────────────────────────
print("Connecting to Qdrant...")
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
print("Loading embedding model...")
embedder = SentenceTransformer(EMBEDDING_MODEL)

def setup_collection():
    """Create Qdrant collection if it doesn't exist."""
    existing = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME in existing:
        print(f"Collection '{COLLECTION_NAME}' already exists, skipping creation.")
        return
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,  # all-MiniLM-L6-v2 produces 384-dim vectors
            distance=Distance.COSINE,
        ),
    )
    print(f"Collection '{COLLECTION_NAME}' created.")

def parse_document(file_path: Path) -> list[dict]:
    """Parse a document using Docling and return chunks with metadata."""
    print(f"  Parsing: {file_path.name}")
    converter = DocumentConverter()
    result = converter.convert(str(file_path))
    doc = result.document

    chunks = []
    current_section = "Introduction"

    for i, element in enumerate(doc.texts):
        text = element.text.strip()
        if not text or len(text) < 50:
            continue

        # Detect headings vs body text
        label = str(element.label).lower()
        if "head" in label or "title" in label:
            current_section = text
            chunk_type = "heading"
        elif "table" in label:
            chunk_type = "table"
        elif "code" in label:
            chunk_type = "code"
        else:
            chunk_type = "text"

        # Get page number if available
        page_number = 1
        if hasattr(element, "prov") and element.prov:
            page_number = element.prov[0].page_no

        chunks.append({
            "text": text,
            "section_title": current_section,
            "chunk_type": chunk_type,
            "page_number": page_number,
            "source_document": file_path.name,
        })

    return chunks

def ingest_collection(collection_folder: str):
    """Ingest all documents from a collection folder."""
    folder_path = DATA_DIR / collection_folder
    access_roles = ACCESS_MATRIX[collection_folder]

    if not folder_path.exists():
        print(f"Folder not found: {folder_path}")
        return

    files = list(folder_path.iterdir())
    if not files:
        print(f"No files found in {folder_path}")
        return

    print(f"\nIngesting collection: {collection_folder} ({len(files)} files)")

    points = []
    for file_path in files:
        if file_path.suffix.lower() not in [".pdf", ".docx", ".txt", ".md"]:
            print(f"  Skipping unsupported file: {file_path.name}")
            continue

        try:
            chunks = parse_document(file_path)
            print(f"  Found {len(chunks)} chunks in {file_path.name}")

            for chunk in chunks:
                # Generate embedding
                embedding = embedder.encode(chunk["text"]).tolist()

                # Build metadata payload
                payload = {
                    "text":              chunk["text"],
                    "source_document":   chunk["source_document"],
                    "collection":        collection_folder,
                    "access_roles":      access_roles,
                    "section_title":     chunk["section_title"],
                    "page_number":       chunk["page_number"],
                    "chunk_type":        chunk["chunk_type"],
                }

                points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload=payload,
                ))

        except Exception as e:
            print(f"  ERROR processing {file_path.name}: {e}")

    if points:
        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"  Stored {len(points)} chunks for '{collection_folder}'")

def main():
    print("=" * 50)
    print("FinBot Document Ingestion Pipeline")
    print("=" * 50)

    setup_collection()

    for collection in ["general", "finance", "engineering", "marketing"]:
        ingest_collection(collection)

    # Verify
    count = qdrant.count(collection_name=COLLECTION_NAME)
    print(f"\nDone! Total chunks stored in Qdrant: {count.count}")

if __name__ == "__main__":
    main()
