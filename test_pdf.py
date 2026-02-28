#!/usr/bin/env python3
"""
Test PDF processing on a single file
Usage: python3 test_pdf.py <path_to_pdf>
"""

import sys
import os
import fitz
from PIL import Image
import re

def analyze_pdf(pdf_path):
    """Analyze PDF structure and extract questions"""
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"Analyzing: {os.path.basename(pdf_path)}")
    print(f"{'='*60}\n")
    
    try:
        doc = fitz.open(pdf_path)
        
        print(f"Total pages: {len(doc)}")
        print(f"{'='*60}\n")
        
        for page_num in range(min(3, len(doc))):  # Analyze first 3 pages
            print(f"Page {page_num + 1}:")
            print("-" * 60)
            
            page = doc[page_num]
            
            # Extract text
            text = page.get_text()
            
            # Find question numbers
            pattern = r'^(\d+)\s+'
            questions = []
            
            for match in re.finditer(pattern, text, re.MULTILINE):
                q_num = match.group(1)
                pos = match.start()
                
                # Get context (20 chars after)
                context = text[pos:pos+50].replace('\n', ' ')
                questions.append((q_num, context))
            
            if questions:
                print(f"Found {len(questions)} questions:")
                for q_num, context in questions:
                    print(f"  Q{q_num}: {context}...")
            else:
                print("  No questions detected")
            
            # Show text blocks
            blocks = page.get_text("blocks")
            print(f"\nText blocks: {len(blocks)}")
            
            for i, block in enumerate(blocks[:5]):  # First 5 blocks
                x0, y0, x1, y1, text_content, block_no, block_type = block
                preview = text_content.strip()[:50].replace('\n', ' ')
                print(f"  Block {i+1} @ y={int(y0)}: {preview}...")
            
            print()
        
        doc.close()
        
        print(f"{'='*60}")
        print("Analysis complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_pdf.py <path_to_pdf>")
        print("\nExample:")
        print("  python3 test_pdf.py data/pdfs/9702_s24_qp_42.pdf")
        return 1
    
    pdf_path = sys.argv[1]
    analyze_pdf(pdf_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
