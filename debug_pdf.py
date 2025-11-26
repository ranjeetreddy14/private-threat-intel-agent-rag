from pypdf import PdfReader
import os

def check_pdf(filename):
    path = os.path.join("data", filename)
    try:
        reader = PdfReader(path)
        print(f"--- Checking {filename} ---")
        print(f"Total Pages: {len(reader.pages)}")
        
        text = ""
        for i, page in enumerate(reader.pages[:3]): # Check first 3 pages
            extracted = page.extract_text()
            print(f"\n[Page {i+1}] Length: {len(extracted)}")
            print(f"Content Preview: {extracted[:200]}...")
            text += extracted
            
        if len(text.strip()) < 50:
            print("\n[WARNING] Very little text extracted. This might be a scanned PDF (image-only).")
        else:
            print("\n[SUCCESS] Text extraction seems to work.")
            
    except Exception as e:
        print(f"[ERROR] Failed to read PDF: {e}")

if __name__ == "__main__":
    # List PDFs in data folder
    pdfs = [f for f in os.listdir("data") if f.endswith(".pdf")]
    if not pdfs:
        print("No PDFs found in data/")
    else:
        for pdf in pdfs:
            check_pdf(pdf)
