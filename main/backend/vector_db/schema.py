"""
backend/app/vector_db/schema.py
Defines the metadata schema stored alongside FAISS vectors.
"""

# Each chunk stored in the vector DB carries this metadata structure.
# The actual FAISS index only holds float32 vectors; metadata lives in
# a parallel list serialised with pickle.

CHUNK_SCHEMA = {
    "chunk_id": str,        # unique id: "<document_id>_chunk_<index>"
    "document_id": str,     # parent document UUID
    "chunk_index": int,     # 0-based position within the document
    "chunk_text": str,      # the raw chunk text
    "chunk_size": int,      # word count
    "metadata": dict,       # free-form dict (filename, pages, entities, …)
}
