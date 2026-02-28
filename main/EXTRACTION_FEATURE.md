# Extraction Metadata Feature

## Overview
Added a metadata extraction layer that saves extracted text and metadata from uploaded documents, with a frontend interface to view and manage extractions.

## Backend Changes

### 1. Metadata Service (`backend/services/metadata_service.py`)
- Saves extraction metadata as both JSON and plain text
- Stores in `data/extracted_metadata/` directory
- Provides methods to:
  - Save extraction (JSON + TXT)
  - Retrieve extraction by file_id
  - List all extractions with pagination
  - Delete extraction

### 2. New API Routes (`backend/routes/extractions.py`)
- `GET /extractions` - List all extractions (paginated)
- `GET /extractions/{file_id}` - Get full extraction details
- `GET /extractions/{file_id}/text` - Download plain text file
- `DELETE /extractions/{file_id}` - Delete extraction

### 3. Updated Upload Route
- Now calls `metadata_service.save_extraction()` after processing
- Saves complete metadata including:
  - OCR results (engine, confidence, full_text)
  - Validation status
  - Preprocessing metadata
  - Structured fields

## Frontend Changes

### 1. Extractions API Service (`frontend/src/services/extractionsApi.js`)
- Client-side API wrapper for extraction endpoints
- Methods for list, get, download, and delete

### 2. Extractions Page (`frontend/src/pages/ExtractionsPage.jsx`)
- List view showing all extracted documents
- Detail view with full text and metadata
- Actions: View, Download, Delete
- Color-coded confidence and validation status

### 3. Navigation
- Added "Extractions" link to main navigation
- Route: `/extractions`

## Data Storage

### Directory Structure
```
data/
├── extracted_json/          # Processing results (existing)
│   └── {file_id}.json
└── extracted_metadata/      # NEW: Full extraction metadata
    ├── {file_id}.json       # Complete metadata with full_text
    └── {file_id}.txt        # Plain text for easy viewing
```

### JSON Format
```json
{
  "file_id": "uuid",
  "filename": "document.pdf",
  "timestamp": "2026-02-28T...",
  "ocr": {
    "engine": "tesseract",
    "confidence": 0.95,
    "word_count": 1234,
    "total_pages": 5,
    "full_text": "...",
    "structured_fields": {}
  },
  "validation": {
    "recommendation": "accept",
    "warnings": []
  },
  "preprocessing": {
    "cleaned_text_length": 5000,
    "normalized_text_length": 4800,
    "chunks_created": 10,
    "metadata_extracted": {}
  }
}
```

## Usage

### Backend
```bash
# Start backend
cd unified/main
python -m backend.main
```

### Frontend
```bash
# Start frontend
cd unified/main/frontend
npm run dev
```

### API Examples
```bash
# List extractions
curl http://localhost:8000/extractions

# Get specific extraction
curl http://localhost:8000/extractions/{file_id}

# Download text
curl http://localhost:8000/extractions/{file_id}/text -o output.txt

# Delete extraction
curl -X DELETE http://localhost:8000/extractions/{file_id}
```

## Features

1. **Automatic Saving**: Every uploaded document is automatically saved with full metadata
2. **Multiple Formats**: JSON for structured data, TXT for easy reading
3. **List View**: Browse all extractions with key metrics
4. **Detail View**: View full text and all metadata
5. **Download**: Export extracted text as plain text file
6. **Delete**: Remove extractions when no longer needed
7. **Pagination**: Handle large numbers of extractions efficiently

## Benefits

- Historical record of all processed documents
- Easy access to extracted text without re-processing
- Debugging and quality assurance
- Export capability for external use
- Clean separation from vector DB storage
