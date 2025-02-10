import os
from typing import Dict, List
from pydantic import BaseModel

from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import StateGraph

llm = OllamaLLM(model="llama3.2")


class CodeReviewState(BaseModel):
    project_path: str
    python_files: List[str] = []
    report: Dict[str, str] = {}


workflow = StateGraph(CodeReviewState)


@workflow.add_node
def find_python_files(state: CodeReviewState) -> CodeReviewState:
    """Finds all Python files in the given project directory."""
    python_files = []
    for root, _, files in os.walk(state.project_path):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return CodeReviewState(
        project_path=state.project_path,
        python_files=python_files,
        report=state.report
    )


@workflow.add_node
def review_code(state: CodeReviewState) -> CodeReviewState:
    """Analyzes each Python file for errors, optimizations, and improvements."""
    report = {}
    for file in state.python_files:
        print(f"🔍 Analyzing: {file} ...")
        with open(file, "r", encoding="utf-8") as f:
            code = f.read()

        # Define prompt
        prompt = f"""
        You are an expert code reviewer. Analyze the following Python code and provide feedback on:
        1. **Errors & Bugs**: Identify syntax or logical mistakes.
        2. **Performance Improvements**: Suggest optimizations.
        3. **Code Quality & Best Practices**: Recommend refactoring where needed.

        **File: {os.path.basename(file)}**  
        ```python
        {code}
        ```

        Provide a structured response.
        """
        feedback = llm.invoke(prompt)
        report[file] = feedback

    return CodeReviewState(
        project_path=state.project_path,
        python_files=state.python_files,
        report=report
    )


workflow.set_entry_point("find_python_files")
workflow.add_edge("find_python_files", "review_code")
workflow.add_edge("review_code", END)

code_review_executor = workflow.compile()

if __name__ == "__main__":
    project_path = input("Enter the project directory path: ")
    result = code_review_executor.invoke(CodeReviewState(project_path=project_path))

    for file, feedback in result['report'].items():
        print("\n" + "=" * 80)
        print(f"📄 **File:** {file}")
        print(feedback)
        print("=" * 80)
