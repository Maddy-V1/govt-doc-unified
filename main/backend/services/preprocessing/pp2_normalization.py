"""
backend/app/preprocessing/pp2_tokenization.py
"""
'''
STEP 2: TEXT NORMALIZATION
What happens:
Text is standardized into consistent formats across all documents.
Specific actions:

Unicode normalization: Convert all characters to canonical form (NFC), replace smart quotes with regular quotes, normalize dashes
Number standardization: Remove commas from numbers (1,00,000 → 100000), handle both Indian and international formats
Date standardization: Convert all dates to ISO format (YYYY-MM-DD) regardless of input format (DD/MM/YYYY, MM-DD-YYYY, etc.)
Currency standardization: Rs. → INR, $ → USD, € → EUR with consistent spacing
Preserve original case: Keep original for display, create lowercase version for search

Why it matters:
Inconsistent formats fragment search results. If one document says "15/01/2024" and another says "2024-01-15", a date-based search might miss one. Similarly, "Rs. 1,00,000" and "Rs 100000" should be treated as the same amount. Normalization ensures "different ways of saying the same thing" are treated identically.
Significance for the project:
Enables reliable filtering and sorting. Users can search "invoices from January 2024" and get ALL January invoices regardless of how dates were originally written. Financial calculations (sum of all payments) work correctly only with normalized numbers.'''

import unicodedata
import re
from dateutil import parser

class TextNormalizer:

    def __init__(self):
        # 1. Define your global mapping (ISO 4217 format)
        self.CURRENCY_MAP = {
            '$': 'USD', 'US$': 'USD',
            '€': 'EUR', 
            '£': 'GBP', 
            '¥': 'JPY', 
            '₹': 'INR', 'Rs': 'INR', 'Rs.': 'INR', 'INR': 'INR',
            'A$': 'AUD', 
            'C$': 'CAD', 
            'Fr': 'CHF', 'CHF': 'CHF',
            'R$': 'BRL',
            # ... add as many as you need here
        }
        
        # 2. Compile the regex ONCE when the class is initialized.
        # CRITICAL STEP: Sort keys by length descending. 
        # This ensures 'US$' is matched before '$', and 'Rs.' before 'Rs'.
        sorted_symbols = sorted(self.CURRENCY_MAP.keys(), key=len, reverse=True)
        
        # Escape the symbols so things like '$' or '.' don't break the regex
        escaped_symbols = [re.escape(sym) for sym in sorted_symbols]
        
        # Build a regex pattern like: (US\$|Rs\.|Rs|A\$|C\$|\$|€|£)\s*
        # The \s* handles any trailing spaces automatically
        self.currency_pattern = re.compile(
            r'\b(' + '|'.join(escaped_symbols) + r')\b|\b(' + '|'.join(escaped_symbols) + r')(?=\d)|(?<=\d)(' + '|'.join(escaped_symbols) + r')\b|(' + '|'.join(escaped_symbols) + r')\s*', 
            re.IGNORECASE
        )
        
        # A simpler, more robust pattern if symbols are always followed/preceded by numbers or spaces:
        self.simple_currency_pattern = re.compile(r'(' + '|'.join(escaped_symbols) + r')\s*', re.IGNORECASE)

    def normalize_unicode(self, text: str) -> str:
        """Unicode normalization: Convert to canonical form (NFC), fix quotes and dashes"""
        text = unicodedata.normalize('NFC', text)
        text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
        text = text.replace('—', '-').replace('–', '-')
        return text

    def standardize_numbers(self, text: str) -> str:
        """Number standardization: Removes commas cleanly for both Indian and Int'l formats"""
        # Looks for any comma strictly surrounded by digits and removes it
        text = re.sub(r'(?<=\d),(?=\d)', '', text) 
        return text

    def standardize_dates(self, text: str) -> str:
        """Date standardization: ISO format (YYYY-MM-DD), handling 2 or 4 digit years"""
        # Expanded to catch 2-digit years as well (e.g., 15/01/24)
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        
        def replace_date(match):
            try:
                # dayfirst=True ensures 05/04/2024 is parsed as April 5th, not May 4th
                parsed_date = parser.parse(match.group(0), dayfirst=True)
                return parsed_date.strftime('%Y-%m-%d')
            except parser.ParserError:
                return match.group(0)  
                
        text = re.sub(date_pattern, replace_date, text)
        return text

    def standardize_currency(self, text: str) -> str:
        """Currency standardization using a dynamic hash map lookup"""
        
        # This function acts as the replacement logic for re.sub
        def replace_match(match):
            # Get the exact symbol that was matched, strip any whitespace, and convert to title case
            # to match the dictionary keys (e.g. 'rs.' becomes 'Rs.')
            matched_symbol = match.group(1).strip()
            
            # Since we used re.IGNORECASE, we need to find the correct key case-insensitively
            # (In production, storing keys in lowercase is usually safer, but this works too)
            for key in self.CURRENCY_MAP.keys():
                if key.lower() == matched_symbol.lower():
                    return f"{self.CURRENCY_MAP[key]} "
            
            # Fallback (should theoretically never hit if regex works)
            return match.group(0)

        # Apply the single-pass regex replacement
        return self.simple_currency_pattern.sub(replace_match, text)

    def process(self, text: str) -> dict:
        """
        Executes the full normalization pipeline and fulfills the 
        'Keep original for display, lowercase for search' requirement.
        """
        normalized = self.normalize_unicode(text)
        normalized = self.standardize_numbers(normalized)
        normalized = self.standardize_dates(normalized)
        normalized = self.standardize_currency(normalized)
        
        return {
            "display_text": normalized,
            "search_text": normalized.lower()
        }

# --- Example Usage ---
if __name__ == "__main__":
    normalizer = TextNormalizer()
    
    # Test string with all the edge cases
    raw_ocr_text = "The amount is rs. 1,00,000 for the invoice dated 15/04/24. Also paid $ 5,000 on 04-05-2024."
    
    result = normalizer.process(raw_ocr_text)
    print(f"Display: {result['display_text']}")
    print(f"Search:  {result['search_text']}")
    
    # Output:
    # Display: The amount is INR 100000 for the invoice dated 2024-04-15. Also paid USD 5000 on 2024-05-04.
    # Search:  the amount is inr 100000 for the invoice dated 2024-04-15. also paid usd 5000 on 2024-05-04.
