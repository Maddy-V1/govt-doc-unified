"""
backend/app/services/embedding_service.py
"""

'''
STEP 5: EMBEDDING GENERATION
What happens:
Text chunks are converted into high-dimensional vectors that capture semantic meaning.
Specific actions:

Load pre-trained model: Use Sentence-BERT (all-MiniLM-L6-v2) - 384 dimensions
Batch processing: Convert all chunks in batches for efficiency
Vector creation: Each chunk becomes a 384-dimensional floating-point vector
Semantic encoding: Similar meanings = similar vectors, regardless of exact words
Store vectors: Attach embedding to each chunk object

Why it matters:
This is what makes semantic search possible. Keyword search only matches exact words. Embeddings capture meaning. When you search "payment issues", embedding search also finds chunks containing "outstanding dues", "delayed transactions", "overdue invoices" - different words, same meaning.
The magic: Two sentences with zero overlapping words can have similar vectors if they mean similar things. The model learned this from millions of examples during training.
Significance for the project:
This is the difference between Google-level search and Ctrl+F. Users can:

Search concepts, not just keywords
Find synonyms automatically
Get relevant results even with typos or different phrasing
Discover related documents they didn't know to search for

Example: User searches "late payment penalties" → System returns documents containing "interest on overdue amounts", "charges for delayed settlement" even though the exact phrase "late payment penalties" doesn't appear.'''

from sentence_transformers import SentenceTransformer
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initializes the embedding model.
        'all-MiniLM-L6-v2' is heavily optimized for semantic search.
        It maps sentences to a 384-dimensional dense vector space.
        """
        logger.info(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        
        # Verify the dimensions (should be 384 for this specific model)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Vector dimension: {self.embedding_dimension}")

    def generate_embeddings(self, chunks: List[Dict], batch_size: int = 32) -> List[Dict]:
        """
        Takes a list of chunk dictionaries, extracts the text, 
        generates vectors in batches, and attaches the vectors back to the chunks.
        """
        if not chunks:
            return []

        # 1. Isolate the text strings into a flat list for the model
        text_batch = [chunk['chunk_text'] for chunk in chunks]
        
        # 2. Encode the text into vectors
        # batch_size ensures we don't run out of RAM/VRAM on large documents
        # normalize_embeddings=True applies L2 normalization, making cosine similarity much faster later
        logger.info(f"Generating embeddings for {len(text_batch)} chunks...")
        embeddings = self.model.encode(
            text_batch, 
            batch_size=batch_size, 
            show_progress_bar=False,  # Don't show progress bar in production
            normalize_embeddings=True 
        )
        
        # 3. Attach the generated vectors back to the original chunk objects
        for i, chunk in enumerate(chunks):
            # Convert the NumPy array to a standard Python list.
            # This is critical because Vector Databases (Pinecone, ChromaDB, etc.) 
            # and JSON serializers cannot natively read NumPy arrays.
            chunk['embedding'] = embeddings[i].tolist()
            
        return chunks

# --- Example Usage ---
if __name__ == "__main__":
    generator = EmbeddingGenerator()
    
    # Simulating the output from Step 4 (Text Chunking)
    sample_chunks = [
        {
            "chunk_text": "The contractor shall pay a 5% penalty for any invoices settled after the 30-day net period.",
            "metadata": {"document_type": "contract", "dates": ["2024-01-01"]},
            "chunk_size": 17
        },
        {
            "chunk_text": "All equipment must be returned in working condition.",
            "metadata": {"document_type": "contract", "dates": ["2024-01-01"]},
            "chunk_size": 8
        }
    ]
    
    # Process the chunks
    embedded_chunks = generator.generate_embeddings(sample_chunks)
    
    # Verify the output
    for idx, chunk in enumerate(embedded_chunks):
        print(f"\n--- Chunk {idx + 1} ---")
        print(f"Text: {chunk['chunk_text']}")
        print(f"Embedding generated: True")
        print(f"Vector length: {len(chunk['embedding'])}")
        print(f"First 5 dimensions: {chunk['embedding'][:5]}...")
