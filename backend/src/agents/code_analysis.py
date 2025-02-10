import os
from typing import Dict, List
from pydantic import BaseModel

from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import StateGraph

llm = OllamaLLM(model="llama3.2")


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
        print(f"🔍 Analyzing: {file} ...")
        with open(file, "r", encoding="utf-8") as f:
            code = f.read()

        _, file_extension = os.path.splitext(file)

        prompt = f"""
        You are an expert code reviewer. Analyze the following code and provide feedback on:
        1. **Errors & Bugs**: Identify syntax or logical mistakes.
        2. **Performance Improvements**: Suggest optimizations.
        3. **Code Quality & Best Practices**: Recommend refactoring where needed.

        **File: {os.path.basename(file)} ({file_extension[1:]})**
        ```{file_extension[1:]}
        {code}
        ```

        Provide a structured response.
        """
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

if __name__ == "__main__":
    file_or_directory = input("Enter a file path or project directory path: ").strip()

    if os.path.isfile(file_or_directory):
        file_path = file_or_directory
        project_path = ""
        ignore_files = []
        file_extensions = []
    else:
        file_path = ""
        project_path = file_or_directory
        ignore_files = input(
            "Enter the files to exclude from scanning (separated by spaces, leave empty for none): ").split()
        file_extensions = input(
            "Enter the file extensions to scan (e.g., .py .txt, leave empty for all files): ").split()

    result = code_review_executor.invoke(
        CodeReviewState(
            file_path=file_path,
            project_path=project_path,
            ignore_files=ignore_files,
            file_extensions=file_extensions
        )
    )

    output_dir = "../outputs"
    os.makedirs(output_dir, exist_ok=True)

    for file, feedback in result.report.items():
        file_name = os.path.basename(file)
        output_path = os.path.join(output_dir, f"{file_name}-code-analysis.md")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(feedback)

        absolute_path = os.path.abspath(output_path)
        print(f"✅ Code analysis report for file {file_name} saved at: {absolute_path}")
