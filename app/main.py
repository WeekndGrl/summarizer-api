from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import os
from app.summarizer import summarize_content, fetch_web_content


app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "🚀 Summarizer API is up and running!"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/summarize")
async def summarize_api(
    url: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    keywords: Optional[str] = Form(""),
):
    try:
        keywords_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
        if url and not content:
            content = fetch_web_content(url)
        summary = summarize_content(url, content or "", keywords_list)
        return { "summary": summary }
    except Exception as e:
        return { "error": str(e) }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
