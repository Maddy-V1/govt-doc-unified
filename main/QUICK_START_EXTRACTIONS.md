# Quick Start: Extractions Feature

## What Was Added

A complete metadata extraction system that saves and displays all uploaded document extractions.

## Files Created

### Backend
1. `backend/services/metadata_service.py` - Metadata storage service
2. `backend/routes/extractions.py` - API endpoints for extractions
3. `data/extracted_metadata/` - Storage directory

### Frontend
1. `frontend/src/services/extractionsApi.js` - API client
2. `frontend/src/pages/ExtractionsPage.jsx` - Extractions UI

### Modified
- `backend/routes/upload.py` - Added metadata saving
- `backend/main.py` - Registered extractions router
- `frontend/src/App.jsx` - Added extractions route
- `frontend/src/components/Layout.jsx` - Added navigation link

## How to Use

### 1. Start Backend
```bash
cd unified/main
python -m backend.main
```

### 2. Start Frontend
```bash
cd unified/main/frontend
npm run dev
```

### 3. Access Extractions
- Navigate to: http://localhost:5173/extractions
- Or click "Extractions" in the navigation bar

## Features

### List View
- Shows all extracted documents
- Displays: filename, confidence, word count, pages, status
- Actions: View, Download, Delete

### Detail View
- Full extracted text
- Complete metadata
- Validation status
- Structured fields (if any)
- Download as plain text

### API Endpoints
- `GET /extractions` - List all
- `GET /extractions/{file_id}` - Get details
- `GET /extractions/{file_id}/text` - Download text
- `DELETE /extractions/{file_id}` - Delete

## Data Storage

Each upload creates two files in `data/extracted_metadata/`:
1. `{file_id}.json` - Complete metadata
2. `{file_id}.txt` - Plain text for easy viewing

## Testing

1. Upload a document via the Upload page
2. Go to Extractions page
3. You should see your uploaded document
4. Click "View" to see full details
5. Click "Download" to get the text file
6. Click "Delete" to remove it

## Next Steps

The system is ready to use! Every document you upload will automatically:
1. Be processed through OCR
2. Have metadata extracted and saved
3. Appear in the Extractions page
4. Be available for download as text
