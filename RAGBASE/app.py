from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import asyncio
import random

from ragbase.chain import ask_question, create_chain
from ragbase.config import Config
from ragbase.ingestor import Ingestor
from ragbase.model import create_llm
from ragbase.retriever import create_retriever
from ragbase.uploader import upload_files

load_dotenv()

app = FastAPI()

# CORS middleware for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize variables
LOADING_MESSAGES = [
    "Calculating your answer through multiverse...",
    "Adjusting quantum entanglement...",
    "Summoning star wisdom... almost there!",
    "Consulting Schrödinger's cat...",
    "Warping spacetime for your response...",
    "Balancing neutron star equations...",
    "Analyzing dark matter... please wait...",
    "Engaging hyperdrive... en route!",
    "Gathering photons from a galaxy...",
    "Beaming data from Andromeda... stand by!",
]

qa_chain = None
session_messages = [
    {"role": "assistant", "content": "Hi! What do you want to know about your documents?"}
]


# Function to build the QA chain
def build_qa_chain(files):
    try:
        file_paths = upload_files(files)

        vector_store = Ingestor().ingest(file_paths)
        llm = create_llm()
        retriever = create_retriever(llm, vector_store=vector_store)

        return create_chain(llm, retriever)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building QA chain: {e}")


# API for uploading documents
@app.post("/upload_documents/")
async def upload_documents(files: List[UploadFile] = File(...)):
    global qa_chain
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    try:
        qa_chain = build_qa_chain(files)
        return {"message": "Documents uploaded and QA chain initialized successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Request model for asking questions
class QuestionRequest(BaseModel):
    question: str


# API for asking a question
@app.post("/ask_question/")
async def ask_question_api(request: QuestionRequest):
    global qa_chain
    if qa_chain is None:
        raise HTTPException(status_code=400, detail="QA chain is not initialized. Please upload files first.")

    question = request.question
    full_response = ""
    documents = []
    try:
        async for event in ask_question(qa_chain, question, session_id="session-id-42"):
            if isinstance(event, str):
                full_response += event
            elif isinstance(event, list):
                documents.extend(event)

        # Add the assistant's response to session messages
        session_messages.append({"role": "assistant", "content": full_response})
        return {
            "response": full_response,
            "sources": [{"source": doc.page_content} for doc in documents],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during question answering: {str(e)}")


# API for fetching conversation history
@app.get("/conversation_history/")
async def get_conversation_history():
    return {"messages": session_messages}
    

# API for resetting conversation history
@app.post("/reset_conversation/")
async def reset_conversation():
    global session_messages
    session_messages = [
        {"role": "assistant", "content": "Hi! What do you want to know about your documents?"}
    ]
    return {"message": "Conversation history reset successfully."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)