# Complete System Summary

## Three OCR Engines + Multi-Format Extraction

### System Architecture

```
unified/
├── ocr1/                    # Tesseract OCR
│   ├── engine.py
│   ├── preprocessing.py
│   ├── postprocessing.py
│   └── pdf_handler.py
│
├── ocr2/                    # Sarvam AI OCR
│   ├── sarvam_engine.py
│   └── config.py
│
├── ocr3/                    # PaddleOCR (NEW)
│   ├── paddle_engine.py
│   ├── preprocessing.py
│   ├── text_grouping.py
│   ├── output_formatters.py
│   ├── pdf_handler.py
│   └── config.py
│
└── main/
    ├── backend/
    │   ├── services/
    │   │   ├── ocr_service.py          # Unified OCR selector
    │   │   ├── metadata_service.py     # Multi-format storage
    │   │   ├── preprocessing/          # Text preprocessing
    │   │   ├── embedding_service.py    # Vector embeddings
    │   │   └── vector_store.py         # FAISS storage
    │   │
    │   ├── routes/
    │   │   ├── upload.py               # Document upload
    │   │   ├── chat.py                 # RAG chat
    │   │   ├── extractions.py          # View extractions
    │   │   └── health.py               # Health check
    │   │
    │   ├── agents/
    │   │   ├── validation_agent.py     # OCR validation
    │   │   └── rag_agent.py            # RAG queries
    │   │
    │   └── main.py                     # FastAPI app
    │
    └── frontend/
        ├── src/
        │   ├── pages/
        │   │   └── ExtractionsPage.jsx # View all extractions
        │   ├── components/
        │   │   ├── upload/             # Upload UI
        │   │   └── chat/               # Chat UI
        │   └── services/
        │       ├── extractionsApi.js   # Extractions API
        │       └── chatApi.js          # Chat API
        │
        └── package.json
```

## OCR Engines Comparison

| Feature | Tesseract (ocr1) | Sarvam (ocr2) | PaddleOCR (ocr3) |
|---------|------------------|---------------|------------------|
| **Type** | Local | Cloud API | Local |
| **Languages** | Limited | Excellent | Multi-language |
| **Speed** | Fast | API dependent | Fast (GPU) |
| **Accuracy** | Good | Excellent | Excellent |
| **Cost** | Free | Paid | Free |
| **Offline** | ✓ | ✗ | ✓ |
| **GPU Support** | ✗ | N/A | ✓ |
| **Hindi Support** | Basic | Excellent | Excellent |
| **CSV Output** | ✗ | ✗ | ✓ |
| **Preprocessing** | Basic | N/A | Advanced |

## Complete Pipeline

### 1. Upload Document
```
User uploads PDF/Image
    ↓
Validate file type & size
    ↓
Save to uploads/
```

### 2. OCR Processing
```
Select OCR engine (from .env)
    ↓
┌─────────────┬──────────────┬──────────────┐
│ Tesseract   │ Sarvam AI    │ PaddleOCR    │
│ (ocr1)      │ (ocr2)       │ (ocr3)       │
└─────────────┴──────────────┴──────────────┘
    ↓
Extract text + confidence + pages
```

### 3. Validation
```
Validation Agent checks:
- Confidence score
- Word count
- Text quality
    ↓
Recommendation: accept | review | reject
```

### 4. Preprocessing
```
pp1: Cleaning (remove noise, fix spacing)
    ↓
pp2: Normalization (case, unicode)
    ↓
pp3: Metadata extraction (entities, dates)
    ↓
pp4: Chunking (split into semantic chunks)
```

### 5. Embedding & Storage
```
Generate embeddings (all-MiniLM-L6-v2)
    ↓
Store in FAISS vector DB
    ↓
Save metadata (JSON + TXT + CSV*)
```

### 6. Retrieval (RAG)
```
User query
    ↓
Generate query embedding
    ↓
Search FAISS (top-k similar chunks)
    ↓
LLM generates answer with context
```

## Output Formats

### All Engines
- **JSON**: Complete metadata in `data/extracted_json/`
- **TXT**: Plain text in `data/extracted_metadata/`

### PaddleOCR Only
- **CSV**: Structured data in `data/extracted_metadata/`

### Format Details

#### JSON (extracted_json/)
```json
{
  "file_id": "uuid",
  "filename": "document.pdf",
  "ocr_engine": "paddleocr",
  "confidence": 0.92,
  "word_count": 1234,
  "chunks_created": 25,
  "validation": {...},
  "structured_fields": {...}
}
```

#### JSON (extracted_metadata/)
```json
{
  "file_id": "uuid",
  "filename": "document.pdf",
  "timestamp": "2026-02-28T...",
  "ocr": {
    "engine": "paddleocr",
    "confidence": 0.92,
    "full_text": "...",
    "structured_fields": {...}
  },
  "validation": {...},
  "preprocessing": {...}
}
```

