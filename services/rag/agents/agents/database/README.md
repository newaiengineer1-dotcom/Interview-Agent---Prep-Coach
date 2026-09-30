# Interview Agent - Prep Coach

**AI Interview, Smarter You**

An Agentic RAG Interview Coach built for the hackathon. This MVP demonstrates Generative AI, Agentic AI, AI Workflows, Multi-Agent Systems, and AI-powered Business Process Automation.

## Five Agents
- Evidence Agent — CV/JD grounding
- Research Agent — optional public context
- Strategy Agent — chooses the next competency
- Interviewer Agent — asks one practical question
- Coach Agent — evaluates, verifies and coaches

## Run Locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
