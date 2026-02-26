#!/usr/bin/env python3
"""
Setup Verification Script
Run this to check if your system is ready to run.
"""

import sys
import subprocess
from pathlib import Path
import os

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def check_command(cmd, name):
    """Check if a command exists"""
    try:
        result = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ {name}: {version}")
            return True
        else:
            print(f"❌ {name}: Not found or error")
            return False
    except FileNotFoundError:
        print(f"❌ {name}: Not installed")
        return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def check_python_package(package, name=None):
    """Check if a Python package is installed"""
    if name is None:
        name = package
    try:
        __import__(package)
        print(f"✅ {name}: Installed")
        return True
    except ImportError:
        print(f"❌ {name}: Not installed")
        return False

def check_file(path, name):
    """Check if a file exists"""
    if Path(path).exists():
        size = Path(path).stat().st_size
        size_mb = size / (1024 * 1024)
        print(f"✅ {name}: Found ({size_mb:.1f} MB)")
        return True
    else:
        print(f"❌ {name}: Not found at {path}")
        return False

def check_directory(path, name):
    """Check if a directory exists"""
    if Path(path).is_dir():
        print(f"✅ {name}: Exists")
        return True
    else:
        print(f"❌ {name}: Not found")
        return False

def main():
    print_header("System Verification for Unified Document Intelligence")
    
    issues = []
    
    # Check system commands
    print_header("System Commands")
    if not check_command("python3", "Python 3"):
        issues.append("Python 3 not found")
    if not check_command("node", "Node.js"):
        issues.append("Node.js not found")
    if not check_command("tesseract", "Tesseract OCR"):
        issues.append("Tesseract not found (required if OCR_ENGINE=tesseract)")
    if not check_command("pdfinfo", "Poppler"):
        issues.append("Poppler not found (required for PDF processing)")
    
    # Check Python packages
    print_header("Python Packages")
    packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pytesseract", "PyTesseract"),
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
        ("pdf2image", "pdf2image"),
        ("faiss", "FAISS"),
        ("sentence_transformers", "SentenceTransformers"),
        ("llama_cpp", "llama-cpp-python"),
        ("spacy", "SpaCy"),
    ]
    
    for package, name in packages:
        if not check_python_package(package, name):
            issues.append(f"{name} not installed")
    
    # Check SpaCy model
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print(f"✅ SpaCy Model (en_core_web_sm): Loaded")
    except:
        print(f"❌ SpaCy Model (en_core_web_sm): Not found")
        issues.append("SpaCy model not downloaded")
    
    # Check project structure
    print_header("Project Structure")
    base_dir = Path(__file__).parent
    
    dirs_to_check = [
        ("backend", "Backend directory"),
        ("frontend", "Frontend directory"),
        ("data", "Data directory"),
        ("uploads", "Uploads directory"),
        ("vector_db", "Vector DB directory"),
    ]
    
    for dir_name, desc in dirs_to_check:
        check_directory(base_dir / dir_name, desc)
    
    # Check important files
    print_header("Configuration Files")
    files_to_check = [
        (".env", "Environment file"),
        ("backend/main.py", "Backend main file"),
        ("backend/requirements.txt", "Requirements file"),
        ("frontend/package.json", "Frontend package.json"),
    ]
    
    for file_name, desc in files_to_check:
        if not check_file(base_dir / file_name, desc):
            issues.append(f"{desc} not found")
    
    # Check .env configuration
    print_header("Environment Configuration")
    env_file = base_dir / ".env"
    if env_file.exists():
        with open(env_file) as f:
            env_content = f.read()
            
        # Check OCR_ENGINE
        if "OCR_ENGINE=" in env_content:
            for line in env_content.split('\n'):
                if line.startswith("OCR_ENGINE="):
                    engine = line.split('=')[1].strip()
                    print(f"✅ OCR Engine: {engine}")
                    break
        else:
            print(f"⚠️  OCR_ENGINE not set in .env")
        
        # Check LLM_MODEL_PATH
        if "LLM_MODEL_PATH=" in env_content:
            for line in env_content.split('\n'):
                if line.startswith("LLM_MODEL_PATH="):
                    model_path = line.split('=')[1].strip()
                    full_path = base_dir / model_path
                    if full_path.exists():
                        size_mb = full_path.stat().st_size / (1024 * 1024)
                        print(f"✅ LLM Model: Found ({size_mb:.1f} MB)")
                    else:
                        print(f"❌ LLM Model: Not found at {full_path}")
                        issues.append("LLM model file not found")
                    break
        else:
            print(f"⚠️  LLM_MODEL_PATH not set in .env")
    
    # Check Node modules
    print_header("Frontend Dependencies")
    node_modules = base_dir / "frontend" / "node_modules"
    if node_modules.exists():
        print(f"✅ Node modules: Installed")
    else:
        print(f"❌ Node modules: Not installed (run 'npm install' in frontend/)")
        issues.append("Node modules not installed")
    
    # Summary
    print_header("Summary")
    if issues:
        print(f"\n❌ Found {len(issues)} issue(s):\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print(f"\n📖 See SETUP.md for installation instructions")
        return 1
    else:
        print(f"\n✅ All checks passed! System is ready to run.")
        print(f"\n🚀 Next steps:")
        print(f"  1. Start backend: cd backend && python main.py")
        print(f"  2. Start frontend: cd frontend && npm run dev")
        print(f"  3. Open browser: http://localhost:5173")
        return 0

if __name__ == "__main__":
    sys.exit(main())
