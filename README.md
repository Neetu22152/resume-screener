# Resume Screener

A web app that compares a resume against a job description and scores how well they match.

## What it does
- Extracts meaningful keywords using NLP (spaCy)
- Filters out filler words automatically
- Shows matched keywords in green and missing keywords in red
- Gives a percentage match score

## Tech used
- Python
- FastAPI
- spaCy

## How to run
pip install fastapi uvicorn python-multipart spacy
python -m spacy download en_core_web_sm
uvicorn main:app --reload
