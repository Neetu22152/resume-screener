from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
import spacy
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
nlp = spacy.load("en_core_web_sm")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_keywords(text):
    doc = nlp(text.lower())
    keywords = [
        token.lemma_ for token in doc
        if not token.is_stop
        and not token.is_punct
        and not token.is_space
        and len(token.text) > 2
        and token.pos_ in ("NOUN", "PROPN")
    ]
    return set(keywords)

def get_ai_suggestions(missing_keywords):
    if not missing_keywords:
        return "Your resume looks great! No major keywords missing."
    missing = ", ".join(sorted(missing_keywords))
    prompt = f"""
    A job applicant is missing these keywords from their resume: {missing}
    Write 2-3 specific sentences they can copy-paste into their resume to naturally
    include these missing skills. Make it professional and realistic. Be brief.
    """
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return "AI suggestions unavailable right now. Try again in a few minutes."

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
      <body style="font-family: sans-serif; max-width: 600px; margin: 60px auto; padding: 0 20px;">
        <h2>Resume Screener</h2>
        <form action="/analyze" method="post" enctype="multipart/form-data">
          <p>
            <label>Job Description</label><br>
            <textarea name="job_description" rows="6"
              style="width:100%; margin-top:6px; padding:8px;"
              placeholder="Paste the job description here..."></textarea>
          </p>
          <p>
            <label>Upload Resume (.txt)</label><br>
            <input type="file" name="resume" accept=".txt" style="margin-top:6px;">
          </p>
          <button type="submit"
            style="background:#333; color:white; padding:10px 24px; border:none; cursor:pointer;">
            Analyze
          </button>
        </form>
      </body>
    </html>
    """

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(job_description: str = Form(...), resume: UploadFile = File(...)):
    resume_text = (await resume.read()).decode("utf-8", errors="ignore")

    job_keywords = extract_keywords(job_description)
    resume_keywords = extract_keywords(resume_text)

    matched = job_keywords & resume_keywords
    missing = job_keywords - resume_keywords

    score = round(len(matched) / len(job_keywords) * 100) if job_keywords else 0
    color = "#2ecc71" if score >= 60 else "#e67e22" if score >= 40 else "#e74c3c"

    ai_suggestions = get_ai_suggestions(missing)

    matched_html = " ".join(
        f'<span style="background:#d5f5e3;padding:2px 8px;border-radius:12px;font-size:13px;">{w}</span>'
        for w in sorted(matched)
    )
    missing_html = " ".join(
        f'<span style="background:#fde8e8;padding:2px 8px;border-radius:12px;font-size:13px;">{w}</span>'
        for w in sorted(missing)
    )

    return f"""
    <html>
      <body style="font-family: sans-serif; max-width: 600px; margin: 60px auto; padding: 0 20px;">
        <h2>Result</h2>
        <div style="margin: 20px 0;">
          <div style="font-size:48px; font-weight:bold; color:{color};">{score}%</div>
          <div style="background:#eee; border-radius:8px; height:12px; margin-top:8px;">
            <div style="background:{color}; width:{score}%; height:12px; border-radius:8px;"></div>
          </div>
        </div>
        <p><strong>Keywords you have</strong> ({len(matched)})</p>
        <p>{matched_html}</p>
        <p style="margin-top:16px;"><strong>Keywords you are missing</strong> ({len(missing)})</p>
        <p>{missing_html}</p>
        <div style="margin-top:24px; padding:16px; background:#f0f7ff; border-radius:8px; border-left:4px solid #3498db;">
          <p style="margin:0 0 8px 0;"><strong>AI Suggestions</strong></p>
          <p style="margin:0; font-size:14px; line-height:1.6;">{ai_suggestions}</p>
        </div>
        <a href="/" style="display:inline-block; margin-top:24px; color:#333;">Try another</a>
      </body>
    </html>
    """