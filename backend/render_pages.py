import pymupdf
import os


os.makedirs("data/pages", exist_ok=True)


def render_pdf(pdf_path, pdf_name):

    doc = pymupdf.open(pdf_path)

    for page_num, page in enumerate(doc):

        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(2, 2)
        )

        output_path = (
            f"data/pages/{pdf_name}_page_{page_num + 1}.png"
        )

        pix.save(output_path)

    print(f"Finished rendering {pdf_name}")


render_pdf("data/pdf1.pdf", "pdf1")
render_pdf("data/pdf2.pdf", "pdf2")

print("All pages rendered.")