"""
backend/app/preprocessing/pp3_normalization.py
"""
'''
STEP 3: METADATA EXTRACTION
What happens:
Structured information is automatically extracted from unstructured text.
Specific actions:

Named Entity Recognition (NER): Identify persons, organizations, locations, dates, monetary amounts
Pattern matching: Extract dates using regex, monetary values, invoice numbers, IDs
Document classification: Classify as invoice, contract, receipt, letter, etc. based on keyword presence
Field detection: Find key-value pairs like "Total Amount: $5000", "Contractor: ABC Corp"
Aggregate statistics: Calculate total amounts, identify earliest/latest dates in document

Why it matters:
Metadata enables advanced filtering that pure text search cannot provide. Users don't just want to search text - they want to find "all invoices over $10,000 from Q1 2024 mentioning ABC Corp". Without metadata extraction, this is impossible. The text is there, but it's not queryable as structured data.
Significance for the project:
Transforms search into a database query. Instead of just finding documents containing words, users can filter by:

Amount ranges (invoices > $5000)
Date ranges (contracts signed in 2024)
Vendors/contractors (all documents from ABC Corp)
Document types (show me only receipts)

This is what makes the system professionally useful versus just a toy demo.'''


import re
import spacy
from collections import defaultdict

class MetadataExtractor:
    def __init__(self):
        """Initialize the NLP model for entity extraction."""
        try:
            # Load the pre-trained English statistical model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise OSError("SpaCy model not found. Run: python -m spacy download en_core_web_sm")

    def extract_metadata(self, text: str) -> dict:
        """Orchestrates the extraction of all metadata fields."""
        metadata = {
            'entities': self.extract_entities(text),
            'dates': self.extract_dates(text),
            'amounts': self.extract_amounts(text),
            'document_type': self.classify_document(text),
            'total_value': self.calculate_total(text) # Added an aggregate stat!
        }
        return metadata

    def extract_entities(self, text: str) -> dict:
        """
        Named Entity Recognition (NER) using SpaCy.
        Returns a dictionary grouping entities by type.
        """
        doc = self.nlp(text)
        
        # Using a set to prevent duplicate entities
        entities = defaultdict(set)
        
        for ent in doc.ents:
            # We filter for specific useful labels: 
            # ORG (Companies), PERSON (People), GPE (Locations)
            if ent.label_ in ['ORG', 'PERSON', 'GPE']:
                entities[ent.label_].add(ent.text)
                
        # Convert sets back to lists for JSON serialization later
        return {k: list(v) for k, v in entities.items()}

    def extract_dates(self, text: str) -> list:
        """Dates are extracted using the normalized format from Step 2."""
        return re.findall(r'\b\d{4}-\d{2}-\d{2}\b', text)

    def extract_amounts(self, text: str) -> list:
        """
        Extracts monetary amounts. Since Step 2 normalized currencies, 
        we look for the 3-letter ISO code followed by numbers.
        """
        # Matches "INR 5000", "USD 100.50", "EUR 10,000" (if commas survived)
        pattern = r'\b[A-Z]{3}\s\d+(?:\.\d{1,2})?\b'
        return re.findall(pattern, text)

    def calculate_total(self, text: str) -> float:
        """Aggregate statistic: Finds the highest numerical value associated with currency."""
        amounts = self.extract_amounts(text)
        if not amounts:
            return 0.0
            
        numeric_values = []
        for amount in amounts:
            # Strip the currency code and convert to float
            num_str = re.sub(r'[A-Z]{3}\s', '', amount)
            try:
                numeric_values.append(float(num_str))
            except ValueError:
                continue
                
        # The highest currency value on an invoice/receipt is usually the "Total"
        return max(numeric_values) if numeric_values else 0.0

    def classify_document(self, text: str) -> str:
        """
        Document classification using a keyword heuristic scoring system.
        For a production AIML system, you might replace this with a trained text classifier (like BERT or Naive Bayes).
        """
        text_lower = text.lower()
        
        # Keyword dictionaries for different document types
        categories = {
            "invoice": ["invoice", "bill to", "due date", "tax", "subtotal", "remittance"],
            "receipt": ["receipt", "paid", "transaction id", "cashier", "card ending in"],
            "contract": ["agreement", "contract", "party of the first part", "signed", "terms and conditions"],
            "letter": ["sincerely", "dear", "regards", "to whom it may concern"]
        }
        
        scores = {}
        for category, keywords in categories.items():
            # Count how many times the keywords appear in the text
            scores[category] = sum(text_lower.count(kw) for kw in keywords)
            
        # Find the category with the highest score
        best_match = max(scores, key=scores.get)
        
        # Only return the match if it actually found keywords, otherwise default to "unknown"
        if scores[best_match] > 0:
            return best_match
            
        return "unknown"

# --- Example Usage ---
if __name__ == "__main__":
    extractor = MetadataExtractor()
    
    # Text that has already passed through your TextNormalizer
    normalized_text = """
    INVOICE
    Date: 2024-04-15
    Bill To: TechCorp Solutions
    Attn: Rahul Sharma
    Location: New Delhi
    
    Services Rendered for AIML Development: INR 50000.00
    Server Costs: INR 2500.50
    Total Amount Due: INR 52500.50
    """
    
    metadata = extractor.extract_metadata(normalized_text)
    
    import json
    print(json.dumps(metadata, indent=2))