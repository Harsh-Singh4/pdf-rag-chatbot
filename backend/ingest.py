import json
import pymupdf


def extract_pages(pdf_path):
    doc = pymupdf.open(pdf_path)

    pages = []

    for page_num, page in enumerate(doc):

        text = page.get_text("text").strip()
        images = page.get_images(full=True)

        pages.append({
            "pdf": pdf_path,
            "page": page_num + 1,
            "text": text,
            "has_images": len(images) > 0
        })

    return pages


pdf1 = extract_pages("data/pdf1.pdf")
pdf2 = extract_pages("data/pdf2.pdf")

pages = pdf1 + pdf2


# Save extracted pages
with open("pages.json", "w", encoding="utf-8") as f:
    json.dump(pages, f, ensure_ascii=False, indent=2)


print("Total pages:", len(pages))
print("Saved to pages.json")

text_pages = [p for p in pages if p["text"]]

print("Pages containing text:", len(text_pages))
print("Pages without text:", len(pages) - len(text_pages))