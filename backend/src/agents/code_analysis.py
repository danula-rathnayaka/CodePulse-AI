import os
from typing import Dict, List
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form
from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import StateGraph

llm = OllamaLLM(model="deepseek-coder:1.3b")


class CodeReviewState(BaseModel):
    file_path: str = ""
    project_path: str = ""
    ignore_files: List[str] = []
    file_extensions: List[str] = []
    files_found: List[str] = []
    report: Dict[str, str] = {}


workflow = StateGraph(CodeReviewState)


@workflow.add_node
def find_files_found(state: CodeReviewState) -> CodeReviewState:
    """Finds all files in the given project directory or processes a single file if provided."""
    files_found = []
    ignore_files_set = set(state.ignore_files)

    if state.file_path:
        if os.path.isfile(state.file_path):
            _, file_extension = os.path.splitext(state.file_path)
            if not state.file_extensions or file_extension in state.file_extensions:
                files_found.append(state.file_path)
    else:
        for root, dirs, files in os.walk(state.project_path):
            dirs[:] = [d for d in dirs if d not in ignore_files_set]
            files = [f for f in files if f not in ignore_files_set]

            for file in files:
                if any(file.endswith(ext) for ext in state.file_extensions):
                    files_found.append(os.path.join(root, file))

    return CodeReviewState(
        file_path=state.file_path,
        project_path=state.project_path,
        ignore_files=state.ignore_files,
        files_found=files_found,
        report=state.report
    )


@workflow.add_node
def review_code(state: CodeReviewState) -> CodeReviewState:
    """Analyzes each file for errors, optimizations, and improvements."""
    report = {}
    for file in state.files_found:
        with open(file, "r", encoding="utf-8") as f:
            code = f.read()

        _, file_extension = os.path.splitext(file)

        prompt = f"""
        You are an **expert code reviewer** specializing in **high-performance computing, security, and software architecture**.  
        Analyze the following **strictly within its context** and provide a professional, structured review.

        # **Code Review Guidelines**
        Your review must be **precise, technical, and actionable**, covering the following aspects:

        ### **1. Errors & Bugs**
        - Identify syntax errors, logical mistakes, or undefined behaviors.
        - Highlight incorrect assumptions and edge cases that may cause failures.
        - Provide **clear and practical solutions** to fix the issues.

        ### **2. Performance & Optimization**
        - Detect inefficient algorithms, redundant operations, and slow-performing logic.
        - Suggest **optimized data structures or alternative implementations**.
        - Explain **why your optimizations improve performance**.

        ### **3. Code Quality & Maintainability**
        - Evaluate **code structure, readability, and modularity**.
        - Identify **violations of clean code principles (SOLID, DRY, KISS, etc.)**.
        - Recommend **refactoring strategies** to improve long-term maintainability.

        ### **4. Security & Reliability**
        - Identify **potential security risks** (e.g., injection vulnerabilities, unsafe input handling, concurrency issues).
        - Recommend **secure coding practices** to mitigate risks.
        - Highlight **weak error handling or failure points** and suggest improvements.

        ### **5. Best Practices & Standards**
        - Assess adherence to **industry best practices** (naming conventions, function decomposition, error handling).
        - Recommend **framework-specific and language-specific improvements**.
        - Provide **real-world, production-ready enhancements**.

        # **Code Review for:** {os.path.basename(file)} ({file_extension[1:]})
        ```{file_extension[1:]}
        {code}
        
        Response Format
        Provide the final output as a markdown formatted string
        Your response must strictly follow this format:

        Code Review
        1. Errors & Bugs
        [List of issues + proposed solutions]

        2. Performance & Optimization
        [List inefficiencies + optimized alternatives]

        3. Code Quality & Maintainability
        [List issues + refactoring suggestions]

        4. Security & Reliability
        [List security vulnerabilities + fixes]

        5. Best Practices & Standards
        [List best practices violations + improvements]

        Rules:

        Do NOT describe the file’s purpose—focus only on the code review.
        Do NOT make assumptions about missing parts—analyze only what is provided.
        Follow this structured format exactly to ensure a high-quality review. """

        feedback = llm.invoke(prompt)
        report[file] = feedback

    return CodeReviewState(
        file_path=state.file_path,
        project_path=state.project_path,
        files_found=state.files_found,
        report=report
    )


workflow.set_entry_point("find_files_found")
workflow.add_edge("find_files_found", "review_code")
workflow.add_edge("review_code", END)

code_review_executor = workflow.compile()


def get_code_review_for_file(file_path: str) -> dict:
    result = code_review_executor.invoke(
        CodeReviewState(
            file_path=file_path,
            project_path="",
            ignore_files=[],
            file_extensions=[]
        )
    )

    return dict(result['report'])

def get_code_review_for_folder(project_path: str, ignore_files, file_extensions) -> dict:
    result = code_review_executor.invoke(
        CodeReviewState(
            file_path="",
            project_path=project_path,
            ignore_files=ignore_files,
            file_extensions=file_extensions
        )
    )

    return dict(result['report'])
