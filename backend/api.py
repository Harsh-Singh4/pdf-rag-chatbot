from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chat import answer_question


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "PDF RAG Chatbot API is running"
    }


@app.post("/ask")
def ask_question(data: dict):

    question = data.get("question", "").strip()

    if not question:
        return {
            "error": "Question cannot be empty"
        }

    answer = answer_question(question)

    return {
        "answer": answer
    }