from fastapi import FastAPI, Form

from agents.code_analysis import get_code_review_for_file

app = FastAPI(title="CodePulse AI", version="1.0")


@app.post("/review_file")
async def review_uploaded_file(file_path: str) -> dict:
    return {"review": get_code_review_for_file(file_path)}

