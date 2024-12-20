# from fastapi import FastAPI, File, UploadFile
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# import shutil
# from pathlib import Path

# from dotenv import load_dotenv

# # Assuming ragbase modules are properly defined
# from ragbase.chain import ask_question, create_chain
# from ragbase.config import Config
# from ragbase.ingestor import Ingestor
# from ragbase.model import create_llm
# from ragbase.retriever import create_retriever
# from ragbase.uploader import upload_files

# load_dotenv()

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow all origins for testing; restrict in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# UPLOAD_DIR = Path("uploads")  # Use pathlib for path handling
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Ensure upload directory exists

# @app.post("/upload_pdf/")
# async def upload_pdf(files: list[UploadFile] = File(...)):
#     try:
#         uploaded_files = []
#         # Process and save each uploaded file
#         for file in files:
#             file_path = UPLOAD_DIR / file.filename  # Path to save the file
#             with open(file_path, "wb") as buffer:
#                 shutil.copyfileobj(file.file, buffer)  # Save the file content
            
#             # Read the file content as text (if the file is text-based)
#             file_content = ""
#             try:
#                 # For text-based files like PDFs or CSVs, you can try to decode to text
#                 file_content = file.file.read().decode('utf-8', errors='ignore')
#             except Exception as e:
#                 # Handle non-text files or binary files
#                 file_content = "Non-text file or binary content"

#             # Add the file information to the response
#             uploaded_files.append({
#                 "filename": file.filename,
#                 "content_type": file.content_type,
#                 "file_size": file.size,
#                 "file_content": file_content  # Store the file content as a string (if available)
#             })

#         # LLM related processing
#         file_paths = upload_files(files)
#         print("-------------->file: ", files)
#         vector_store = Ingestor().ingest(file_paths)
#         llm = create_llm()
#         retriever = create_retriever(llm, vector_store=vector_store)
#         create_chain(llm, retriever)
#         print("-------> files", files)

#         # Return the uploaded files details in the response
#         return JSONResponse(content={"uploaded_files": uploaded_files}, status_code=200)

#     except Exception as e:
#         return JSONResponse(content={"message": f"Error: {str(e)}"}, status_code=500)


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=5000)

# ------------------------------------------------>

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
        print("---------------> file_paths: ", file_paths)
        vector_store = Ingestor().ingest(file_paths)
        llm = create_llm()
        retriever = create_retriever(llm, vector_store=vector_store)
        print("---------------> retriever: ", retriever)
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


print("--------------->1 qa_chain",qa_chain)
# API for asking a question
@app.post("/ask_question/")
async def ask_question_api(request: QuestionRequest):
    global qa_chain
    print("--------------->2 qa_chain",qa_chain)
    if qa_chain is None:
        raise HTTPException(status_code=400, detail="QA chain is not initialized. Please upload files first.")

    question = request.question
    full_response = ""
    documents = []
    print("----------------++++++> question",question)
    try:
        async for event in ask_question(qa_chain, question, session_id="session-id-42"):
            if isinstance(event, str):
                full_response += event
            elif isinstance(event, list):
                documents.extend(event)

        # Add the assistant's response to session messages
        session_messages.append({"role": "assistant", "content": full_response})
        print("full response: ", full_response)
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


# ------------------------------------------------>

# from fastapi import FastAPI, File, UploadFile
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import shutil
# from pathlib import Path

# from dotenv import load_dotenv

# # Assuming ragbase modules are properly defined
# from ragbase.chain import ask_question, create_chain
# from ragbase.config import Config
# from ragbase.ingestor import Ingestor
# from ragbase.model import create_llm
# from ragbase.retriever import create_retriever
# from ragbase.uploader import upload_files

# load_dotenv()

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow all origins for testing; restrict in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# UPLOAD_DIR = Path("uploads")  # Use pathlib for path handling
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Ensure upload directory exists

# @app.post("/upload_pdf/")
# async def upload_pdf(files: list[UploadFile] = File(...)):
#     try:
#         uploaded_files = []
#         # Process and save each uploaded file
#         for file in files:
#             file_path = UPLOAD_DIR / file.filename  # Path to save the file
#             with open(file_path, "wb") as buffer:
#                 shutil.copyfileobj(file.file, buffer)  # Save the file content
            
#             # Read the file content as text (if the file is text-based)
#             file_content = ""
#             try:
#                 # For text-based files like PDFs or CSVs, you can try to decode to text
#                 file_content = file.file.read().decode('utf-8', errors='ignore')
#             except Exception as e:
#                 # Handle non-text files or binary files
#                 file_content = "Non-text file or binary content"

