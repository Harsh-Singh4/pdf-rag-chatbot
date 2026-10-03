import json
import faiss
import re

from sentence_transformers import SentenceTransformer


# -------------------------------------------------
# Load FAISS index
# -------------------------------------------------

index = faiss.read_index("vector.index")


# -------------------------------------------------
# Load chunk metadata
# -------------------------------------------------

with open("chunk_metadata.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)


# -------------------------------------------------
# Load embedding model
# -------------------------------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")


# -------------------------------------------------
# Keyword matching
# -------------------------------------------------

def keyword_score(query, text):

    query_words = set(
        re.findall(r"\b[a-zA-Z0-9]+\b", query.lower())
    )

    text_words = set(
        re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    )

    if not query_words:
        return 0

    matches = query_words.intersection(text_words)

    return len(matches) / len(query_words)


# -------------------------------------------------
# Hybrid retrieval
# -------------------------------------------------

def search(query, k=5):

    # ---------------------------------------------
    # Semantic search
    # ---------------------------------------------

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    semantic_scores, indices = index.search(
        query_embedding,
        10
    )


    # ---------------------------------------------
    # Collect candidates
    # ---------------------------------------------

    candidates = {}

    for score, idx in zip(
        semantic_scores[0],
        indices[0]
    ):

        candidates[idx] = {
            "semantic_score": float(score),
            "keyword_score": keyword_score(
                query,
                chunks[idx]["text"]
            )
        }


    # ---------------------------------------------
    # Keyword search over all chunks
    # ---------------------------------------------

    for idx, chunk in enumerate(chunks):

        score = keyword_score(
            query,
            chunk["text"]
        )

        if score > 0:

            if idx not in candidates:

                candidates[idx] = {
                    "semantic_score": 0,
                    "keyword_score": score
                }

            else:

                candidates[idx]["keyword_score"] = score


    # ---------------------------------------------
    # Combine scores
    # ---------------------------------------------

    results = []

    for idx, scores in candidates.items():

        combined_score = (
            0.7 * scores["semantic_score"]
            +
            0.3 * scores["keyword_score"]
        )

        results.append({
            "score": combined_score,
            "semantic_score": scores["semantic_score"],
            "keyword_score": scores["keyword_score"],
            "text": chunks[idx]["text"],
            "pdf": chunks[idx]["pdf"],
            "page": chunks[idx]["page"],
            "has_images": chunks[idx]["has_images"]
        })


    # ---------------------------------------------
    # Sort by combined score
    # ---------------------------------------------

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    return results[:k]


# -------------------------------------------------
# Test
# -------------------------------------------------

if __name__ == "__main__":

    query = input("Enter your question: ")

    results = search(query)

    print("\n--- RESULTS ---")

    for result in results:

        print(
            f"{result['pdf']} | "
            f"Page {result['page']} | "
            f"Combined: {result['score']:.4f} | "
            f"Semantic: {result['semantic_score']:.4f} | "
            f"Keyword: {result['keyword_score']:.4f}"
        )