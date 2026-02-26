# System Architecture

## 🏗️ Two-Server Architecture

Your system runs **TWO separate servers** that work together:

### Server 1: Backend (FastAPI) - Port 8000
**Purpose:** Main processing engine
**Technology:** Python + FastAPI
**Location:** `unified/main/backend/`

### Server 2: Frontend (Vite) - Port 5173
**Purpose:** User interface
**Technology:** React + Vite + TailwindCSS
**Location:** `unified/main/frontend/`

---

## 🔄 Request Flow

### Upload Document Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER ACTION                                              │
│    User drags PDF to browser (localhost:5173)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. FRONTEND (React - Port 5173)                            │
│    • UploadPage.jsx captures file                          │
│    • Calls api.uploadDocument(file)                        │
│    • Sends: POST /upload with FormData                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Vite Proxy
                         │ /upload → http://localhost:8000/upload
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. BACKEND (FastAPI - Port 8000)                           │
│    routes/upload.py receives request                       │
│                                                             │
│    Step 1: Validate file (PDF/JPG/PNG, size)               │
│    Step 2: Run OCR                                          │
│            ├─ Tesseract (local) OR                         │
│            └─ Sarvam AI (cloud)                            │
│    Step 3: Validate OCR result                             │
│            └─ validation_agent.py                          │
│    Step 4: Preprocess text                                 │
│            ├─ pp1: Cleaning                                │
│            ├─ pp2: Normalization                           │
│            ├─ pp3: Metadata (SpaCy NER)                    │
│            └─ pp4: Chunking                                │
│    Step 5: Generate embeddings                             │
│            └─ SentenceTransformer (384-dim)                │
│    Step 6: Store in FAISS vector DB                        │
│    Step 7: Save JSON to data/extracted_json/               │
│                                                             │
│    Returns: JSON with results                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ JSON Response
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. FRONTEND DISPLAYS RESULTS                                │
│    • OCRResultCard shows confidence, pages, words           │
│    • ValidationBadge shows Ready/Review/Rejected            │
│    • StructuredFields shows extracted data                  │
└─────────────────────────────────────────────────────────────┘
```

### Chat Query Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER ACTION                                              │
│    User types question in chat (localhost:5173)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. FRONTEND (React - Port 5173)                            │
│    • ChatPage.jsx captures query                           │
│    • Calls api.sendChat(query)                             │
│    • Sends: POST /chat with JSON body                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Vite Proxy
                         │ /chat → http://localhost:8000/chat
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. BACKEND (FastAPI - Port 8000)                           │
│    routes/chat.py receives request                         │
│                                                             │
│    Step 1: Refine query with LLM                           │
│            └─ rag_agent.refine_query()                     │
│            └─ Llama 3.1 8B makes query more specific       │
│                                                             │
│    Step 2: Retrieve relevant chunks                        │
│            ├─ Encode query with SentenceTransformer        │
│            ├─ Search FAISS index (cosine similarity)       │
│            └─ Filter by threshold (0.3)                    │
│                                                             │
│    Step 3: Generate answer with LLM                        │
│            └─ rag_agent.generate_answer()                  │
│            └─ Llama 3.1 8B generates answer from context   │
│                                                             │
│    Returns: JSON with answer + sources                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ JSON Response
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. FRONTEND DISPLAYS RESULTS                                │
│    • MessageBubble shows answer                             │
│    • SourcePanel shows retrieved chunks with similarity     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 Port Configuration

### Backend: Port 8000
```bash
# Configured in: unified/main/.env
PORT=8000
HOST=0.0.0.0

# Accessible at:
http://localhost:8000          # Root info
http://localhost:8000/docs     # Swagger UI
http://localhost:8000/health   # Health check
http://localhost:8000/upload   # Upload endpoint
http://localhost:8000/chat     # Chat endpoint
```

### Frontend: Port 5173
```bash
# Configured in: unified/main/frontend/vite.config.js
# Default Vite dev server port

# Accessible at:
http://localhost:5173          # Main UI
http://localhost:5173/         # Upload page
http://localhost:5173/chat     # Chat page
```

### Proxy Configuration
The frontend proxies API requests to the backend:

```javascript
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/upload': 'http://localhost:8000',
      '/chat': 'http://localhost:8000',
      '/health': 'http://localhost:8000'
    }
  }
})
```

**What this means:**
- When frontend calls `/upload`, Vite forwards to `http://localhost:8000/upload`
- User only sees `http://localhost:5173` in browser
- No CORS issues because proxy handles it

---

## 📦 Component Breakdown

### Backend Components

