# OCR3 - PaddleOCR Engine

Multi-language OCR engine with CSV, JSON, and TXT output support.

## Features

- Multi-language support (Hindi, English, mixed scripts)
- GPU acceleration (optional)
- Advanced image preprocessing
- Row-based text grouping
- Multiple output formats (CSV, JSON, TXT)
- Optimized for scanned government documents

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# For GPU support (requires CUDA)
pip uninstall paddlepaddle
pip install paddlepaddle-gpu
```

## Quick Test

```bash
# Test on a PDF
python test_paddle.py /path/to/document.pdf

# Test on an image
python test_paddle.py /path/to/image.jpg
```

## Configuration

Edit `config.py` or set environment variables:

```python
PADDLE_LANG = "hi"           # Language: 'en', 'hi', etc.
PADDLE_USE_GPU = False       # Enable GPU acceleration
PADDLE_DPI = 200             # Rendering DPI
PADDLE_CONF_THRESH = 0.30    # Confidence threshold
PADDLE_ROW_GAP = 10          # Row grouping gap (pixels)
```

## Usage

### Basic Usage

```python
from ocr3 import PaddleOCREngine, OutputFormatter

# Initialize engine
engine = PaddleOCREngine()

# Process file
result = engine.process_file("document.pdf")

# Save outputs
OutputFormatter.save_all_formats(result, "output/document")
# Creates: document.txt, document.json, document.csv
```

### Process Single Image

```python
import cv2
from ocr3 import PaddleOCREngine

engine = PaddleOCREngine()
image = cv2.imread("image.jpg")
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

result = engine.process_image(image)
print(result['text'])
```

### Custom Output

```python
from ocr3 import OutputFormatter

# Save only specific formats
OutputFormatter.save_all_formats(
    result,
    "output/document",
    formats=['txt', 'csv']  # Only TXT and CSV
)
```

## Output Formats

### JSON
Complete metadata with page-by-page results:
```json
{
  "ocr_engine": "paddleocr",
  "total_pages": 5,
  "confidence": 0.92,
  "word_count": 1234,
  "full_text": "...",
  "pages": [...]
}
```

### TXT
Plain text extraction with page separators

### CSV
Structured data:
```csv
Page,Row,Text
1,1,Header text
1,2,First row
2,1,Second page
```

## Preprocessing

The engine applies:
1. **CLAHE**: Adaptive histogram equalization
2. **Sharpening**: Unsharp mask for text edges
3. **Denoising**: Fast non-local means denoising

Configure in `config.py`:
```python
ENABLE_CLAHE = True
ENABLE_SHARPENING = True
ENABLE_DENOISING = True
```

## Performance Tips

### Speed
- Use GPU: Set `PADDLE_USE_GPU=True`
- Lower DPI: Try 150 instead of 200
- Disable preprocessing: Set to False in config

### Accuracy
- Increase DPI: Try 300 for small text
- Enable all preprocessing
- Adjust confidence threshold

### Memory
- Process pages in batches
- Lower DPI
- Disable GPU if RAM limited

## Integration with Main System

The engine is integrated into the unified system:

```python
# In main/backend/services/ocr_service.py
from ocr3.paddle_engine import PaddleOCREngine

# Set in .env
OCR_ENGINE=paddleocr
```

Results are automatically saved with CSV support.

## Troubleshooting

### Import Error
```bash
pip install paddlepaddle paddleocr
```

### GPU Not Detected
```bash
python -c "import paddle; print(paddle.device.is_compiled_with_cuda())"
```

### Low Confidence
- Check image quality
- Increase DPI
- Enable preprocessing

### Memory Error
- Reduce DPI
- Process fewer pages
- Use CPU instead of GPU

## File Structure

```
ocr3/
├── __init__.py              # Package exports
├── config.py                # Configuration
├── paddle_engine.py         # Main OCR engine
├── preprocessing.py         # Image preprocessing
├── pdf_handler.py           # PDF utilities
├── text_grouping.py         # Row grouping
├── output_formatters.py     # Format converters
├── requirements.txt         # Dependencies
├── test_paddle.py           # Test script
└── README.md               # This file
```

## License

Same as parent project
