"""
backend/app/preprocessing/pp1_cleaning.py
"""
'''
STEP 1: TEXT CLEANING & ERROR CORRECTION
What happens:
Raw OCR text is cleaned to fix systematic errors and remove noise.
Specific actions:

Fix whitespace: Multiple spaces become single spaces, excessive newlines are normalized
Remove artifacts: Stray special characters, orphaned punctuation, zero-width characters
Fix OCR character confusions: "rn" → "m", "vv" → "w", "cl" → "d", "O" vs "0", "l" vs "1"
Spell correction: Fix misspelled words using dictionary lookup with edit distance ≤ 2
Confidence-based correction: Only apply changes when confidence is high, preserve original if uncertain

Why it matters:
OCR output is inherently noisy. Without cleaning, search breaks completely. Imagine searching for "payment" but OCR read it as "payrnent" (rn→m error) - you'd get zero results even though the document contains what you need. Cleaning ensures that when users search, they find relevant documents despite OCR imperfections.
Significance for the project:
This is the foundation of search accuracy. A single uncorrected character can make the difference between finding a critical invoice or missing it entirely during tax audits or legal discovery.
'''
import re
from spellchecker import SpellChecker
import string

class OCRTextCleaner:
    def __init__(self, confidence_threshold: float = 0.8):
        """
        Initializes the cleaner. 
        confidence_threshold: The score below which the OCR engine is considered 'uncertain'.
        """
        # Initialize spell checker once to save compute time during processing
        self.spell = SpellChecker()
        self.confidence_threshold = confidence_threshold

    def remove_whitespace(self, text: str) -> str:
        """Fix whitespace: Multiple spaces become single spaces, excessive newlines are normalized"""
        text = re.sub(r'\s+', ' ', text)  
        text = re.sub(r'\n+', '\n', text)  
        return text.strip()

    def remove_artifacts(self, text: str) -> str:
        """Remove artifacts: Stray special characters, orphaned punctuation, zero-width characters"""
        text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        return text

    def fix_ocr_confusions(self, word: str) -> str:
        """Fix OCR character confusions safely using context."""
        word = word.replace('rn', 'm')
        word = word.replace('vv', 'w')
        word = word.replace('cl', 'd')
        
        # More sophisticated handling: Only replace O/l with 0/1 if surrounded by digits
        word = re.sub(r'(?<=\d)O(?=\d)', '0', word)
        word = re.sub(r'(?<=\d)l(?=\d)', '1', word)
        return word

    def correct_spelling(self, word: str) -> str:
        """Spell correction: Fix misspelled words, safely handling attached punctuation."""
        
        # 1. Isolate the core word by stripping leading/trailing punctuation
        # Example: '"Algorthm."' becomes 'Algorthm'
        core_word = word.strip(string.punctuation)
        
        # 2. Skip if it's empty (e.g., it was just a comma ",") or contains numbers ("CS101")
        if not core_word or not core_word.isalpha():
            return word
            
        # 3. Skip if the core word is already in the dictionary
        if core_word in self.spell:
            return word
            
        # 4. Attempt the correction
        correction = self.spell.correction(core_word)
        
        # 5. Validate the correction exists and is different
        if correction and correction != core_word:
            # Simple check: only correct if the correction is reasonable
            # (pyspellchecker doesn't have a distance method, so we just trust it)
            return word.replace(core_word, correction, 1)
            
        return word  # Keep original if no valid correction is found

    def clean_text_pipeline(self, ocr_tokens: list) -> str:
        """
        The orchestrator.
        Expected input format: [{'text': 'Cl0se', 'conf': 0.45}, {'text': 'the', 'conf': 0.99}, ...]
        """
        processed_words = []
        
        for token in ocr_tokens:
            word = token.get('text', '')
            conf = token.get('conf', 1.0) # Default to 1.0 (100%) if missing

            # 1. Universal Cleaning (Safe to apply to everything)
            word = self.remove_artifacts(word)
            
            # 2. Confidence-Based Correction Gatekeeper
            # Logic: If the OCR engine was highly confident, trust it. 
            # If it was uncertain (below threshold), apply our heuristic fixes.
            if conf < self.confidence_threshold:
                
                # Apply structural fixes
                word = self.fix_ocr_confusions(word)
                
                # Apply spelling fixes (computationally heavier, do this last)
                word = self.correct_spelling(word)

            if word: # Ensure we don't append empty strings if artifacts removed everything
                processed_words.append(word)

        # 3. Final String Assembly and Whitespace Normalization
        final_string = ' '.join(processed_words)
        return self.remove_whitespace(final_string)