# Setup Guide - Unified Government Document Intelligence System

## Quick Start Checklist

### 1. Prerequisites Installation

#### macOS (using Homebrew)
```bash
# Install Tesseract OCR
brew install tesseract

# Install Poppler (for PDF processing)
brew install poppler

# Install Python 3.9+
brew install python@3.11

# Install Node.js 18+
brew install node
```

#### Verify Installations
```bash
tesseract --version
pdfinfo -v
python3 --version
node --version
```

### 2. Backend Setup

```bash
cd unified/main/backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download SpaCy language model
python -m spacy download en_core_web_sm
```

### 3. Environment Configuration

Edit `unified/main/.env`:

```bash
# Choose OCR engine
OCR_ENGINE=tesseract  # or 'sarvam'

# For Tesseract (local)
TESSERACT_PATH=/opt/homebrew/bin/tesseract
TESSERACT_LANG=eng

# For Sarvam AI (cloud) - if using
SARVAM_API_KEY=your_actual_api_key_here

# LLM Model Path - verify this exists!
LLM_MODEL_PATH=../../Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
```

**Important**: Verify the LLM model file exists:
```bash
ls -lh ~/Desktop/govt-doc/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
```

### 4. Frontend Setup

```bash
cd unified/main/frontend

# Install Node dependencies
npm install
```

### 5. Run the Application

#### Terminal 1 - Backend
```bash
cd unified/main/backend
source venv/bin/activate
python main.py
```

Backend will start at: `http://localhost:8000`

#### Terminal 2 - Frontend
```bash
cd unified/main/frontend
npm run dev
```

Frontend will start at: `http://localhost:5173`

### 6. Verify System Health

Open browser: `http://localhost:8000/health`

Should show:
- ✅ Tesseract: OK (if using tesseract)
- ✅ LLM Model: OK
- ✅ Vector DB: OK
- ✅ Embedding Model: OK

### 7. Test the System

1. Open `http://localhost:5173`
2. Upload a test PDF or image
3. Wait for processing
4. Check the results (OCR confidence, validation, structured fields)
5. Go to Chat page
6. Ask questions about the uploaded document

## Common Issues & Solutions

### Issue: Tesseract not found
```bash
# Install Tesseract
brew install tesseract

# Update .env with correct path
which tesseract  # Copy this path to TESSERACT_PATH in .env
```

### Issue: Poppler not found (pdf2image error)
```bash
brew install poppler
```

### Issue: LLM model not found
```bash
# Download the model or update the path in .env
# The model should be at: ~/Desktop/govt-doc/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
```

### Issue: SpaCy model not found
```bash
python -m spacy download en_core_web_sm
```

### Issue: Port already in use
```bash
# Backend (8000)
lsof -ti:8000 | xargs kill -9

# Frontend (5173)
lsof -ti:5173 | xargs kill -9
```

### Issue: FAISS import error
```bash
pip install --force-reinstall faiss-cpu
```

### Issue: llama-cpp-python build error
```bash
# Install with pre-built wheels
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

## Switching OCR Engines

### To use Tesseract (Local, Free)
Edit `.env`:
```bash
OCR_ENGINE=tesseract
TESSERACT_PATH=/opt/homebrew/bin/tesseract
```

### To use Sarvam AI (Cloud, Requires API Key)
Edit `.env`:
```bash
OCR_ENGINE=sarvam
SARVAM_API_KEY=your_actual_api_key
```

Restart the backend after changing OCR engine.

## Project Structure

```
unified/
├── ocr1/                    # Tesseract OCR engine
├── ocr2/                    # Sarvam AI OCR engine
└── main/
    ├── .env                 # Configuration
    ├── backend/
    │   ├── agents/          # Validation & RAG agents
    │   ├── core/            # Config & logging
    │   ├── routes/          # API endpoints
    │   ├── services/        # OCR, preprocessing, embeddings, LLM
    │   ├── vector_db/       # FAISS vector database
    │   └── main.py          # FastAPI application
    ├── frontend/            # React application
    ├── uploads/             # Uploaded files (auto-created)
    ├── data/                # Processed data & logs (auto-created)
    └── vector_db/           # FAISS index storage (auto-created)
```

## API Documentation

Once backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development Tips

### Backend Hot Reload
The backend auto-reloads on code changes (RELOAD=True in .env)

### Frontend Hot Reload
Vite automatically reloads on code changes

### View Logs
```bash
tail -f unified/main/data/logs/app.log
```

### Clear Vector Database
```bash
rm -rf unified/main/vector_db/faiss.index
rm -rf unified/main/vector_db/metadata.pkl
```

### Reset Uploads
```bash
rm -rf unified/main/uploads/pdfs/*
rm -rf unified/main/uploads/images/*
rm -rf unified/main/data/extracted_json/*
```

## Production Deployment

For production:
1. Set `DEBUG=False` in `.env`
2. Set `RELOAD=False` in `.env`
3. Use proper CORS origins
4. Use a production WSGI server (gunicorn)
5. Set up proper logging
6. Use environment variables instead of .env file
7. Set up SSL/TLS
8. Use a reverse proxy (nginx)

## Support

For issues, check:
1. Backend logs: `unified/main/data/logs/app.log`
2. Browser console (F12)
3. Health endpoint: `http://localhost:8000/health`
4. API docs: `http://localhost:8000/docs`
