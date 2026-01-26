import os
import pdfplumber
import sys

# Set encoding to utf-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

def extract_text_from_pdf(pdf_path, output_path, max_pages=None):
    """
    Extracts text from a PDF file and saves it to a text file.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return

    print(f"Extracting text from: {pdf_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            with open(output_path, "w", encoding="utf-8") as f:
                total_pages = len(pdf.pages)
                pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
                
                print(f"Processing {pages_to_process} pages...")
                
                for i in range(pages_to_process):
                    page = pdf.pages[i]
                    text = page.extract_text()
                    
                    # Write header for each page for citation
                    f.write(f"\n\n### Page {i+1} ###\n\n")
                    
                    if text:
                        f.write(text)
                    else:
                        f.write("[No text extracted]")
                        
            print(f"Extraction complete. Saved to {output_path}")
            
    except ImportError:
        print("Error: pdfplumber is not installed. Please install it using: pip install pdfplumber")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    books_dir = os.path.join(base_dir, "books")
    temp_dir = os.path.join(base_dir, "temp")
    
    # Target specific book for Step 0-3 rules
    # This book is foundational and likely contains the basic rules
    target_book = "简体《子平基础概要》梁湘润（216页）.pdf" 
    pdf_path = os.path.join(books_dir, target_book)
    output_path = os.path.join(temp_dir, "rules_source_ziping.txt")
    
    extract_text_from_pdf(pdf_path, output_path, max_pages=216)
