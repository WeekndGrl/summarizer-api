from fastapi import UploadFile
from typing import Optional
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
import os, tempfile, re, time, unicodedata
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

# Load .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is missing! Check your environment variables.")

client = OpenAI(api_key=api_key)
MAX_INPUT_CHARS = 24000

def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\uD800-\uDFFF]", "", text)
    text = re.sub(r"[^\x00-\x7F\u00A0-\uFFFF]+", "", text)
    return text

def fetch_web_content(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text() for p in paragraphs)
        return clean_text(text.strip())
    except Exception as e:
        return f"[Failed to fetch article content: {e}]"

def summarize_content(url: str, content: str, keywords: list[str] = None) -> str:
    content = clean_text(content)
    if len(content) > MAX_INPUT_CHARS:
        content = content[:MAX_INPUT_CHARS] + "\n[...TRUNCATED TO FIT CONTEXT WINDOW...]"

    today = datetime.today().strftime("%Y-%m-%d")
    keyword_str = ", ".join(keywords) if keywords else "None"

    system_prompt = (
        "You are Lyra — a multilingual investigative foresight analyst. Your mission is to uncover early signals, "
        "strategic trends, buried motives, and framing bias in complex information. You are trained in intelligence analysis, "
        "horizon scanning, behavioral economics, and regulatory forensics. Your tone is formal, analytic, and structured — not chatty."
    )

    user_prompt = (
        f"# Context\n"
        f"- Source URL: {url}\n"
        f"- Date: {today}\n"
        f"- Keywords to prioritize: {keyword_str}\n\n"
        f"# Raw Content:\n{content}\n\n"
        "# 🎯 Your Task:\n"
        "Conduct a high-level OSINT scan of the material above. Look for:\n"
        "- Weak or early signals that may indicate future developments\n"
        "- Power asymmetries, buried agendas, unexplained decisions\n"
        "- Legal/regulatory positioning or financial strategies\n"
        "- Subtext: what’s implied but unsaid, contradictory, or framed selectively\n"
        "- Connections to geopolitical or market-level shifts\n\n"
        "# 🧠 Output Format:\n"
        "## 1. Key Weak Signals\n"
        "- <Pattern or excerpt — why it might matter>\n\n"
        "## 2. Stakeholders & Strategic Behavior\n"
        "- <Actors involved, strategic or financial motive, timing relevance>\n\n"
        "## 3. Policy, Economic, or Legal Implications\n"
        "- <Emerging regulation, market positioning, lobbying clues>\n\n"
        "## 4. Narrative Engineering\n"
        "- <Euphemisms, loaded terms, omissions, linguistic control>\n\n"
        "## 5. Context Linkages\n"
        "- <Tie to past events, funding flows, political cycles, etc.>\n\n"
        "## 6. Intelligence Summary\n"
        ">  Write at least 2400 tokens worth of structured insight.>\n\n"
        "## 7. Confidence Level\n"
        "- Low / Medium / High — based on evidence weight\n\n"
        "## 8. Recommended Watch Points\n"
        "- <Next steps, actors to monitor, scenario flags>"
    )

    time.sleep(6)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.6,
        max_tokens=2400,
    )

    return response.choices[0].message.content.strip()

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