```
backend/
├── main.py                    # FastAPI app entry point
├── core/
│   ├── config.py             # Settings from .env
│   └── logging.py            # Logging setup
├── routes/
│   ├── upload.py             # POST /upload endpoint
│   ├── chat.py               # POST /chat endpoint
│   └── health.py             # GET /health endpoint
├── services/
│   ├── ocr_service.py        # OCR engine selector
│   ├── embedding_service.py  # SentenceTransformer
│   ├── llm_service.py        # Llama 3.1 8B
│   ├── retrieval_service.py  # FAISS search
│   ├── rag_service.py        # Full RAG pipeline
│   ├── vector_store.py       # FAISS wrapper
│   └── preprocessing/
│       ├── pp1_cleaning.py   # Text cleaning
│       ├── pp2_normalization.py  # Normalization
│       ├── pp3_metadata.py   # SpaCy NER
│       └── pp4_chunking.py   # Text chunking
├── agents/
│   ├── validation_agent.py   # OCR quality check
│   └── rag_agent.py          # LLM wrapper
└── vector_db/
    └── db_client.py          # FAISS client
```

### Frontend Components

```
frontend/
├── index.html                # Entry HTML
├── src/
│   ├── main.jsx             # React entry point
│   ├── App.jsx              # Router setup
│   ├── services/
│   │   └── api.js           # API client (axios)
│   ├── components/
│   │   ├── Layout.jsx       # Header + nav + footer
│   │   ├── upload/
│   │   │   ├── UploadPage.jsx        # Upload interface
│   │   │   ├── OCRResultCard.jsx     # OCR results
│   │   │   ├── ValidationBadge.jsx   # Validation status
│   │   │   └── StructuredFields.jsx  # Extracted fields
│   │   └── chat/
│   │       ├── ChatPage.jsx          # Chat interface
│   │       ├── MessageBubble.jsx     # Message display
│   │       └── SourcePanel.jsx       # Retrieved sources
│   └── index.css            # TailwindCSS
└── vite.config.js           # Vite + proxy config
```

---

## 🚀 Starting the System

### Option 1: Two Terminals (Recommended)

**Terminal 1 - Backend:**
```bash
cd unified/main/backend
source venv/bin/activate
python main.py
```
Output: `INFO: Uvicorn running on http://0.0.0.0:8000`

**Terminal 2 - Frontend:**
```bash
cd unified/main/frontend
npm run dev
```
Output: `Local: http://localhost:5173/`

### Option 2: Background Processes

**Start Backend in Background:**
```bash
cd unified/main/backend
source venv/bin/activate
nohup python main.py > backend.log 2>&1 &
```

**Start Frontend in Background:**
```bash
cd unified/main/frontend
nohup npm run dev > frontend.log 2>&1 &
```

**Stop Processes:**
```bash
# Find and kill processes
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend
```

---

## 🔍 Debugging

### Check if Backend is Running
```bash
curl http://localhost:8000/health
# Should return JSON with status
```

### Check if Frontend is Running
```bash
curl http://localhost:5173
# Should return HTML
```

### View Backend Logs
```bash
tail -f unified/main/data/logs/app.log
```

### View Frontend Logs
Check browser console (F12)

### Test API Directly
```bash
# Upload test
curl -X POST http://localhost:8000/upload \
  -F "file=@test.pdf"

# Chat test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?"}'
```

---

## 🌐 Network Flow

```
User Browser
    │
    │ Opens http://localhost:5173
    │
    ▼
┌─────────────────────────┐
│  Vite Dev Server        │
│  Port 5173              │
│  Serves React App       │
└───────────┬─────────────┘
            │
            │ User clicks Upload/Chat
            │ Frontend makes API call
            │
            ▼
┌─────────────────────────┐
│  Vite Proxy             │
│  Forwards /upload,      │
│  /chat, /health to      │
│  http://localhost:8000  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  FastAPI Server         │
│  Port 8000              │
│  Processes Request      │
│  Returns JSON           │
└─────────────────────────┘
```

---

## 💾 Data Flow

### Upload Data Flow
```
PDF File (User)
    ↓
Frontend (FormData)
    ↓
Backend /upload
    ↓
OCR Engine (Text Extraction)
    ↓
Preprocessing (Cleaning, Chunking)
    ↓
Embedding Model (Vectors)
    ↓
FAISS Index (Storage)
    ↓
JSON File (data/extracted_json/)
```

### Query Data Flow
```
User Question (Text)
    ↓
Frontend (JSON)
    ↓
Backend /chat
    ↓
LLM (Query Refinement)
    ↓
Embedding Model (Query Vector)
    ↓
FAISS Index (Similarity Search)
    ↓
LLM (Answer Generation)
    ↓
Frontend (Display Answer + Sources)
```

---

## 🎯 Summary

**Backend (Port 8000):**
- Main processing server
- Handles OCR, embeddings, LLM, vector DB
- Python + FastAPI
- Heavy lifting happens here

**Frontend (Port 5173):**
- User interface
- Displays results
- React + Vite
- Lightweight, just UI

**Communication:**
- Frontend → Backend via HTTP requests
- Vite proxy handles routing
- JSON for data exchange

**You access:** `http://localhost:5173` (frontend)
**Frontend talks to:** `http://localhost:8000` (backend)
**User never sees:** Port 8000 (proxied)
