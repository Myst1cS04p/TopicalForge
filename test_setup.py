#!/usr/bin/env python3
"""
Quick test script to validate TopicalForge setup
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    modules = {
        "selenium": "selenium",
        "PIL": "Pillow",
        "fitz": "PyMuPDF",
        "watchdog": "watchdog"
    }
    
    failed = []
    
    for module, package in modules.items():
        try:
            if module == "PIL":
                import PIL
            elif module == "fitz":
                import fitz
            else:
                __import__(module)
            print(f"   {package}")
        except ImportError as e:
            print(f"    {package} - {e}")
            failed.append(package)
    
    return len(failed) == 0, failed

def test_chromedriver():
    """Test if ChromeDriver is available"""
    print("\nTesting ChromeDriver...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        driver.quit()
        print("    ChromeDriver working")
        return True
    except Exception as e:
        print(f"   ChromeDriver failed: {e}")
        return False

def test_directories():
    """Test if required directories exist"""
    print("\nTesting directory structure...")
    
    required_dirs = [
        "data/pdfs",
        "data/raw_questions", 
        "data/sorted_questions",
        "logs"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        exists = os.path.exists(dir_path)
        status = "GOOD" if exists else "MISSING"
        print(f"  {status} {dir_path}")
        all_exist = all_exist and exists
    
    return all_exist

def main():
    print("=" * 60)
    print("TopicalForge - Setup Validation")
    print("=" * 60)
    print()
    
    # Test imports
    imports_ok, failed_modules = test_imports()
    
    # Test ChromeDriver
    chrome_ok = test_chromedriver()
    
    # Test directories
    dirs_ok = test_directories()
    
    print()
    print("=" * 60)
    
    if imports_ok and chrome_ok and dirs_ok:
        print("All tests passed! TopicalForge is ready to use.")
        print()
        print("Run: python3 main.py")
        return 0
    else:
        print(" Some tests failed. Please fix the issues above.")
        print()
        if not imports_ok:
            print("Install missing modules:")
            print(f"  pip install {' '.join(failed_modules)} --break-system-packages")
        if not chrome_ok:
            print("Install ChromeDriver:")
            print("  sudo apt install chromium-chromedriver")
        if not dirs_ok:
            print("Create directories:")
            print("  mkdir -p data/pdfs data/raw_questions data/sorted_questions logs")
        return 1

if __name__ == "__main__":
    sys.exit(main())
