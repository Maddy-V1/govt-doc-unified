"""
Quick test script for PaddleOCR integration
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ocr3.paddle_engine import PaddleOCREngine
from ocr3.output_formatters import OutputFormatter


def test_paddleocr(file_path: str):
    """Test PaddleOCR on a file"""
    print(f"Testing PaddleOCR on: {file_path}")
    print("=" * 60)
    
    # Initialize engine
    print("\n1. Initializing PaddleOCR...")
    engine = PaddleOCREngine()
    
    # Process file
    print(f"\n2. Processing file...")
    result = engine.process_file(file_path)
    
    # Print results
    print(f"\n3. Results:")
    print(f"   Success: {result['success']}")
    print(f"   OCR Engine: {result['ocr_engine']}")
    print(f"   Total Pages: {result['total_pages']}")
    print(f"   Confidence: {result['confidence']:.2%}")
    print(f"   Word Count: {result['word_count']}")
    print(f"   Processing Time: {result['processing_time']:.2f}s")
    
    # Show first 500 characters of text
    print(f"\n4. Extracted Text (first 500 chars):")
    print("-" * 60)
    print(result['full_text'][:500])
    print("-" * 60)
    
    # Save outputs
    print(f"\n5. Saving outputs...")
    base_path = Path(file_path).stem
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    saved_files = OutputFormatter.save_all_formats(
        result,
        str(output_dir / base_path)
    )
    
    print(f"   Saved files:")
    for format_type, path in saved_files.items():
        print(f"   - {format_type.upper()}: {path}")
    
    print(f"\n✓ Test completed successfully!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_paddle.py <path_to_pdf_or_image>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    try:
        test_paddleocr(file_path)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
