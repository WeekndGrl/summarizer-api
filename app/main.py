from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from app.summarizer import summarize_input

app = FastAPI()

# CORS setup for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/summarize")
async def summarize(
    file: Optional[UploadFile] = None,
    url: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    keywords: Optional[str] = Form(None)
):
    result = await summarize_input(file=file, url=url, content=content, keywords=keywords)
    return {"summary": result}

@app.get("/")
def root():
    return {"message": "Summarizer API ready."}
