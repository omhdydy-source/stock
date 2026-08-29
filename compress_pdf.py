import pymupdf as fitz
import sys
import os

input_path = r"C:\Users\omh\Documents\카카오톡 받은 파일\강다호_주민등록초본_20260828.pdf"
output_path = r"C:\Users\omh\Documents\카카오톡 받은 파일\강다호_주민등록초본_20260828_compressed.pdf"
work_dir = r"C:\Users\omh\Desktop\stock"

doc = fitz.open(input_path)
new_doc = fitz.open()

for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=150)
    img_path = os.path.join(work_dir, f"page_{i}.jpg")
    pix.save(img_path)
    
    img_doc = fitz.open(img_path)
    pdf_bytes = img_doc.convert_to_pdf()
    img_pdf = fitz.open("pdf", pdf_bytes)
    new_doc.insert_pdf(img_pdf)
    img_doc.close()
    
    if os.path.exists(img_path):
        os.remove(img_path)

new_doc.save(output_path)
new_doc.close()
doc.close()

print(f"Original size: {os.path.getsize(input_path) / (1024*1024):.2f} MB")
print(f"Compressed size: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
