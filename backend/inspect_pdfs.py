import fitz
import os

pdf_paths = [
    "data/pdf1.pdf",
    "data/pdf2.pdf"
]

for pdf_path in pdf_paths:

    doc = fitz.open(pdf_path)

    print("\n==========================")
    print(pdf_path)
    print("==========================")

    total_images = 0
    empty_text_pages = 0

    for page_number, page in enumerate(doc):

        text = page.get_text().strip()
        images = page.get_images(full=True)

        total_images += len(images)

        if not text:
            empty_text_pages += 1

        print(
            f"Page {page_number + 1}: "
            f"text_chars={len(text)}, "
            f"images={len(images)}"
        )

    print("\nTotal pages:", len(doc))
    print("Total images:", total_images)
    print("Pages with no extracted text:", empty_text_pages)