#### TXT
```
File: document.pdf
File ID: uuid
OCR Engine: paddleocr
Confidence: 92.00%
Word Count: 1234
Pages: 5

============================================================
EXTRACTED TEXT
============================================================

[Full extracted text here]
```

#### CSV (PaddleOCR only)
```csv
Page,Row,Text
1,1,Header text
1,2,First row content
2,1,Second page content
```

## API Endpoints

### Upload
```
POST /upload
- Processes document through full pipeline
- Returns: file_id, confidence, validation, etc.
```

### Chat (RAG)
```
POST /chat
Body: { "query": "What is...?" }
- Searches vector DB
- Generates answer with LLM
- Returns: answer, sources, confidence
```

### Extractions
```
GET /extractions
- List all processed documents
- Returns: summaries with metadata

GET /extractions/{file_id}
- Get complete extraction details
- Returns: full metadata + text

GET /extractions/{file_id}/text
- Download as plain text file

GET /extractions/{file_id}/csv
- Download as CSV (PaddleOCR only)

DELETE /extractions/{file_id}
- Delete extraction metadata
```

### Health
```
GET /health
- System health check
- Returns: status, ocr_engine, vector_count
```

## Frontend Pages

### 1. Upload Page (/)
- Drag & drop file upload
- Real-time processing status
- OCR results display
- Validation badges
- Structured fields view

### 2. Extractions Page (/extractions)
- List all processed documents
- Filter by OCR engine
- Download TXT/CSV
- View full details
- Delete extractions

### 3. Chat Page (/chat)
- RAG-powered Q&A
- Source citations
- Conversation history
- Confidence scores

## Configuration

### .env File
```bash
# OCR Engine Selection
OCR_ENGINE=paddleocr  # tesseract | sarvam | paddleocr

# Tesseract
TESSERACT_PATH=/opt/homebrew/bin/tesseract
TESSERACT_LANG=eng

# Sarvam AI
SARVAM_API_KEY=your_key_here

# PaddleOCR
PADDLE_LANG=hi
PADDLE_USE_GPU=false
PADDLE_DPI=200
PADDLE_CONF_THRESH=0.30
ENABLE_CSV_OUTPUT=true

# LLM
LLM_MODEL_PATH=../../Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Chunking
CHUNK_SIZE=400
CHUNK_OVERLAP=50

# Server
HOST=0.0.0.0
PORT=8000
```

## Installation

### Backend
```bash
cd unified/main

# Install base requirements
pip install -r requirements.txt

# For PaddleOCR
pip install -r ../ocr3/requirements.txt

# Start server
python -m backend.main
```

### Frontend
```bash
cd unified/main/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

## Usage Flow

1. **Start Backend**: `python -m backend.main`
2. **Start Frontend**: `npm run dev`
3. **Upload Document**: Go to http://localhost:5173
4. **View Extractions**: Click "Extractions" in nav
5. **Download Formats**: Click TXT or CSV buttons
6. **Ask Questions**: Go to Chat page

## Key Features

### ✓ Three OCR Engines
- Switch between engines via .env
- Each optimized for different use cases
- Consistent output format

### ✓ Multi-Format Output
- JSON for structured data
- TXT for plain text
- CSV for tabular data (PaddleOCR)

### ✓ Complete Pipeline
- OCR → Validation → Preprocessing → Embedding → Storage
- Automatic metadata extraction
- Quality validation

### ✓ RAG System
- Vector search with FAISS
- LLM-powered answers
- Source citations

### ✓ Modern UI
- React + Tailwind CSS
- Real-time updates
- Responsive design

## Performance

### Processing Speed (per page)
- Tesseract: ~1-2s
- Sarvam: ~2-3s (API)
- PaddleOCR CPU: ~2-3s
- PaddleOCR GPU: ~0.5-1s

### Accuracy
- Tesseract: 85-90% (English)
- Sarvam: 95%+ (Hindi/English)
- PaddleOCR: 90-95% (Multi-language)

## Next Steps

1. Add batch processing
2. Implement progress tracking
3. Add document type classification
4. Support more languages
5. Add export to Excel
6. Implement user authentication
7. Add document comparison
8. Create API documentation

## Troubleshooting

### OCR Engine Not Working
```bash
# Check .env
cat .env | grep OCR_ENGINE

# Test engine
python -c "from ocr3 import PaddleOCREngine; print('OK')"
```

### No CSV Output
- Only PaddleOCR generates CSV
- Check `OCR_ENGINE=paddleocr` in .env
- Verify `ENABLE_CSV_OUTPUT=true`

### Low Confidence
- Try different OCR engine
- Increase DPI (PaddleOCR)
- Check image quality

### Memory Issues
- Lower DPI
- Process fewer pages
- Use CPU instead of GPU

## Support

For issues or questions:
1. Check documentation in `docs/`
2. Review `.md` files in each folder
3. Test with `test_paddle.py`
4. Check logs in `data/logs/`
