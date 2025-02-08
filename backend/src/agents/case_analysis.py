from typing import Dict

from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import Graph

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
llm = OllamaLLM(model="llama3.2")

task_storage: Dict[str, str] = {}
case_study_text = ""
task_plan_prompt = PromptTemplate(
    input_variables=["case_study", "history"],
    template="""
    You are an advanced AI specializing in structured task extraction and planning. Your goal is to analyze the given 
    case study and extract a precise, step-by-step list of tasks that must be completed.  

### **Guidelines:**  
- Extract **only** tasks explicitly mentioned in the case study. Do not generate or assume tasks that are not stated.  
- Maintain the **original order** of tasks as they appear in the case study.  
- Provide each task in a **detailed step-by-step manner**, ensuring clarity and completeness.  
- Clearly explain what each task involves, specifying any key details mentioned in the case study.  
- Identify any **dependencies** between tasks (e.g., Task B must be done after Task A).  
- If deadlines are mentioned, include them with the corresponding tasks. If not no need to put anything.   

### **Input:**  
#### **Case Study:**  
{case_study}  

#### **Conversation History (for reference):**  
{history}  

### **Expected Output Format:**  
Provide the extracted tasks as a **step-by-step numbered list** in the following format:  

1. **[Task Name]**  
   - **Description:** A detailed explanation of what needs to be done.  
   - **Dependencies:** If the task depends on another task, specify it.  
   - **Deadline:** If a deadline is mentioned, include it.  

Continue this format for all tasks mentioned in the case study. Ensure that the output is **clear, structured, 
and strictly based on the given information.**  

If the case study lacks essential details, state the missing information explicitly instead of making assumptions.  

Now, analyze the case study and extract the structured task list.

"""
)


def generate_task_plan(_):
    """Generates an initial task plan based on the case study."""
    global case_study_text

    history = memory.load_memory_variables({}).get("chat_history", [])

    response = llm.invoke(task_plan_prompt.format(case_study=case_study_text, history=history))

    memory.save_context({"input": case_study_text}, {"output": response})

    task_storage["task_plan"] = response

    return {"task_plan": response}


def ask_human_review(_):
    """Asks the user if the plan is acceptable."""

    task_plan = task_storage.get("task_plan", "No task plan found. Generate one first.")
    print("\nGenerated Task Plan:\n", task_plan)

    user_feedback = input("\nDo you approve this plan? (/yes to approve, or provide feedback): ")

    return {"user_feedback": user_feedback}


def process_feedback(inputs):
    """Processes human feedback: either iterate or finalize."""

    user_feedback = inputs["user_feedback"]

    if user_feedback.lower() == "/yes":
        return {"final_plan": task_storage.get("task_plan", "No final plan available.")}
    else:
        memory.save_context({"input": "User Feedback"}, {"output": user_feedback})
        return {"retry": True}


workflow = Graph()

workflow.add_node("generate_task_plan", generate_task_plan)
workflow.add_node("ask_human_review", ask_human_review)
workflow.add_node("process_feedback", process_feedback)

workflow.set_entry_point("generate_task_plan")
workflow.add_edge("generate_task_plan", "ask_human_review")
workflow.add_edge("ask_human_review", "process_feedback")

workflow.add_conditional_edges(
    "process_feedback",
    lambda output: "generate_task_plan" if "retry" in output else END
)

graph_executor = workflow.compile()


def get_agent_result(file_path: str):
    global case_study_text
    with open(file_path, 'r') as f:
        case_study_text = f.read()

    result = graph_executor.invoke({})

    return result["final_plan"]
