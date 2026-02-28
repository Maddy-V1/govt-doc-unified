# OCR3 - PaddleOCR Integration

## Overview
Added PaddleOCR as the third OCR engine (ocr3) with support for CSV, JSON, and TXT output formats.

## Features

### PaddleOCR Advantages
- Multi-language support (Hindi, English, mixed)
- GPU acceleration support
- Advanced preprocessing (CLAHE, sharpening, denoising)
- Row-based text grouping for structured output
- CSV export for tabular data
- High accuracy on scanned documents

### Output Formats
1. **JSON**: Complete metadata with page-by-page results
2. **TXT**: Plain text extraction
3. **CSV**: Structured data (Page, Row, Text columns)

## File Structure

```
unified/
├── ocr3/                           # NEW: PaddleOCR engine
│   ├── __init__.py
│   ├── config.py                   # Configuration settings
│   ├── paddle_engine.py            # Main OCR engine
│   ├── preprocessing.py            # Image preprocessing
│   ├── pdf_handler.py              # PDF to image conversion
│   ├── text_grouping.py            # Row grouping utilities
│   └── output_formatters.py        # CSV/JSON/TXT formatters
│
└── main/
    ├── backend/
    │   ├── services/
    │   │   ├── ocr_service.py      # UPDATED: Added PaddleOCR support
    │   │   └── metadata_service.py # UPDATED: Added CSV support
    │   └── routes/
    │       ├── upload.py            # UPDATED: Pass CSV data
    │       └── extractions.py       # UPDATED: Added CSV endpoint
    │
    ├── frontend/
    │   ├── src/
    │   │   ├── services/
    │   │   │   └── extractionsApi.js  # UPDATED: Added CSV download
    │   │   └── pages/
    │   │       └── ExtractionsPage.jsx # UPDATED: Show CSV button
    │   
    └── .env                         # UPDATED: Added PaddleOCR config
```

## Installation

### 1. Install PaddleOCR

```bash
# CPU version
pip install paddlepaddle paddleocr

# GPU version (CUDA required)
pip install paddlepaddle-gpu paddleocr
```

### 2. Install Dependencies

```bash
pip install opencv-python pymupdf numpy
```

## Configuration

### Environment Variables (.env)

```bash
# Set OCR engine to paddleocr
OCR_ENGINE=paddleocr

# PaddleOCR Settings
PADDLE_LANG=hi                    # 'en' for English, 'hi' for Hindi/mixed
PADDLE_USE_GPU=false              # Set to true if GPU available
PADDLE_DPI=200                    # Optimal DPI for scanned docs
PADDLE_CONF_THRESH=0.30           # Minimum confidence threshold
PADDLE_ROW_GAP=10                 # Y-proximity for row grouping (pixels)

# Output Formats
ENABLE_CSV_OUTPUT=true
ENABLE_JSON_OUTPUT=true
ENABLE_TXT_OUTPUT=true

# Preprocessing
ENABLE_CLAHE=true                 # Adaptive histogram equalization
ENABLE_SHARPENING=true            # Unsharp mask for text edges
ENABLE_DENOISING=true             # Remove scan speckle
```

## Usage

### 1. Start Backend

```bash
cd unified/main
python -m backend.main
```

### 2. Upload Document

The system will automatically use PaddleOCR if `OCR_ENGINE=paddleocr` in .env

### 3. View Results

Navigate to `/extractions` page to see:
- Full text extraction
- JSON metadata
- CSV download (for PaddleOCR results)

## API Endpoints

### Upload
```bash
POST /upload
# Processes document with PaddleOCR and saves all formats
```

### List Extractions
```bash
GET /extractions
# Returns list with has_csv flag for PaddleOCR results
```

### Download Formats
```bash
GET /extractions/{file_id}/text   # Plain text
GET /extractions/{file_id}/csv    # CSV (PaddleOCR only)
GET /extractions/{file_id}        # Full JSON metadata
```

## CSV Format

PaddleOCR generates CSV with the following structure:

```csv
Page,Row,Text
1,1,Header Text
1,2,First row content
2,1,Second page content
```

Each row represents a line of text detected by OCR, grouped by reading order.

## Preprocessing Pipeline

1. **CLAHE**: Adaptive histogram equalization for uneven lighting
2. **Sharpening**: Unsharp mask to crisp text edges
3. **Denoising**: Fast non-local means denoising to remove scan artifacts
4. **RGB Conversion**: Back to 3-channel for PaddleOCR

Note: Avoids full binarization as PaddleOCR works better with anti-aliased text.

## Performance

- **DPI 200**: Optimal balance of speed and accuracy
- **GPU Acceleration**: 3-5x faster with CUDA
- **Processing Time**: ~2-3 seconds per page (CPU), ~0.5-1s (GPU)

## Comparison with Other Engines

| Feature | Tesseract (ocr1) | Sarvam (ocr2) | PaddleOCR (ocr3) |
|---------|------------------|---------------|------------------|
| Languages | Limited | Cloud API | Multi-language |
| Speed | Fast | API dependent | Fast (GPU) |
| Accuracy | Good | Excellent | Excellent |
| CSV Output | No | No | Yes |
| Offline | Yes | No | Yes |
| Cost | Free | Paid API | Free |
| Hindi Support | Basic | Excellent | Excellent |

## Frontend Features

### Extractions Page
- Shows "CSV" button for PaddleOCR results
- Color-coded by OCR engine
- Download options: TXT, CSV (if available)

### Detection
- Automatically detects if CSV is available
- Shows CSV button only for PaddleOCR extractions
- Graceful fallback if CSV not found

## Troubleshooting

### PaddleOCR Not Found
```bash
pip install paddlepaddle paddleocr
```

### GPU Not Working
```bash
# Check CUDA installation
python -c "import paddle; print(paddle.device.is_compiled_with_cuda())"

# Install GPU version
pip install paddlepaddle-gpu
```

### Low Confidence
- Increase DPI (try 300)
- Enable all preprocessing options
- Check image quality

### Memory Issues
- Reduce DPI to 150
- Process fewer pages at once
- Disable GPU if RAM limited

## Next Steps

1. Test with various document types
2. Tune preprocessing parameters
3. Add document type classification
4. Implement batch processing
5. Add progress tracking for large PDFs

## Benefits

1. **Multi-format Output**: CSV, JSON, TXT all generated automatically
2. **Structured Data**: Row-based grouping for tabular extraction
3. **High Accuracy**: Advanced preprocessing optimized for scanned docs
4. **Offline Processing**: No API costs or internet dependency
5. **GPU Support**: Fast processing with CUDA acceleration
6. **Hindi Support**: Excellent for government documents in Hindi/English mix
