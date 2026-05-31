from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
import spacy

app = FastAPI()
nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    doc = nlp(text.lower())
    keywords = [
        token.lemma_ for token in doc
        if not token.is_stop        # removes "a", "the", "with", "for" etc
        and not token.is_punct      # removes ".", ",", "!" etc
        and not token.is_space      # removes blank lines
        and len(token.text) > 2
        and token.pos_ in ("NOUN", "PROPN")# removes tiny words like "to", "is"
    ]
    return set(keywords)

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

    matched_html = " ".join(f'<span style="background:#d5f5e3;padding:2px 8px;border-radius:12px;font-size:13px;">{w}</span>' for w in sorted(matched))
    missing_html = " ".join(f'<span style="background:#fde8e8;padding:2px 8px;border-radius:12px;font-size:13px;">{w}</span>' for w in sorted(missing))

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

        <p style="margin-top:16px;"><strong>Keywords you're missing</strong> ({len(missing)})</p>
        <p>{missing_html}</p>

        <a href="/" style="display:inline-block; margin-top:24px; color:#333;">Try another</a>
      </body>
    </html>
    """