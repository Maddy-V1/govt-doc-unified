"""
backend/app/preprocessing/pp4_stopwords.py
"""
'''
STEP 4: TEXT CHUNKING
What happens:
Long documents are split into smaller, semantically coherent pieces.
Specific actions:

Split at sentence boundaries: Never cut mid-sentence
Target chunk size: 300-500 words per chunk
Overlapping chunks: 50-word overlap between consecutive chunks
Preserve context: Each chunk includes surrounding context from overlap
Attach metadata: Every chunk carries document-level metadata (date, type, source)

Why it matters:
Embedding models work best on medium-length text. They can't effectively encode entire 50-page documents into a single vector - too much information gets lost. But individual sentences lack context. The sweet spot is 300-500 word chunks that contain complete thoughts.
Overlap prevents information loss. If a critical sentence appears at the boundary between two chunks, overlap ensures it appears fully in at least one chunk. Otherwise, partial matches at chunk boundaries get missed.
Significance for the project:
Enables precise result matching. When users search, they get the specific paragraph/section that answers their query, not the entire 30-page contract. Each result shows relevant context, making it easy to verify relevance without opening the full document.
Also enables scalability - a 100-page document becomes 200 searchable chunks rather than one giant unsearchable blob.
'''

import re

class TextChunker:
    def __init__(self, target_word_size: int = 400, overlap_word_size: int = 50):
        """
        Initializes the chunker with target and overlap sizes.
        Optimal sizes for models like OpenAI's text-embedding-ada-002 or BERT 
        usually sit between 300-500 words.
        """
        self.target_size = target_word_size
        self.overlap_size = overlap_word_size

    def _split_into_sentences(self, text: str) -> list:
        """
        Splits text into sentences safely.
        Looks for standard punctuation (.!?) followed by a space and a capital letter.
        """
        # This regex avoids splitting on floating point numbers (e.g., 3.14)
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_document(self, text: str, metadata: dict) -> list:
        """
        Splits the document into overlapping chunks while preserving sentence boundaries,
        and attaches the parent document's metadata to every chunk.
        """
        sentences = self._split_into_sentences(text)
        chunks = []
        
        current_chunk_sentences = []
        current_word_count = 0
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sentence_words = sentence.split()
            word_count = len(sentence_words)

            # Edge Case: A single sentence is massive (larger than the target size itself)
            if not current_chunk_sentences and word_count >= self.target_size:
                chunks.append({
                    "chunk_text": sentence,
                    "metadata": metadata.copy(),
                    "chunk_size": word_count
                })
                i += 1
                continue

            # Check if adding this sentence pushes us over the target limit
            if current_word_count + word_count > self.target_size and current_chunk_sentences:
                # 1. Finalize and save the current chunk
                chunks.append({
                    "chunk_text": " ".join(current_chunk_sentences),
                    "metadata": metadata.copy(),
                    "chunk_size": current_word_count
                })
                
                # 2. Calculate the Overlap for the next chunk
                overlap_sentences = []
                overlap_word_count = 0
                
                # Backtrack through the current chunk's sentences from end to start
                for sent in reversed(current_chunk_sentences):
                    sent_len = len(sent.split())
                    if overlap_word_count + sent_len <= self.overlap_size:
                        overlap_sentences.insert(0, sent)
                        overlap_word_count += sent_len
                    else:
                        # Grab one final sentence to ensure we hit or slightly exceed the overlap target
                        overlap_sentences.insert(0, sent)
                        overlap_word_count += sent_len
                        break
                
                # 3. Reset the current chunk to START with the overlapping sentences
                current_chunk_sentences = overlap_sentences
                current_word_count = overlap_word_count
                
                # Notice we DO NOT increment 'i' here, because the current sentence 
                # that triggered the split still needs to be evaluated in the next loop iteration.
            else:
                # Safe to add the sentence to the current chunk
                current_chunk_sentences.append(sentence)
                current_word_count += word_count
                i += 1

        # Don't forget to append the final, potentially smaller chunk at the end of the document
        if current_chunk_sentences:
            chunks.append({
                "chunk_text": " ".join(current_chunk_sentences),
                "metadata": metadata.copy(),
                "chunk_size": current_word_count
            })

        return chunks

# --- Example Usage ---
if __name__ == "__main__":
    chunker = TextChunker(target_word_size=50, overlap_word_size=15) # Smaller sizes for testing
    
    # Let's assume this is the text and metadata output from Step 3
    sample_text = (
        "This is the first sentence of the document. It contains some basic information. "
        "Moving on, this is the third sentence, which adds a bit more context. "
        "Here is the fourth sentence talking about invoices and payments. "
        "Finally, the fifth sentence wraps up the first paragraph. "
        "Starting a new thought here in the sixth sentence. "
        "The seventh sentence is critical for understanding the contract terms."
    )
    
    sample_metadata = {
        "document_type": "contract",
        "dates": ["2024-04-15"],
        "entities": {"ORG": ["TechCorp Solutions"]}
    }
    
    resulting_chunks = chunker.chunk_document(sample_text, sample_metadata)
    
    for idx, chunk in enumerate(resulting_chunks):
        print(f"\n--- Chunk {idx + 1} (Words: {chunk['chunk_size']}) ---")
        print(f"Text: {chunk['chunk_text']}")
        # print(f"Meta: {chunk['metadata']}")
