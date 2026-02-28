"""
Text grouping utilities for organizing OCR output into reading-order rows
"""

import numpy as np
from typing import List, Tuple


def group_into_rows(
    texts: List[str],
    scores: List[float],
    polys: List[List],
    conf_thresh: float = 0.30,
    row_gap: int = 10
) -> List[List[Tuple[str, float, int, int]]]:
    """
    Group OCR detections into reading-order rows
    
    Args:
        texts: List of detected text strings
        scores: Confidence scores for each detection
        polys: Bounding box polygons for each detection
        conf_thresh: Minimum confidence threshold
        row_gap: Maximum Y-distance (pixels) to group into same row
        
    Returns:
        List of rows, where each row is a list of (text, score, x_min, y_min) tuples
    """
    entries = []
    
    for txt, sc, poly in zip(texts, scores, polys):
        if sc < conf_thresh:
            continue
        
        pts = np.array(poly)
        x_min = int(pts[:, 0].min())
        y_min = int(pts[:, 1].min())
        entries.append((txt, sc, x_min, y_min))
    
    if not entries:
        return []
    
    # Sort by Y position first, then X position
    entries.sort(key=lambda e: (e[3], e[2]))
    
    # Group into rows based on Y proximity
    rows = []
    current_row = [entries[0]]
    anchor_y = entries[0][3]
    
    for e in entries[1:]:
        if abs(e[3] - anchor_y) <= row_gap:
            current_row.append(e)
        else:
            # Sort current row by X position (left to right)
            rows.append(sorted(current_row, key=lambda e: e[2]))
            current_row = [e]
            anchor_y = e[3]
    
    # Add last row
    rows.append(sorted(current_row, key=lambda e: e[2]))
    
    return rows


def rows_to_plain_text(rows: List[List[Tuple]]) -> str:
    """Convert rows to plain text with newlines between rows"""
    return "\n".join("  ".join(t[0] for t in row) for row in rows)


def rows_to_json_entries(rows: List[List[Tuple]]) -> List[dict]:
    """Convert rows to JSON-serializable list"""
    out = []
    for row_idx, row in enumerate(rows):
        for t in row:
            out.append({
                "row": row_idx + 1,
                "text": t[0],
                "confidence": round(t[1], 4),
                "x_min": t[2],
                "y_min": t[3],
            })
    return out


def rows_to_csv_data(rows: List[List[Tuple]], page_num: int) -> List[List[str]]:
    """
    Convert rows to CSV-ready data
    Each row becomes: [Page, Row, Text1, Text2, ...]
    """
    csv_rows = []
    for row_idx, row in enumerate(rows):
        parts = [t[0] for t in row]
        csv_row = [str(page_num), str(row_idx + 1)] + parts
        csv_rows.append(csv_row)
    return csv_rows
