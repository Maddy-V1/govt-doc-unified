"""
ocr2/sarvam_engine.py
Sarvam AI OCR Engine — fixed imports for unified project structure.
"""

import os
import re
import logging
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Sarvam AI API key — loaded from environment (set in main/.env)
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")


def _get_sarvam_client():
    if not SARVAM_API_KEY:
        raise RuntimeError(
            "SARVAM_API_KEY is not set. Add it to main/.env"
        )
    from sarvamai import SarvamAI
    return SarvamAI(api_subscription_key=SARVAM_API_KEY)


def _extract_pages_from_html(html_content: str) -> List[str]:
    soup = BeautifulSoup(html_content, "html.parser")

    # Strategy 1: page-break divs
    page_divs = soup.find_all('div', style=lambda s: s and 'page-break' in s)
    if page_divs:
        pages = [d.get_text(separator="\n", strip=True) for d in page_divs]
        pages = [p for p in pages if p]
        if pages:
            return pages

    # Strategy 2: top-level divs
    body = soup.find('body') or soup
    top_divs = body.find_all('div', recursive=False)
    if len(top_divs) > 1:
        pages = [d.get_text(separator="\n", strip=True) for d in top_divs]
        pages = [p for p in pages if p]
        if len(pages) > 1:
            return pages

    # Strategy 3: <hr> separators
    hrs = soup.find_all('hr')
    if hrs:
        parts = re.split(r'<hr\s*/?>', str(soup), flags=re.IGNORECASE)
        pages = []
        for part in parts:
            text = BeautifulSoup(part, "html.parser").get_text(separator="\n", strip=True)
            if text.strip():
                pages.append(text)
        if len(pages) > 1:
            return pages

    # Strategy 4: markdown-style page separators
    full_text = soup.get_text(separator="\n", strip=True)
    parts = re.split(r'\n\s*[-=]{3,}\s*(?:Page\s*\d+)?\s*[-=]{3,}\s*\n',
                     full_text, flags=re.IGNORECASE)
    if len(parts) > 1:
        pages = [p.strip() for p in parts if p.strip()]
        if len(pages) > 1:
            return pages

    # Strategy 5: sections/articles
    sections = soup.find_all(['section', 'article'])
    if len(sections) > 1:
        pages = [s.get_text(separator="\n", strip=True) for s in sections]
        pages = [p for p in pages if p]
        if len(pages) > 1:
            return pages

    # Fallback: single page
    if full_text.strip():
        return [full_text]
    return []


def _extract_text_from_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def _extract_pages_from_zip(zip_path: str) -> List[Dict[str, Any]]:
    pages = []
    with zipfile.ZipFile(zip_path, 'r') as zf:
        file_list = zf.namelist()
        logger.info(f"ZIP contents: {file_list}")

        html_files = sorted([f for f in file_list if f.endswith(('.html', '.htm'))])
        md_files   = sorted([f for f in file_list if f.endswith('.md')])
        txt_files  = sorted([f for f in file_list if f.endswith('.txt')])

        content_files = html_files or md_files or txt_files
        is_html = bool(html_files)

        if not content_files:
            logger.warning(f"No content files in ZIP: {file_list}")
            return []

        if len(content_files) > 1:
            for idx, filename in enumerate(content_files, start=1):
                with zf.open(filename) as f:
                    content = f.read().decode('utf-8', errors='replace')
                text = _extract_text_from_html(content) if is_html else content.strip()
                if text.strip():
                    pages.append({
                        'page_number': idx,
                        'text': text,
                        'word_count': len(text.split()),
                        'source_file': filename,
                    })
        else:
            filename = content_files[0]
            with zf.open(filename) as f:
                content = f.read().decode('utf-8', errors='replace')

            if is_html:
                page_texts = _extract_pages_from_html(content)
            else:
                parts = re.split(r'\n\s*[-=]{3,}\s*\n|\n\s*#+\s*Page\s+\d+',
                                  content, flags=re.IGNORECASE)
                page_texts = [p.strip() for p in parts if p.strip()]

            for idx, text in enumerate(page_texts, start=1):
                if text.strip():
                    pages.append({
                        'page_number': idx,
                        'text': text,
                        'word_count': len(text.split()),
                        'source_file': filename,
                    })
    return pages


def extract_text_sarvam(file_path: Path, language: str = "hi-IN") -> Dict[str, Any]:
    """
    Extract text using Sarvam AI Document Intelligence API.

    Args:
        file_path: Path to PDF or image file
        language:  BCP-47 language code (default hi-IN for Hindi+English govt docs)

    Returns:
        {
            'full_text': str,
            'word_count': int,
            'pages': list[dict],
            'page_metrics': dict | None,
        }
    """
    temp_dir = None
    try:
        client   = _get_sarvam_client()
        file_path = Path(file_path)

        logger.info(f"Sarvam OCR start: {file_path.name} (lang={language})")

        job = client.document_intelligence.create_job(
            language=language, output_format="html"
        )
        logger.info(f"Job created: {job.job_id}")

        job.upload_file(str(file_path))
        job.start()
        status = job.wait_until_complete()
        logger.info(f"Job state: {status.job_state}")

        page_metrics = None
        try:
            page_metrics = job.get_page_metrics()
        except Exception as e:
            logger.warning(f"page_metrics unavailable: {e}")

        temp_dir = tempfile.mkdtemp(prefix="sarvam_ocr_")
        output_zip = os.path.join(temp_dir, "output.zip")
        job.download_output(output_zip)

        pages = _extract_pages_from_zip(output_zip)

        if not pages:
            return {'full_text': '', 'word_count': 0, 'pages': [], 'page_metrics': page_metrics}

        # If Sarvam returned 1 block but API says multi-page, split by lines
        expected = (page_metrics or {}).get('total_pages', 0)
        if expected > 1 and len(pages) == 1:
            lines = pages[0]['text'].split('\n')
            if len(lines) >= expected:
                lpp = max(1, len(lines) // expected)
                pages = []
                for pg in range(expected):
                    start = pg * lpp
                    end   = start + lpp if pg < expected - 1 else len(lines)
                    txt   = '\n'.join(lines[start:end]).strip()
                    pages.append({
                        'page_number': pg + 1,
                        'text': txt,
                        'word_count': len(txt.split()),
                        'source_file': 'split_from_single',
                    })

        full_text   = "\n\n".join(p['text'] for p in pages).strip()
        total_words = sum(p['word_count'] for p in pages)

        logger.info(f"Sarvam OCR done: {total_words} words, {len(pages)} pages")
        return {
            'full_text':    full_text,
            'word_count':   total_words,
            'pages':        pages,
            'page_metrics': page_metrics,
        }

    except Exception as e:
        logger.error(f"Sarvam OCR failed: {e}", exc_info=True)
        raise RuntimeError(f"Sarvam OCR error: {e}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


def test_sarvam_connection() -> bool:
    try:
        if not SARVAM_API_KEY:
            return False
        _get_sarvam_client()
        return True
    except Exception as e:
        logger.error(f"Sarvam connection failed: {e}")
        return False
