# main.py

import os
import io
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from app.summarizer import summarize_content, fetch_web_content

from PyPDF2 import PdfReader
from PIL import Image
import pytesseract

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/summarize")
async def summarize_api(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    keywords: Optional[str] = Form(""),
):
    try:
        keywords_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]

        # If file is uploaded and no content yet
        if file and not content:
            ext = file.filename.split(".")[-1].lower()
            raw_bytes = await file.read()

            if ext == "pdf":
                reader = PdfReader(io.BytesIO(raw_bytes))
                content = "\n".join(page.extract_text() or "" for page in reader.pages)

            elif ext == "txt":
                content = raw_bytes.decode("utf-8", errors="ignore")

            elif ext in ["jpg", "jpeg", "png", "webp"]:
                image = Image.open(io.BytesIO(raw_bytes))
                content = pytesseract.image_to_string(image)

            else:
                return { "error": f"Unsupported file type: {ext}" }

        if url and not content:
            content = fetch_web_content(url)

        summary = summarize_content(url or "", content or "", keywords_list)
        return { "summary": summary }

    except Exception as e:
        return { "error": str(e) }

@app.get("/")
def read_root():
    return { "message": "🚀 Summarizer API is up and running!" }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