#             # Add the file information to the response
#             uploaded_files.append({
#                 "filename": file.filename,
#                 "content_type": file.content_type,
#                 "file_size": file.size,
#                 "file_content": file_content  # Store the file content as a string (if available)
#             })

#         build_qa_chain(files)
        

#         # Return the uploaded files details in the response
#         return JSONResponse(content={"uploaded_files": uploaded_files}, status_code=200)

#     except Exception as e:
#         # Handle any errors during the file upload or initial processing
#         print(f"Error during file upload: {str(e)}")
#         return JSONResponse(content={"message": f"Error during file upload: {str(e)}"}, status_code=500)
    
# #this is the CHAIN
# def build_qa_chain(files):
#     file_paths = upload_files(files)
#     print("-------------->file: ",files)
#     vector_store = Ingestor().ingest(file_paths)
#     llm = create_llm()
#     retriever = create_retriever(llm, vector_store=vector_store)
#     return create_chain(llm, retriever)


# # Request model for asking questions
# class QuestionRequest(BaseModel):
#     question: str

# @app.post("/ask_question/")
# async def ask_question_api(data: QuestionRequest):
#     try:
#         # Retrieve the question from the request
#         question = data.question
#         print(f"Received question: {question}")
#         response = question
#         # Return the generated response
#         return JSONResponse(content={"Question": response}, status_code=200)

#     except Exception as e:
#         # Handle any errors that occur
#         print(f"Error during question processing: {str(e)}")
#         return JSONResponse(content={"message": f"Error: {str(e)}"}, status_code=500)


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=5000)

# ------------------------------------------------>

# from fastapi import FastAPI, File, UploadFile, HTTPException, Form
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import List
# import asyncio
# import random
# from ragbase.chain import ask_question, create_chain
# from ragbase.config import Config
# from ragbase.ingestor import Ingestor
# from ragbase.model import create_llm
# from ragbase.retriever import create_retriever
# from ragbase.uploader import upload_files
# from langchain_community.chat_message_histories import ChatMessageHistory

# # Initialize FastAPI application
# app = FastAPI()

# # Enable CORS for frontend integration
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Chat message store
# store = {}

# # Helper functions
# LOADING_MESSAGES = [
#     "Calculating your answer through multiverse...",
#     "Adjusting quantum entanglement...",
#     "Summoning star wisdom... almost there!",
#     "Consulting Schrödinger's cat...",
#     "Warping spacetime for your response...",
#     "Balancing neutron star equations...",
#     "Analyzing dark matter... please wait...",
#     "Engaging hyperdrive... en route!",
#     "Gathering photons from a galaxy...",
#     "Beaming data from Andromeda... stand by!",
# ]

# def get_session_history(session_id: str) -> ChatMessageHistory:
#     if session_id not in store:
#         store[session_id] = ChatMessageHistory()
#     return store[session_id]

# @app.post("/upload")
# async def upload_documents(files: List[UploadFile] = File(...)):
#     try:
#         print("-------->vector_store")
#         file_paths = upload_files(files)
#         print("-------->>>>><<<<<file_paths",file_paths)
#         vector_store = Ingestor().ingest(file_paths)
#         llm = create_llm()
#         retriever = create_retriever(llm, vector_store=vector_store)
#         chain = create_chain(llm, retriever)
#         print("-------->chain", chain)
#         return {"message": "Files uploaded and chain created successfully", "chain": id(chain)}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error during upload: {str(e)}")

# class QuestionRequest(BaseModel):
#     session_id: str
#     question: str
#     chain_id: str

# @app.post("/ask")
# async def ask_question_api(request: QuestionRequest):
#     try:
#         chain = ... # Retrieve the chain object using `request.chain_id`
#         full_response = ""
#         documents = []
#         history = get_session_history(request.session_id)

#         history.add_user_message(request.question)
#         print("history",history)
#         async for event in ask_question(chain, request.question, session_id=request.session_id):
#             if isinstance(event, str):
#                 full_response += event
#             elif isinstance(event, list):
#                 documents.extend(event)

#         history.add_assistant_message(full_response)

#         response = {
#             "response": full_response,
#             "sources": [{"page_content": doc.page_content} for doc in documents],
#         }
#         return JSONResponse(content=response)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

# @app.get("/history/{session_id}")
# def get_chat_history(session_id: str):
#     try:
#         history = get_session_history(session_id)
#         return {"messages": history.get_messages()}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")
