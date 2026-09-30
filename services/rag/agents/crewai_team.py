import json
from crewai import Agent, Task, Crew, Process
try:
    from crewai import LLM
except Exception:
    LLM = None
from services.groq_service import get_api_key

ROLES = [
    ("Evidence Agent","Extracts and protects candidate/JD evidence; never invents candidate facts."),
    ("Research Agent","Finds optional public role/company context and keeps it separate from candidate evidence."),
    ("Strategy Agent","Chooses the next skill/objective based on interview state and the latest evaluation."),
    ("Interviewer Agent","Turns the strategy into one concise, natural hiring-manager question."),
    ("Coach Agent","Scores the answer, identifies gaps, verifies claims and drafts a better practice answer."),
]

def build_agents(llm=None):
    if llm is None and LLM is not None and get_api_key():
        try:
            llm = LLM(
                model="groq/openai/gpt-oss-20b",
                api_key=get_api_key(),
                base_url="https://api.groq.com/openai/v1",
                temperature=0.15,
            )
        except Exception:
            llm = None
    return [Agent(role=r, goal=g, backstory=g, llm=llm, verbose=False, allow_delegation=False) for r,g in ROLES]

def make_crew(agents, tasks):
    return Crew(agents=agents, tasks=tasks, process=Process.sequential, verbose=False)

def safe_json(text):
    try:
        return json.loads(text)
    except Exception:
        s=text.strip()
        a=s.find("{"); b=s.rfind("}")
        if a>=0 and b>a:
            try: return json.loads(s[a:b+1])
            except Exception: pass
    return {"raw":text}
