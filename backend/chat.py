import json
import faiss
import time
import re
import os

from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from google import genai


# -------------------------------------------------
# Load API key
# -------------------------------------------------

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# -------------------------------------------------
# Load FAISS index
# -------------------------------------------------

index = faiss.read_index("vector.index")


# -------------------------------------------------
# Load chunks
# -------------------------------------------------

with open("chunk_metadata.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)


# -------------------------------------------------
# Load embedding model
# -------------------------------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")


# -------------------------------------------------
# Retrieve relevant chunks
# -------------------------------------------------

def retrieve(query, k=5):

    query_lower = query.lower()

    # -------------------------------------------------
    # Check for explicit page number
    # -------------------------------------------------

    page_match = re.search(
        r'\bpage\s+(\d+)\b',
        query_lower
    )

    if page_match:

        page_number = int(page_match.group(1))

        page_results = [
            {
                "score": 1.0,
                "text": chunk["text"],
                "pdf": chunk["pdf"],
                "page": chunk["page"],
                "has_images": chunk["has_images"]
            }
            for chunk in chunks
            if chunk["page"] == page_number
        ]

        if page_results:
            return page_results

    # -------------------------------------------------
    # Semantic search
    # -------------------------------------------------

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    # Retrieve more candidates before re-ranking
    scores, indices = index.search(
        query_embedding,
        10
    )

    # -------------------------------------------------
    # Extract important query words
    # -------------------------------------------------

    query_words = set(
        re.findall(r'\b[a-zA-Z0-9]+\b', query_lower)
    )

    stop_words = {
        "the", "is", "was", "were", "in",
        "on", "of", "to", "a", "an",
        "what", "which", "how", "many",
        "tell", "me", "about"
    }

    query_words -= stop_words

    # Find years in the query
    years = re.findall(
        r'\b(?:19|20)\d{2}\b',
        query_lower
    )

    # -------------------------------------------------
    # Re-score retrieved results
    # -------------------------------------------------

    rescored = []

    for score, idx in zip(scores[0], indices[0]):

        chunk = chunks[idx]

        text_lower = chunk["text"].lower()

        final_score = float(score)

        # -------------------------------------------------
        # Keyword matching
        # -------------------------------------------------

        keyword_matches = sum(
            1
            for word in query_words
            if word in text_lower
        )

        final_score += keyword_matches * 0.03

        # -------------------------------------------------
        # Year matching
        # -------------------------------------------------

        for year in years:

            if year in text_lower:
                final_score += 0.15

        # -------------------------------------------------
        # Coal / Non-coal distinction
        # -------------------------------------------------

        if "non-coal" in query_lower:

            if "non-coal" in text_lower:
                final_score += 0.30

            elif chunk["pdf"].endswith("pdf2.pdf"):
                final_score += 0.20

        elif "coal" in query_lower:

            if chunk["pdf"].endswith("pdf1.pdf"):
                final_score += 0.30

            # Penalize non-coal results
            if "non-coal" in text_lower:
                final_score -= 0.20

        # -------------------------------------------------
        # Store result
        # -------------------------------------------------

        rescored.append({
            "score": final_score,
            "text": chunk["text"],
            "pdf": chunk["pdf"],
            "page": chunk["page"],
            "has_images": chunk["has_images"]
        })

    # -------------------------------------------------
    # Sort by final score
    # -------------------------------------------------

    rescored.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return rescored[:k]


# -------------------------------------------------
# Create image path for a PDF page
# -------------------------------------------------

def get_page_image_path(pdf_path, page_number):

    pdf_name = os.path.splitext(
        os.path.basename(pdf_path)
    )[0]

    image_path = (
        f"data/pages/"
        f"{pdf_name}_page_{page_number}.png"
    )

    if os.path.exists(image_path):
        return image_path

    return None


# -------------------------------------------------
# Answer question
# -------------------------------------------------

def answer_question(query):

    results = retrieve(query)

    # -------------------------------------------------
    # DEBUG: Show retrieved pages
    # -------------------------------------------------

    print("\n--- RETRIEVED PAGES ---")

    for result in results:

        print(
            f"{result['pdf']} | "
            f"Page {result['page']} | "
            f"Score {result['score']:.4f} | "
            f"Has image: {result['has_images']}"
        )

    print("-----------------------")

    # -------------------------------------------------
    # Build text context
    # -------------------------------------------------

    context = ""

    for result in results:

        context += f"""
Source: {result['pdf']}
Page: {result['page']}

{result['text']}

--------------------
"""

    # -------------------------------------------------
    # Prepare Gemini content
    # -------------------------------------------------

    contents = []

    prompt = f"""
You are a document-based chatbot.

Answer the user's question using ONLY the information provided
from the PDF documents below, including the extracted text and
the supplied page images.

Follow these rules:

1. If the answer is explicitly stated in the provided documents,
   provide it directly.

2. If the answer is not explicitly stated but can be calculated,
   compared, summarized, or reasonably inferred from information
   in the provided documents, you may derive the answer.
   Clearly explain the calculation or reasoning when useful.

3. Use the provided documents as the primary source.
   If the documents do not contain enough information to answer
   the question, you may use relevant web search information
   to supplement the answer.

4. When using web search:
   - Prefer reliable and authoritative sources.
   - Clearly distinguish information obtained from the PDFs
     from information obtained through web search.
   - Do not present web-sourced information as if it came
     from the provided documents.

5. If neither the provided documents nor relevant web sources
   contain enough information to answer the question, say:

   "I could not find enough information to answer this question
   in the provided documents or reliable web sources."

6. When page images are provided, use them to understand
   graphs, charts, tables, figures, labels, and other visual
   information that may not be completely represented in the
   extracted text.

7. If the question refers to a specific page, figure, table,
   graph, or chart, pay particular attention to the corresponding
   retrieved page.

8. Keep the answer concise and directly answer the question.

9. At the end, provide the relevant PDF name and page number(s)
   used for the answer.

10. If web search was used, also provide the relevant web source
    names or links used for the answer.
    
User question:
{query}

Retrieved document content:

{context}
"""

    contents.append(prompt)

    # -------------------------------------------------
    # Add relevant page images
    # -------------------------------------------------

    added_images = set()

    for result in results:

        if not result["has_images"]:
            continue

        image_path = get_page_image_path(
            result["pdf"],
            result["page"]
        )

        if image_path is None:
            continue

        # Avoid sending the same image twice
        if image_path in added_images:
            continue

        added_images.add(image_path)

        with open(image_path, "rb") as image_file:

            contents.append(
                genai.types.Part.from_bytes(
                    data=image_file.read(),
                    mime_type="image/png"
                )
            )

    # -------------------------------------------------
    # Send request to Gemini
    # -------------------------------------------------

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=contents
            )

            return response.text

        except Exception as e:

            print(
                f"\nGemini request failed "
                f"(attempt {attempt + 1}/3)"
            )

            if attempt < 2:

                print("Retrying in 5 seconds...")
                time.sleep(5)

            else:

                print("Error:", e)

                return (
                    "Gemini is temporarily unavailable. "
                    "Please try again later."
                )


# -------------------------------------------------
# Chat loop
# -------------------------------------------------

if __name__ == "__main__":

    while True:

        query = input(
            "\nAsk a question (or type 'exit'): "
        )

        if query.lower() == "exit":
            break

        answer = answer_question(query)

        print("\nANSWER:")
        print(answer)