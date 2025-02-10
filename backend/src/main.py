from agents.case_analysis import get_agent_result as case_analyst
from agents.plan_creator import get_agent_result as plan_creator

case = case_analyst(file_path="../Sample Data/SampleData.txt")
print(case)
print("----------------------------------------")

print(plan_creator(case))
