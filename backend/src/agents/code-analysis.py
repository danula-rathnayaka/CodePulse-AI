import os

from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="llama3.2")


def get_python_files(directory):
    """Recursively finds all Python files in the given directory."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def read_code(file_path):
    """Reads the content of a Python file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def analyze_code(code, file_name):
    """Uses an LLM to analyze the given code."""

    prompt = PromptTemplate(
        input_variables=["file_name", "code"],
        template="""
    You are an expert code reviewer. Analyze the following Python code and provide feedback on:
    1. **Errors & Bugs**: Identify syntax or logical mistakes.
    2. **Performance Improvements**: Suggest optimizations.
    3. **Code Quality & Best Practices**: Recommend refactoring where needed.

    **File: {file_name}**  
    ```python
    {code}
    ```

    Provide a structured response.
    """)

    response = llm.invoke(prompt.format(file_name=file_name, code=code))
    return response


def review_project(directory):
    """Scans and reviews all Python files in the project."""
    python_files = get_python_files(directory)
    report = {}

    for file in python_files:
        print(f"Analyzing {file} ...")
        code = read_code(file)
        feedback = analyze_code(code, os.path.basename(file))
        report[file] = feedback

    return report


if __name__ == "__main__":
    project_path = input("Enter the project directory path: ")
    report = review_project(project_path)

    # Print report
    for file, feedback in report.items():
        print("\n" + "=" * 80)
        print(f"📄 **File:** {file}")
        print(feedback)
        print("=" * 80)
