from fastapi import FastAPI, Form

from agents.code_analysis import get_code_review_for_file, get_code_review_for_folder
from agents.bug_fixer import get_bug_fixer

app = FastAPI(title="CodePulse AI", version="1.0")


@app.get("/review_file")
async def review_file(file_path: str) -> dict:
    return {"review": get_code_review_for_file(file_path)}


@app.get("/review_folder")
async def review_folder(project_path: str, ignore_files, file_extensions) -> dict:
    return {"review": get_code_review_for_folder(project_path, ignore_files, file_extensions)}


@app.get("/bug_fixer")
async def bug_fixer(file_path: str, error_msg: str) -> dict:
    return {"review": get_bug_fixer(file_path, error_msg)}
