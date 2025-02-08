from typing import Dict

from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import Graph

case_analysis = ""

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
llm = OllamaLLM(model="llama3.2")

task_storage: Dict[str, str] = {}

task_plan_prompt = PromptTemplate(
    input_variables=["task_list_from_case_analyst", "history"],
    template="""
You are an advanced AI specializing in structured project management. Your task is to take the task list provided by the case analyst agent and create a comprehensive project roadmap that outlines the entire development process.

### **Guidelines:**  
- Strictly **use** the task list provided by the case analyst agent (`{task_list_from_case_analyst}`). Do not add, modify, or assume any additional tasks outside of what is explicitly listed.
- Organize the tasks into **logical phases** of development.
- For each phase, define multiple **tasks** that need to be completed, as derived directly from the task list.
- Ensure that each task includes clear steps, **dependencies**, **timelines**, and **resources**.
- Consider dependencies between tasks and the logical flow of development from start to finish.
- The roadmap must reflect the **exact plan** from the case analyst agent.

### **Input:**  
#### **Task List from Case Analyst Agent (Final Output):**  
{task_list_from_case_analyst}

#### **Conversation History (for reference):**  
{history}

### **Expected Output Format:**  
The output will be a detailed **project plan** divided into **phases**, with each phase containing multiple tasks. For each task, include the following information:

---

### **Phase 1: Planning and Research**

#### Task 1: **[Task 1 Name]**  
   - **Description:** Provide a concise explanation of what needs to be done for this task.
   - **Priority:** High/Medium/Low (Indicate the importance of this task and whether it should be done first or can be done later).
   - **Dependencies:** List the tasks that must be completed before this one.
   - **Timeline:** Estimated time for completion (e.g., 1 week).
   - **Resources Required:** Tools, technologies, or team members needed.

#### Task 2: **[Task 2 Name]**  
   - **Description:** A detailed explanation of what needs to be done.
   - **Priority:** High/Medium/Low.
   - **Dependencies:** Which tasks need to be done first?
   - **Timeline:** Estimated time for completion.
   - **Resources Required:** Tools or team members needed.

---

### **Phase 2: Initial Development**

#### Task 1: **[Task 3 Name]**  
   - **Description:** What does this task involve?
   - **Priority:** High/Medium/Low.
   - **Dependencies:** List any prerequisites for this task.
   - **Timeline:** Estimated time to complete.
   - **Resources Required:** Team, tools, technologies, etc.

#### Task 2: **[Task 4 Name]**  
   - **Description:** A clear explanation of what must be done for this task.
   - **Priority:** High/Medium/Low.
   - **Dependencies:** Dependencies on other tasks.
   - **Timeline:** How much time should be allocated to complete it.
   - **Resources Required:** Any tools, infrastructure, or team members.

---

### **Phase 3: Testing and Validation**

#### Task 1: **[Task 5 Name]**  
   - **Description:** Detailed description of the testing task.
   - **Priority:** High/Medium/Low.
   - **Dependencies:** What should be completed before starting testing?
   - **Timeline:** Estimated time required.
   - **Resources Required:** Testing tools, testers, etc.

#### Task 2: **[Task 6 Name]**  
   - **Description:** Additional tasks for testing or validation.
   - **Priority:** High/Medium/Low.
   - **Dependencies:** Dependencies on earlier tasks.
   - **Timeline:** Estimated time.
   - **Resources Required:** Resources needed for testing.

---

### **Phase 4: Finalization and Deployment**

#### Task 1: **[Task 7 Name]**  
   - **Description:** Description of the final deployment-related task.
   - **Priority:** High/Medium/Low.
   - **Dependencies:** Dependencies from earlier development phases.
   - **Timeline:** Estimated time to complete.
   - **Resources Required:** Final production setup, deployment tools, etc.

#### Task 2: **[Task 8 Name]**  
   - **Description:** Additional tasks for optimization, release, or post-deployment.
   - **Priority:** High/Medium/Low.
   - **Dependencies:** Dependencies from testing or deployment.
   - **Timeline:** Estimated time required.
   - **Resources Required:** Tools and team members.

---

### **Final Notes:**
- Each task should be **strictly based on** the plan provided by the case analyst agent (`{task_list_from_case_analyst}`).
- The project phases and tasks must be logically organized to reflect the true sequence of steps required for the project.
- Each phase should be comprehensive, guiding the project from **start to finish**.
- Ensure all tasks are actionable and resource requirements are clear and precise.
- If the user requests any **changes or modifications** to the generated project plan as per the **chat history**, make sure to **update the plan accordingly** to reflect the feedback and suggestions.

The roadmap should act as a clear guide for the entire development process, ensuring that the project flows logically and efficiently.
    
"""
)


def generate_project_plan(_):
    """Generates a project plan based on the case study."""
    global case_analysis

    history = memory.load_memory_variables({}).get("chat_history", [])

    response = llm.invoke(task_plan_prompt.format(task_list_from_case_analyst=case_analysis, history=history))

    memory.save_context({"input": case_analysis}, {"output": response})

    task_storage["project_plan"] = response

    return {"project_plan": response}


def ask_human_review(_):
    """Asks the user if the project plan is acceptable."""
    task_plan = task_storage.get("project_plan", "No project plan found. Generate one first.")
    print("\nGenerated Project Plan:\n", task_plan)

    user_feedback = input("\nDo you approve this project plan? (/yes to approve, or provide feedback): ")

    return {"user_feedback": user_feedback}


def process_feedback(inputs):
    """Processes human feedback: either iterate or finalize."""
    user_feedback = inputs["user_feedback"]

    if user_feedback.lower() == "/yes":
        return {"final_plan": task_storage.get("project_plan", "No final plan available.")}

    else:
        memory.save_context({"input": "User Feedback"}, {"output": user_feedback})
        return {"retry": True}


workflow = Graph()

workflow.add_node("generate_project_plan", generate_project_plan)
workflow.add_node("ask_human_review", ask_human_review)
workflow.add_node("process_feedback", process_feedback)

workflow.set_entry_point("generate_project_plan")
workflow.add_edge("generate_project_plan", "ask_human_review")
workflow.add_edge("ask_human_review", "process_feedback")

workflow.add_conditional_edges(
    "process_feedback",
    lambda output: "generate_project_plan" if "retry" in output else END
)

graph_executor = workflow.compile()


def get_agent_result(case):
    global case_analysis
    case_analysis = case
    result = graph_executor.invoke({})

    return result["final_plan"]
