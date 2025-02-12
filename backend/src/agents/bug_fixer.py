from typing import Dict

from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import StateGraph
from pydantic import BaseModel

llm = OllamaLLM(model="deepseek-coder:1.3b")


class BugFixState(BaseModel):
    file_path: str
    error_message: str
    code: str = ""
    fix_suggestion: str = ""
    fixed_code: str = ""
    validation_result: str = ""
    report: Dict[str, str] = {}


workflow = StateGraph(BugFixState)


@workflow.add_node
def read_file(state: BugFixState) -> BugFixState:
    """Reads the file content from the given file path."""

    with open(state.file_path, "r", encoding="utf-8") as file:
        code = file.read()
    return BugFixState(
        file_path=state.file_path,
        error_message=state.error_message,
        code=code,
        report=state.report
    )


@workflow.add_node
def analyze_error(state: BugFixState) -> BugFixState:
    """Analyzes the error message and extracts key information."""

    prompt = f"""
    You are an expert in bug fixing. Given the following error message:
    {state.error_message}
    Please provide a detailed analysis of the potential cause of the error.
    """
    analysis = llm.invoke(prompt)
    return BugFixState(
        file_path=state.file_path,
        error_message=state.error_message,
        code=state.code,
        report={**state.report, "error_analysis": analysis}
    )


@workflow.add_node
def suggest_fix(state: BugFixState) -> BugFixState:
    """Suggests a fix based on the error analysis and code."""

    prompt = f"""
    Based on the following error analysis:
    {state.report.get('error_analysis')}
    Please suggest a fix for the code. The code is:
    ```python
    {state.code}
    ```
    Provide a clear explanation for the fix.
    """
    fix = llm.invoke(prompt)
    return BugFixState(
        file_path=state.file_path,
        error_message=state.error_message,
        code=state.code,
        fix_suggestion=fix,
        report={**state.report, "fix_suggestion": fix}
    )


@workflow.add_node
def apply_fix(state: BugFixState) -> BugFixState:
    """Applies the suggested fix to the code."""

    fixed_code = state.code + "\n# Applied fix: " + state.fix_suggestion
    return BugFixState(
        file_path=state.file_path,
        error_message=state.error_message,
        code=state.code,
        fix_suggestion=state.fix_suggestion,
        fixed_code=fixed_code,
        report=state.report
    )


@workflow.add_node
def validate_fix(state: BugFixState) -> BugFixState:
    """Validates if the fix works correctly by performing a syntax check."""

    prompt = f"""
    Validate the following code for syntax errors:
    ```python
    {state.fixed_code}
    ```
    Respond with either 'Valid' or a description of any issues found.
    """
    validation = llm.invoke(prompt)
    return BugFixState(
        file_path=state.file_path,
        error_message=state.error_message,
        code=state.code,
        fix_suggestion=state.fix_suggestion,
        fixed_code=state.fixed_code,
        validation_result=validation,
        report={**state.report, "validation_result": validation}
    )


@workflow.add_node
def generate_report(state: BugFixState) -> BugFixState:
    """Generates a final report based on the analysis, fix, and validation."""

    report = f"""
    Bug Fix Report:
    =====================
    File Path: {state.file_path}
    Error Message: {state.error_message}

    Error Analysis:
    {state.report.get('error_analysis')}

    Suggested Fix:
    {state.report.get('fix_suggestion')}

    Fixed Code:
    {state.fixed_code}

    Validation Result:
    {state.validation_result}
    """

    return BugFixState(
        file_path=state.file_path,
        error_message=state.error_message,
        code=state.code,
        fix_suggestion=state.fix_suggestion,
        fixed_code=state.fixed_code,
        validation_result=state.validation_result,
        report={**state.report, "final_report": report}
    )


# Define workflow edges
workflow.set_entry_point("read_file")
workflow.add_edge("read_file", "analyze_error")
workflow.add_edge("analyze_error", "suggest_fix")
workflow.add_edge("suggest_fix", "apply_fix")
workflow.add_edge("apply_fix", "validate_fix")
workflow.add_edge("validate_fix", "generate_report")
workflow.add_edge("generate_report", END)

bug_fix_executor = workflow.compile()


def get_bug_fixer(file_path: str, error_msg: str) -> dict:

    result = bug_fix_executor.invoke(
        BugFixState(
            file_path=file_path,
            error_message=error_msg,
        )
    )

    return dict(result['report'])
