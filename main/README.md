# Government Document Intelligence System

Unified system combining Tesseract/Sarvam OCR + RAG (Llama 3.1 8B + FAISS) + React frontend.

---

## Project Structure

```
unified/
├── ocr1/          Tesseract OCR engine
├── ocr2/          Sarvam AI OCR engine
└── main/
    ├── .env       All configuration lives here
    ├── backend/   FastAPI app
    └── frontend/  React + Vite + TailwindCSS
```

---

## Prerequisites

### Python 3.10+
```bash
# Check
python --version          # macOS/Linux
python --version          # Windows
```

### Node.js 18+
```bash
node --version
```

### Tesseract OCR (if using OCR_ENGINE=tesseract)
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows — download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki
# Default install path: C:\Program Files\Tesseract-OCR\tesseract.exe
# Add Tesseract to Windows PATH during install, or set TESSERACT_PATH in .env
```

### Poppler (required for PDF processing)
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows — download from:
# https://github.com/oschwartz10612/poppler-windows/releases/
# Extract zip, add the bin/ folder to your Windows PATH
# Or set PDF poppler_path in ocr1/pdf_handler.py
```

---

## Backend Setup

### macOS / Linux
```bash
cd unified/main/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download SpaCy model
python -m spacy download en_core_web_sm

# Run server
cd unified/main
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Windows
```cmd
cd unified\main\backend

:: Create virtual environment
python -m venv venv
venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt

:: Download SpaCy model
python -m spacy download en_core_web_sm

:: Run server
cd unified\main
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API: http://localhost:8000
Docs: http://localhost:8000/docs

---

## Frontend Setup

### macOS / Linux
```bash
cd unified/main/frontend
npm install
npm run dev
```

### Windows
```cmd
cd unified\main\frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

---

## Configuration (main/.env)

### Switch OCR Engine
```env
# Use Tesseract (local, offline)
OCR_ENGINE=tesseract
TESSERACT_PATH=/opt/homebrew/bin/tesseract        # macOS Homebrew
# TESSERACT_PATH=/usr/bin/tesseract               # Linux
# TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe  # Windows

# Use Sarvam AI (cloud, Hindi+English)
OCR_ENGINE=sarvam
SARVAM_API_KEY=your_actual_key_here
```

### LLM Model Path
The GGUF model is in the parent `govt-doc/` folder.
```env
# macOS/Linux
LLM_MODEL_PATH=../../Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf

# Windows (use absolute path to avoid issues)
# LLM_MODEL_PATH=C:\Users\YourName\Desktop\govt-doc\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /upload | Upload + process document |
| GET | /upload/status/{file_id} | Get processing result |
| POST | /chat | Query documents via RAG |
| GET | /health | System health check |
| GET | / | System info |

---

## Upload Flow

```
PDF/Image → OCR (tesseract or sarvam)
         → validation_agent (confidence check, field validation)
         → pp1 cleaning → pp2 normalization → pp3 metadata → pp4 chunking
         → embeddings (all-MiniLM-L6-v2)
         → FAISS vector DB
```

## Chat Flow

```
User query → rag_agent.refine_query (Llama 3.1 8B)
           → FAISS retrieval (top-5 chunks)
           → rag_agent.generate_answer (Llama 3.1 8B)
           → response + sources
```

---

## Troubleshooting

### Tesseract not found
```bash
# macOS
brew install tesseract
which tesseract   # get path → paste into .env TESSERACT_PATH

# Windows — check install path and update .env:
# TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Poppler not found (PDF error)
```bash
# macOS
brew install poppler

# Windows — download from oschwartz10612/poppler-windows, add bin/ to PATH
```

### LLM model not found
Make sure `Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf` is in `govt-doc/` (parent of `unified/`).
On Windows use an absolute path in `.env` to avoid relative path issues.

### faiss-cpu install fails on Windows
```cmd
pip install faiss-cpu --no-cache-dir
```

### llama-cpp-python install fails
```bash
# CPU only (default)
pip install llama-cpp-python

# With GPU (CUDA) — Windows/Linux
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
pip install llama-cpp-python --no-cache-dir
```

### Import errors (backend.* not found)
Always run uvicorn from `unified/main/`, not from `unified/main/backend/`:
```bash
# Correct
cd unified/main
python -m uvicorn backend.main:app --reload

# Wrong
cd unified/main/backend
python -m uvicorn main:app --reload   # ← breaks imports
```
