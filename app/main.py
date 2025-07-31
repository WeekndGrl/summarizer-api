# app/main.py

from fastapi import FastAPI, Request
from pydantic import BaseModel
from app.summarizer import summarize_content, fetch_web_content
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class SummaryRequest(BaseModel):
    url: str
    content: str = ""
    keywords: list[str] = []

@app.post("/summarize")
async def summarize(req: SummaryRequest):
    content = req.content or fetch_web_content(req.url)
    summary = summarize_content(req.url, content, req.keywords)
    return { "summary": summary }

