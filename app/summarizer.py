from fastapi import UploadFile
from typing import Optional
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
import os, tempfile

from app.summarizer import summarize_content, fetch_web_content


async def process_and_summarize(
    file: Optional[UploadFile], url: Optional[str], content: Optional[str], keywords: Optional[str]
):
    extracted = ""
    kwords = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []

    if url:
        extracted += fetch_web_content(url) + "\n"

    if content:
        extracted += content + "\n"

    if file:
        suffix = os.path.splitext(file.filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp.flush()
            fpath = tmp.name

        if suffix == ".pdf":
            reader = PdfReader(fpath)
            for page in reader.pages:
                extracted += page.extract_text() + "\n"

        elif suffix in [".txt"]:
            with open(fpath, encoding="utf-8", errors="ignore") as f:
                extracted += f.read() + "\n"

        elif suffix in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
            image = Image.open(fpath)
            extracted += pytesseract.image_to_string(image) + "\n"

        os.remove(fpath)

    summary = summarize_content(url or "uploaded-file", extracted, kwords)
    return {"summary": summary}
