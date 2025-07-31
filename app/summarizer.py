# utils/summarizer.py

import os
import re
import time
import unicodedata
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import sys
from nlp import summarize_content, fetch_web_content

# Load .env
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "locker.env"))
load_dotenv(dotenv_path, override=True)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is missing! Check locker.env")

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


if __name__ == "__main__":
    input_path = sys.argv[1]
    url = sys.argv[2] if len(sys.argv) > 2 else "N/A"
    keywords = sys.argv[3:] if len(sys.argv) > 3 else []

    if input_path.lower().startswith("http"):
        content = fetch_web_content(input_path)
    else:
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

    summary = summarize_content(url, content, keywords)
    print(summary.encode("ascii", "ignore").decode())  # Safe print for Windows
