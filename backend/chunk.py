import json


# Load extracted pages
with open("pages.json", "r", encoding="utf-8") as f:
    pages = json.load(f)


def create_chunks(pages, words_per_chunk=1500, overlap=200):

    chunks = []

    for page in pages:

        text = page["text"]

        # Skip pages with no text
        if not text:
            continue

        words = text.split()

        start = 0

        while start < len(words):

            end = start + words_per_chunk

            chunk_words = words[start:end]

            chunk_text = " ".join(chunk_words)

            chunks.append({
                "text": chunk_text,
                "pdf": page["pdf"],
                "page": page["page"],
                "has_images": page["has_images"]
            })

            start += words_per_chunk - overlap

    return chunks


chunks = create_chunks(pages)


# Save chunks
with open("chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)


print("Total pages:", len(pages))
print("Total chunks:", len(chunks))

print("\nFirst chunk:")
print(chunks[0])