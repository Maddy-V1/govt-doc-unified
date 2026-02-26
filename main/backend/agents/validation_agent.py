"""Validation Agent - Analyzes OCR output before vector DB storage"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def validate_ocr_result(ocr_result: Dict) -> Dict:
    """
    Validate OCR result and provide recommendations
    
    Args:
        ocr_result: OCR output dictionary with full_text, confidence, word_count, structured_fields
        
    Returns:
        Validation result with passed status, warnings, flags, and recommendation
    """
    try:
        confidence = ocr_result.get("confidence", 0.0)
        word_count = ocr_result.get("word_count", 0)
        structured_fields = ocr_result.get("structured_fields", {})
        
        warnings: List[str] = []
        flags = {
            "low_confidence": False,
            "very_low_word_count": False,
            "no_grand_total": False,
            "no_ddo_code": False,
            "balance_mismatch": False,
            "suspicious_round_numbers": False
        }
        
        # Check confidence
        if confidence < 0.4:
            flags["low_confidence"] = True
            warnings.append(f"Low OCR confidence: {confidence:.1%}")
        
        # Check word count
        if word_count < 10:
            flags["very_low_word_count"] = True
            warnings.append(f"Very low word count: {word_count} words")
        
        # Check structured fields (for Tesseract with Indian govt documents)
        if structured_fields:
            # Check for grand total
            if not structured_fields.get("grand_total"):
                flags["no_grand_total"] = True
                warnings.append("No grand total found in document")
            
            # Check for DDO code
            if not structured_fields.get("ddo_code"):
                flags["no_ddo_code"] = True
                warnings.append("No DDO code found in document")
            
            # Check balance validation
            balance_valid = structured_fields.get("balance_validation", {}).get("is_valid", True)
            if not balance_valid:
                flags["balance_mismatch"] = True
                warnings.append("Balance mismatch detected in document")
            
            # Check for suspicious round numbers
            grand_total = structured_fields.get("grand_total", "")
            # grand_total is a string like "1,82,68,500.00", need to parse it
            if grand_total:
                try:
                    # Remove commas and convert to float
                    total_value = float(grand_total.replace(",", ""))
                    if total_value > 0 and total_value % 10000 == 0:
                        flags["suspicious_round_numbers"] = True
                        warnings.append(f"Suspicious round number detected: {grand_total}")
                except (ValueError, AttributeError):
                    # If parsing fails, skip this check
                    pass
        
        # Determine if passed
        passed = confidence > 0.3 and word_count > 5
        
        # Determine recommendation
        if not passed:
            recommendation = "reject"
        elif confidence > 0.6 and not any([
            flags["balance_mismatch"],
            flags["very_low_word_count"]
        ]):
            recommendation = "store"
        else:
            recommendation = "review"
        
        confidence_ok = confidence > 0.4
        has_text = word_count > 10
        
        result = {
            "passed": passed,
            "confidence_ok": confidence_ok,
            "has_text": has_text,
            "warnings": warnings,
            "flags": flags,
            "structured_fields": structured_fields,
            "recommendation": recommendation
        }
        
        logger.info(f"Validation result: {recommendation} (confidence={confidence:.2f}, words={word_count})")
        
        return result
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        return {
            "passed": False,
            "confidence_ok": False,
            "has_text": False,
            "warnings": [f"Validation error: {str(e)}"],
            "flags": {},
            "structured_fields": {},
            "recommendation": "reject"
        }
