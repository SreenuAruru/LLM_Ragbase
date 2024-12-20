from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import shutil

# Initialize the FastAPI application
app = FastAPI()

# Configure CORS middleware (allows all origins, methods, and headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store uploaded files
UPLOAD_DIR = Path("uploads")  # Use pathlib for path handling
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Ensure upload directory exists

# Request model for asking questions
class QuestionRequest(BaseModel):
    question: str

# Endpoint to upload PDF files
@app.post("/upload_pdf/")
async def upload_pdf(files: list[UploadFile] = File(...)):
    try:
        uploaded_files = []
        # Process and save each uploaded file
        for file in files:
            file_path = UPLOAD_DIR / file.filename  # Path to save the file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Add the file information to the response
            uploaded_files.append({
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": file.size,
                "file_content": file.file.read().decode('utf-8', errors='ignore')  # Read content as text (for non-binary files)
            })

        print("-------> files", files)
        # Return the uploaded files details in the response
        return JSONResponse(content={"uploaded_files": uploaded_files}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"message": f"Error: {str(e)}"}, status_code=500)

# Endpoint to ask a question
@app.post("/ask_question/")
async def ask_question(data: QuestionRequest):
    try:
        question = data.question
        print(f"Received question: {question}")
        
        # Simulate a response (can integrate AI or database logic here)
        return JSONResponse(content={"message": f"Your question '{question}' has been received!"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": f"Error: {str(e)}"}, status_code=500)

# Run the FastAPI application using Uvicorn (for standalone execution)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
