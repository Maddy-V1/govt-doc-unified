"""
Text Postprocessing Module
Text cleaning, normalization, and quality improvement for OCR output.
Enhanced for Phase 2: Structured field extraction for government documents.
"""

import re
from typing import List, Set, Optional, Dict, Any

from ocr1.config import (
    REMOVE_DUPLICATE_LINES,
    NORMALIZE_WHITESPACE,
    REMOVE_NON_PRINTABLE
)
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text from OCR.

    Cleaning steps:
    1. Remove non-printable characters
    2. Normalize whitespace
    3. Fix common OCR errors
    4. Remove duplicate lines
    5. Normalize currency symbols
    6. Fix encoding issues
    """
    if not text:
        return ""

    logger.debug("Starting text postprocessing")
    original_length = len(text)

    if REMOVE_NON_PRINTABLE:
        text = _remove_non_printable_chars(text)

    text = _fix_common_ocr_errors(text)

    if NORMALIZE_WHITESPACE:
        text = _normalize_whitespace(text)

    text = _normalize_currency_symbols(text)

    if REMOVE_DUPLICATE_LINES:
        text = _remove_duplicate_lines(text)

    text = _fix_line_breaks(text)

    cleaned_length = len(text)
    reduction_pct = ((original_length - cleaned_length) / original_length * 100) if original_length > 0 else 0
    logger.debug(f"Text cleaning: {original_length} → {cleaned_length} chars ({reduction_pct:.1f}% reduction)")

    return text.strip()


def _remove_non_printable_chars(text: str) -> str:
    return ''.join(c for c in text if c.isprintable() or c in '\n\t\r')


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\t+', '\t', text)
    text = re.sub(r'\n\n+', '\n\n', text)
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines)


def _fix_common_ocr_errors(text: str) -> str:
    """
    Fix common OCR recognition errors.
    Enhanced for Hindi + English government documents (PWD, finance).
    """
    # Fix O → 0 in numeric/date contexts
    text = re.sub(r'([0-3]?)O([0-9])/([0-1]?)O([0-9])/2O([0-9]{2})',
                  r'\g<1>0\2/\g<3>0\4/20\5', text)
    text = re.sub(r'\bO(\d{9})\b', r'0\1', text)
    text = re.sub(r'\b(\d+)O(\d+)\b', r'\g<1>0\2', text)

    # Fix Head-of-Account codes
    text = re.sub(r'(\d+)/([A-Z]?)O(\d+)',
                  lambda m: m.group(1) + '/' + m.group(2) + '0' + m.group(3), text)

    # Fix bill/account numbers
    text = re.sub(r'([A-Z]{2,})-O(\d+)', r'\1-0\2', text)

    # Remove Tesseract noise characters on their own
    text = re.sub(r'\s+[~^|\\]\s+', ' ', text)

    # Drop lines that are pure garbage (< 15% alphanumeric)
    clean_lines = []
    for line in text.split('\n'):
        alphanum_count = sum(1 for c in line if c.isalnum() or '\u0900' <= c <= '\u097F')
        total = len(line.strip())
        if total == 0 or alphanum_count / total >= 0.15:
            clean_lines.append(line)
    text = '\n'.join(clean_lines)

    # Fix amount formatting
    text = re.sub(r'(\d) \. (\d)', r'\1.\2', text)
    text = re.sub(r'(\d) , (\d{3})', r'\1,\2', text)

    # Common OCR word fixes (govt docs)
    fixes = {
        r'\bIhe\b': 'The', r'\bln\b': 'In', r'\b1he\b': 'the', r'\btne\b': 'the',
        r'\bBhopaI\b': 'Bhopal', r'\bDivlsion\b': 'Division',
        r'\bEngtneer\b': 'Engineer', r'\bExecutlve\b': 'Executive',
        r'\bExpenditare\b': 'Expenditure', r'\bExpenditur\b': 'Expenditure',
        r'\bAcconts\b': 'Accounts',
    }
    for pattern, replacement in fixes.items():
        text = re.sub(pattern, replacement, text)

    return text


def _normalize_currency_symbols(text: str) -> str:
    text = re.sub(r'\bRs\.?\s*', '₹', text, flags=re.IGNORECASE)
    text = re.sub(r'\bINR\s*', '₹', text)
    text = re.sub(r'₹(\d)', r'₹ \1', text)
    return text


def _remove_duplicate_lines(text: str) -> str:
    lines = text.split('\n')
    unique_lines, seen = [], set()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            unique_lines.append(line)
        elif stripped not in seen:
            unique_lines.append(line)
            seen.add(stripped)
    return '\n'.join(unique_lines)


def _fix_line_breaks(text: str) -> str:
    text = re.sub(r'-\n([a-z])', r'\1', text)
    text = re.sub(r'([a-z])\n([a-z])', r'\1 \2', text)
    return text


# ══════════════════════════════════════════════════════════════════════════════
#  PHASE 2 — STRUCTURED FIELD EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def extract_key_information(text: str) -> Dict[str, Any]:
    """
    Phase 2: Extract structured fields from OCR text of Indian government
    financial documents (PWD bills, monthly accounts, schedules, etc.)

    Returns a rich structured dict with all detected fields.
    """
    if not text:
        return _empty_extraction()

    logger.info("Phase 2: Running structured field extraction")

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    full = text

    result = {
        # ── Document identity ──────────────────────────────────────────────
        "document_type": _detect_document_type(full),
        "form_number": _extract_form_number(full),

        # ── Government document header fields ──────────────────────────────
        "division": _extract_division(full),
        "ddo_code": _extract_ddo_code(full),
        "account_number": _extract_account_number(full),
        "month_year": _extract_month_year(full),

        # ── Financial figures ──────────────────────────────────────────────
        "grand_total": _extract_grand_total(full),
        "opening_balance": _extract_balance(full, "opening"),
        "closing_balance": _extract_balance(full, "closing"),
        "total_receipts": _extract_labelled_amount(full, r"total.*receipt|receipt.*total"),
        "total_expenditure": _extract_labelled_amount(full, r"total.*expenditure|expenditure.*total|grand\s+total"),

        # ── Head of Account codes ──────────────────────────────────────────
        "head_of_account_codes": _extract_head_codes(full),

        # ── Remittances ────────────────────────────────────────────────────
        "pw_remittances_cheque": _extract_labelled_amount(full, r"pw\s+remittance.*cheque|8782.*102.*02"),
        "pw_remittances_cash": _extract_labelled_amount(full, r"pw\s+remittance.*remittance|8782.*102.*01"),

        # ── Tax / deposit heads ────────────────────────────────────────────
        "income_tax_amount": _extract_labelled_amount(full, r"income\s+tax|8658.*112"),
        "gst_amount": _extract_labelled_amount(full, r"gst|8658.*139|8658.*0139"),
        "civil_deposit": _extract_labelled_amount(full, r"civil\s+deposit|8443"),

        # ── Schedule-specific ──────────────────────────────────────────────
        "schedule_particulars": _extract_schedule_particulars(lines),

        # ── Work expenditure table ─────────────────────────────────────────
        "work_expenditure_entries": _extract_work_expenditure(lines),

        # ── Dates ──────────────────────────────────────────────────────────
        "dates_found": _extract_dates(full),

        # ── GST number ─────────────────────────────────────────────────────
        "gst_registration_no": _extract_gst_number(full),

        # ── Officers ───────────────────────────────────────────────────────
        "officers_mentioned": _extract_officers(lines),

        # ── Validation flags ───────────────────────────────────────────────
        "validation": _run_basic_validation(full),
    }

    logger.info(f"Phase 2 extraction complete: {result['document_type']} | "
                f"grand_total={result['grand_total']} | "
                f"{len(result['head_of_account_codes'])} HoA codes")

    return result


# ── Private extraction helpers ────────────────────────────────────────────────

def _empty_extraction() -> Dict[str, Any]:
    return {
        "document_type": None, "form_number": None, "division": None,
        "ddo_code": None, "account_number": None, "month_year": None,
        "grand_total": None, "opening_balance": None, "closing_balance": None,
        "total_receipts": None, "total_expenditure": None,
        "head_of_account_codes": [], "pw_remittances_cheque": None,
        "pw_remittances_cash": None, "income_tax_amount": None,
        "gst_amount": None, "civil_deposit": None,
        "schedule_particulars": [], "work_expenditure_entries": [],
        "dates_found": [], "gst_registration_no": None,
        "officers_mentioned": [], "validation": {},
    }


def _detect_document_type(text: str) -> str:
    upper = text.upper()
    if re.search(r'FORM[- ]?80|MONTHLY ACCOUNT', upper):
        return "Monthly Account (Form-80)"
    if re.search(r'FORM[- ]?46|SCHEDULE OF REVENUE|SCHEDULE OF.*FOR THE MONTH', upper):
        return "Schedule of Revenue/Receipts (Form-46)"
    if re.search(r'FORM[- ]?74|CLASSIFIED ABSTRACT', upper):
        return "Classified Abstract of Expenditure (Form-74)"
    if re.search(r'FORM[- ]?64|SCHEDULE OF WORK', upper):
        return "Schedule of Work Expenditure (Form-64)"
    if re.search(r'CASH BALANCE', upper):
        return "Cash Balance Report (Form-5)"
    if re.search(r'LIST OF ACCOUNTS|CODE NO\.?\s*516', upper):
        return "List of Accounts Submitted"
    return "Government Financial Document"


def _extract_form_number(text: str) -> Optional[str]:
    m = re.search(r'FORM[- ]?(\d{1,3})', text, re.IGNORECASE)
    return f"Form-{m.group(1)}" if m else None


def _extract_division(text: str) -> Optional[str]:
    patterns = [
        r'(?:OFFICE OF THE EXECUTIVE ENGINEER[,\s]+)(.*?DIVISION[,\s]+BHOPAL)',
        r'((?:P\.?W\.?D\.?|PWD).*?DIVISION[,\s]+BHOPAL)',
        r'DIVISION\s*[:\-]?\s*(.*?BHOPAL)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def _extract_ddo_code(text: str) -> Optional[str]:
    m = re.search(r'DDO\s*CODE\s*(?:NO\.?)?\s*[:\-]?\s*(\d{8,12})', text, re.IGNORECASE)
    return m.group(1) if m else None


def _extract_account_number(text: str) -> Optional[str]:
    m = re.search(r'A/?C\s*(?:NO\.?)?\s*(?:PW/?)?\s*(\d{3,6})', text, re.IGNORECASE)
    if m:
        return f"PW/{m.group(1)}"
    m2 = re.search(r'PW[-/]?(\d{3,6})', text, re.IGNORECASE)
    return f"PW/{m2.group(1)}" if m2 else None


def _extract_month_year(text: str) -> Optional[str]:
    m = re.search(
        r'(?:MONTH[:\s]+|FOR THE MONTH OF\s+)'
        r'(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)'
        r'[\s,]+(\d{4})',
        text, re.IGNORECASE
    )
    if m:
        return f"{m.group(1).capitalize()} {m.group(2)}"
    m2 = re.search(r'(MARCH|APRIL|MAY|JUNE)\s+(\d{4})', text, re.IGNORECASE)
    return f"{m2.group(1).capitalize()} {m2.group(2)}" if m2 else None


def _parse_indian_amount(s: str) -> Optional[float]:
    """Parse Indian-format number string (e.g. '1,82,68,500.00') to float."""
    try:
        cleaned = re.sub(r'[₹,\s]', '', s)
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _extract_labelled_amount(text: str, label_pattern: str) -> Optional[str]:
    """Find an amount on the same line as a label pattern."""
    pattern = rf'(?:{label_pattern}).*?([\d,{{6,}}\.?\d*])'
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        return m.group(1)
    # Try: label on one line, amount on next
    for match in re.finditer(label_pattern, text, re.IGNORECASE):
        snippet = text[match.start():match.start() + 200]
        amounts = re.findall(r'[\d,]{5,}\.?\d*', snippet)
        if amounts:
            return amounts[0]
    return None


def _extract_grand_total(text: str) -> Optional[str]:
    m = re.search(r'GRAND\s*TOTAL[^₹\d]*([\d,]{6,}\.?\d*)', text, re.IGNORECASE)
    if m:
        return m.group(1)
    # Try from Form-80 grand total row (both receipt and expenditure equal)
    amounts = re.findall(r'[\d,]{8,}\.?\d*', text)
    if amounts:
        # Return the largest amount as candidate grand total
        parsed = [(a, _parse_indian_amount(a)) for a in amounts]
        parsed = [(a, v) for a, v in parsed if v is not None]
        if parsed:
            return max(parsed, key=lambda x: x[1])[0]
    return None


def _extract_balance(text: str, balance_type: str) -> Optional[str]:
    keyword = "OPENING" if balance_type == "opening" else "CLOSING"
    m = re.search(rf'{keyword}\s*BALANCE\s*[=:\-]?\s*([\d,{{4,}}\.?\d*])', text, re.IGNORECASE)
    return m.group(1) if m else None


def _extract_head_codes(text: str) -> List[str]:
    """Extract Head of Account codes like 24/5054/03/337/... or 8443, 8658 etc."""
    # Long codes like 24-5054-04-337-0101-...
    long_codes = re.findall(
        r'\b(?:24|67|80|00)[-/]\d{4}[-/][\d\w][-/][\d]{3}[-/][\d\w\-/]{4,}',
        text
    )
    # Short major heads: 4-digit starting with 0-9
    short_codes = re.findall(r'\b(8[0-9]{3}|4[0-9]{3}|2[0-9]{3})\b', text)
    all_codes = list(dict.fromkeys(long_codes + short_codes))  # deduplicate, preserve order
    return all_codes[:20]


def _extract_schedule_particulars(lines: List[str]) -> List[Dict[str, str]]:
    """Extract Amount B.F., Pertaining, Total, Refunds, C.O. rows from schedules."""
    items = []
    labels = {
        'amount b.f.': 'Amount B/F Last Month',
        'pertaining to this': 'Pertaining to This Month',
        'total end': 'Total End of Month',
        'deduct refund': 'Deduct Refunds',
        'upto date': 'Upto Date C.O.',
    }
    for line in lines:
        lower = line.lower()
        for key, label in labels.items():
            if key in lower:
                amounts = re.findall(r'[\d,]{4,}\.?\d*', line)
                items.append({
                    "label": label,
                    "amount": amounts[0] if amounts else None,
                    "raw_line": line,
                })
                break
    return items


def _extract_work_expenditure(lines: List[str]) -> List[Dict[str, Any]]:
    """Extract work expenditure table rows (head code + 2–3 amounts)."""
    entries = []
    code_pattern = re.compile(
        r'(\d{2,3}[-/]\d{4}[-/][\d\w][-/][\d]{3}[-/][\d\w\-/]{4,})'
    )
    for line in lines:
        m = code_pattern.search(line)
        if m:
            code = m.group(1)
            amounts = re.findall(r'[\d,]{4,}\.?\d*', line)
            if amounts:
                entries.append({
                    "head_code": code,
                    "expenditure_this_month": amounts[0] if len(amounts) > 0 else None,
                    "expenditure_prev_month": amounts[1] if len(amounts) > 1 else None,
                    "expenditure_year": amounts[2] if len(amounts) > 2 else None,
                })
    return entries[:30]  # cap at 30 rows


def _extract_dates(text: str) -> List[str]:
    """Extract all dates in DD/MM/YYYY or YYYY-MM-DD or text formats."""
    patterns = [
        r'\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b',
        r'\b(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})\b',
    ]
    found = set()
    for pat in patterns:
        for m in re.finditer(pat, text):
            found.add(m.group(0))
    return sorted(found)


def _extract_gst_number(text: str) -> Optional[str]:
    """Extract GSTIN (15-char alphanumeric)."""
    m = re.search(r'\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1})\b', text)
    return m.group(1) if m else None


def _extract_officers(lines: List[str]) -> List[str]:
    """Extract officer designations mentioned."""
    designations = [
        r'executive engineer', r'divisional accounts officer',
        r'sr\.?\s*divisional', r'superintending engineer',
        r'chief engineer', r'accountant general',
        r'deputy accountant', r'assistant engineer',
    ]
    found = []
    for line in lines:
        lower = line.lower()
        for d in designations:
            if re.search(d, lower) and line not in found:
                found.append(line.strip())
                break
    return found[:5]


def _run_basic_validation(text: str) -> Dict[str, Any]:
    """
    Run lightweight validation checks on the document.
    Returns flags and messages.
    """
    flags = {}

    # Check grand total presence
    flags["has_grand_total"] = bool(re.search(r'GRAND\s*TOTAL', text, re.IGNORECASE))

    # Check if opening = closing balance (Form-80 requirement)
    ob_m = re.search(r'OPENING\s+BALANCE\s*=\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
    cb_m = re.search(r'CLOSING\s+BALANCE\s*=\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
    if ob_m and cb_m:
        ob = _parse_indian_amount(ob_m.group(1))
        cb = _parse_indian_amount(cb_m.group(1))
        flags["balance_matches"] = (ob == cb) if (ob is not None and cb is not None) else None
        flags["opening_balance_value"] = ob_m.group(1)
        flags["closing_balance_value"] = cb_m.group(1)

    # Check DDO code present
    flags["has_ddo_code"] = bool(re.search(r'DDO\s*CODE', text, re.IGNORECASE))

    # Check signatures/officer names
    flags["has_officer_signature"] = bool(
        re.search(r'executive engineer|divisional accounts officer', text, re.IGNORECASE)
    )

    # Check for suspiciously round numbers (possible error)
    round_amounts = re.findall(r'\b(\d{6,})000\.00\b', text)
    flags["round_number_amounts"] = round_amounts[:5] if round_amounts else []

    return flags
