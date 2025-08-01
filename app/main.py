from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
from .summarizer import process_and_summarize

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "🚀 Summarizer API is live!"}

@app.post("/summarize")
async def summarize(
    file: Optional[UploadFile] = None,
    url: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    keywords: Optional[str] = Form("")
):
    try:
        return await process_and_summarize(file, url, content, keywords)
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
