import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# Load chunks
with open("chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)


# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


# Extract text
texts = [chunk["text"] for chunk in chunks]


# Convert text → embeddings
embeddings = model.encode(
    texts,
    normalize_embeddings=True,
    show_progress_bar=True
)


# Convert to numpy float32
embeddings = np.array(embeddings).astype("float32")


# Create FAISS index
dimension = embeddings.shape[1]

index = faiss.IndexFlatIP(dimension)

index.add(embeddings)


# Save FAISS index
faiss.write_index(index, "vector.index")


# Save chunk metadata
with open("chunk_metadata.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)


print("Number of chunks:", len(chunks))
print("Embedding dimension:", dimension)
print("FAISS index size:", index.ntotal)