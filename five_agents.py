import json, re
from groq_service import call_groq
from crewai_team import build_agents, make_crew, safe_json

def _direct(client, role, task, context):
    system=f"You are the {role} in a five-agent interview system. Be concise, evidence-grounded, practical, and never invent candidate facts. Return JSON only when requested."
    return call_groq(client, system, task+"\n\nEVIDENCE/STATE:\n"+context, temperature=0.15, max_tokens=900)

def run_agent(client, role, task, context, use_crewai=True):
    if use_crewai:
        try:
            agents=build_agents()
            mapping={a.role:a for a in agents}
            agent=next((a for a in agents if a.role.startswith(role)), agents[0])
            t=__import__("crewai").Task(description=task+"\n\nSTATE:\n"+context, expected_output="A concise useful result.", agent=agent)
            result=make_crew([agent],[t]).kickoff()
            return str(result.raw if hasattr(result,"raw") else result)
        except Exception:
            return _direct(client, role, task, context)
    return _direct(client, role, task, context)

def evidence_agent(client, cv, jd):
    prompt="""Create an evidence brief. Separate:
1) supported candidate facts from CV,
2) explicit JD requirements,
3) gaps/unknowns.
Never turn a JD requirement into candidate experience.
Return JSON with supported_facts, jd_requirements, gaps."""
    return run_agent(client,"Evidence Agent",prompt,f"CV:\n{cv[:7000]}\n\nJD:\n{jd[:7000]}")

def research_agent(client, query, enabled=False):
    if not enabled or not query.strip():
        return {"status":"disabled","sources":[]}
    try:
        from ddgs import DDGS
        results=[]
        with DDGS() as ddgs:
            for r in ddgs.text(query,max_results=5):
                results.append({"title":r.get("title",""),"snippet":r.get("body",""),"url":r.get("href","")})
        return {"status":"ok","sources":results}
    except Exception as e:
        return {"status":"unavailable","sources":[],"note":str(e)}

def strategy_agent(client, state, evidence, answer_feedback=""):
    prompt="""Decide the next interview objective. Prefer one skill gap or one JD-critical competency. If the previous answer was weak, drill down; if strong, increase complexity. Return JSON:
{"objective":"...","skill":"...","difficulty":"Easy|Medium|Hard|Expert","reason":"..."}"""
    return safe_json(run_agent(client,"Strategy Agent",prompt,json.dumps({"state":state,"evidence":evidence,"feedback":answer_feedback})[:12000],True))

def interviewer_agent(client, objective, evidence, personality="Professional & Structured"):
    prompt=f"""Create exactly ONE practical interview question, 8-24 words. It must test this objective: {objective}. Personality: {personality}. Use evidence where relevant. No trivia, no invented candidate claims. Return JSON: {{"question":"...","skill":"..."}}"""
    return safe_json(run_agent(client,"Interviewer Agent",prompt,evidence,True))

def coach_agent(client, question, answer, evidence, role, feedback_context=""):
    prompt="""Evaluate the answer on six 1-10 dimensions: technical accuracy, completeness, depth, communication, problem solving, role relevance. Also provide impact_score 1-100, 2 strengths, 2 gaps, a 30-60 second better practice answer using only supported facts or explicit placeholders, and verification notes. Return JSON:
{"technical":0,"completeness":0,"depth":0,"communication":0,"problem_solving":0,"role_relevance":0,"impact_score":0,"strengths":[],"gaps":[],"better_answer":"","verification":[],"tested_skill":""}"""
    ctx=f"ROLE: {role}\nQUESTION: {question}\nANSWER: {answer}\nEVIDENCE: {evidence}\nPREVIOUS: {feedback_context}"
    return safe_json(run_agent(client,"Coach Agent",prompt,ctx,True))
