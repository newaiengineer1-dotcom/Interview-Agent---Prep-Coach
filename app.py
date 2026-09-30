import html, json, datetime, streamlit as st
from config import APP_NAME, APP_TAGLINE
from groq_service import get_client, transcribe
from loader import extract_text, build_index
from five_agents import evidence_agent, research_agent, strategy_agent, interviewer_agent, coach_agent

st.set_page_config(page_title=APP_NAME, page_icon="⚡", layout="wide")

# --- PREMIUM DARK NAVY UI CSS ---
st.markdown("""
<style>
    .stApp { background-color: #080d18; color: #e7edf8; }
    [data-testid="stSidebar"] { background-color: #0d1424; border-right: 1px solid #263653; }
    .hero { padding: 28px 30px; border: 1px solid #263653; border-radius: 22px; background: linear-gradient(135deg,#111b31,#0b1220); box-shadow: 0 16px 60px rgba(0,0,0,.25); margin-bottom: 20px; }
    .hero h1 { font-size: 42px; margin: 0; color: #f7fbff; font-weight: 700; }
    .hero p { color: #9fb0c9; font-size: 16px; margin-top: 5px; }
    .card { padding: 20px; border: 1px solid #263653; border-radius: 18px; background: #10182a; margin: 10px 0; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
    .agent { padding: 12px; border-radius: 12px; background: #0c1424; border: 1px solid #24334f; margin: 7px 0; text-align: center; }
    .agent.active { border-color: #43d7ff; box-shadow: 0 0 15px rgba(67, 215, 255, 0.2); }
    .q { font-size: 24px; line-height: 1.4; color: #ffffff; font-weight: 600; margin-top: 10px; }
    .small { color: #9fb0c9; font-size: 13px; }
    .accent { color: #43d7ff; }
    .ok { color: #4de1a8; }
    .warn { color: #ffc857; }
    .score-box { background: #16213e; border-radius: 12px; padding: 15px; text-align: center; border: 1px solid #263653; }
    .score-val { font-size: 28px; font-weight: bold; color: #4de1a8; }
    .progress-bar { height: 8px; background: #263653; border-radius: 4px; margin-top: 10px; }
    .progress-fill { height: 100%; background: #43d7ff; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "built" not in st.session_state: st.session_state.built = False
if "history" not in st.session_state: st.session_state.history = []
if "state" not in st.session_state: st.session_state.state = {"difficulty": "Medium", "question_no": 0, "skills": []}
if "question" not in st.session_state: st.session_state.question = "Click Start Interview to generate the first question."
if "evidence" not in st.session_state: st.session_state.evidence = ""
if "evidence_json" not in st.session_state: st.session_state.evidence_json = {}
if "research" not in st.session_state: st.session_state.research = {}

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"## ⚡ {APP_NAME}")
    name = st.text_input("Candidate name", "Alex Chen")
    role = st.text_input("Target role", "Backend Software Engineer")
    field = st.text_input("Field / industry", "IT / Software")
    personality = st.selectbox("Hiring-manager style", ["Professional & Structured", "Friendly & Encouraging", "Strict & Demanding", "Startup CTO", "HR Manager"])
    count = st.slider("Questions", 3, 12, 6)
    web = st.checkbox("Optional web research", False)
    cv = st.file_uploader("CV / Resume", type=["pdf", "docx", "txt"])
    jd = st.file_uploader("Job Description", type=["pdf", "docx", "txt"])
    
    if st.button("Build Evidence Base", use_container_width=True, type="primary"):
        if not cv or not jd:
            st.error("Upload both CV and Job Description.")
        else:
            try:
                cv_text = extract_text(cv); jd_text = extract_text(jd)
                st.session_state.rag = build_index(cv_text, jd_text, cv.name, jd.name)
                st.session_state.cv = cv_text; st.session_state.jd = jd_text
                with st.spinner("Evidence Agent is building the evidence base..."):
                    raw = evidence_agent(get_client(), cv_text, jd_text)
                st.session_state.evidence_json = raw if isinstance(raw, dict) else {"raw": raw}
                st.session_state.evidence = st.session_state.rag.context(role + " " + field, 6)
                st.session_state.built = True
                st.success("Evidence base ready.")
            except Exception as e:
                st.error(f"Error building evidence: {str(e)}")
                
    if st.button("Reset Interview", use_container_width=True):
        for k in ["history", "question", "evidence", "evidence_json", "last"]:
            st.session_state.pop(k, None)
        st.session_state.state = {"difficulty": "Medium", "question_no": 0, "skills": []}
        st.session_state.built = False
        st.rerun()

# --- MAIN DASHBOARD HEADER ---
st.markdown(f'''
<div class="hero">
    <h1>🧠 {APP_NAME}</h1>
    <p>{APP_TAGLINE} • Generative AI • Agentic AI • AI Workflow • Multi-Agent • Business Process Automation</p>
</div>
''', unsafe_allow_html=True)

# --- TOP METRICS ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Agent System", "5 Active")
m2.metric("Interview Turns", len(st.session_state.history))
m3.metric("Difficulty", st.session_state.state.get("difficulty", "Medium"))
m4.metric("Field", field)

if not st.session_state.built:
    st.info("👈 Please upload a CV + JD and click 'Build Evidence Base' in the sidebar to begin your interview.")
    st.stop()

# --- AGENT STATUS ROW ---
st.markdown("### 🤖 Agent Activity")
cols = st.columns(5)
agent_names = ["Evidence", "Research", "Strategy", "Interviewer", "Coach"]
for c, label in zip(cols, agent_names):
    active = "active" if (label == "Strategy" and len(st.session_state.history) > 0) or (label == "Interviewer" and st.session_state.state["question_no"] > 0) else ""
    c.markdown(f'<div class="agent {active}">● <b>{label} Agent</b><br><span class="small">Ready</span></div>', unsafe_allow_html=True)

# --- INTERVIEW FLOW ---
if st.button("▶ Start / Next Interview Question", type="primary", use_container_width=True):
    with st.spinner("Strategy Agent → Interviewer Agent..."):
        if web:
            research = research_agent(get_client(), f"{role} {field} current interview requirements", True)
        else:
            research = {"status": "disabled", "sources": []}
        strategy = strategy_agent(get_client(), st.session_state.state, st.session_state.evidence, st.session_state.history[-1].get("feedback", "") if st.session_state.history else "")
        iq = interviewer_agent(get_client(), strategy.get("objective", "role fundamentals"), st.session_state.evidence, personality)
        st.session_state.research = research
        st.session_state.strategy = strategy
        st.session_state.question = iq.get("question", "Walk me through a relevant project and the decisions you made.")
        st.session_state.state["question_no"] += 1
        st.session_state.state["difficulty"] = strategy.get("difficulty", st.session_state.state.get("difficulty", "Medium"))

# Question Display
st.markdown(f'''
<div class="card">
    <div class="small">QUESTION {st.session_state.state["question_no"]} OF {count}</div>
    <div class="q">{html.escape(st.session_state.question)}</div>
</div>
''', unsafe_allow_html=True)

# Answer Input
answer = st.text_area("Your answer", height=150, placeholder="Answer as you would in a real interview...")
audio = st.audio_input("Or record a voice answer")

if audio and st.button("Transcribe voice answer"):
    try:
        text = transcribe(get_client(), audio)
        if text:
            st.session_state.voice_answer = text
            st.success("Transcription ready.")
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")

answer = st.session_state.get("voice_answer", answer)

if st.button("Evaluate Answer", type="primary", use_container_width=True):
    if not answer.strip():
        st.warning("Please provide a text or voice answer first.")
    else:
        with st.spinner("Coach Agent is evaluating and verifying your answer..."):
            evidence = st.session_state.evidence
            result = coach_agent(get_client(), st.session_state.question, answer, evidence, role)
        st.session_state.history.append({"question": st.session_state.question, "answer": answer, "feedback": json.dumps(result)})
        st.session_state.last = result
        # REMOVED: save_session() -> This was causing the SQLite error
        st.session_state.pop("voice_answer", None)

# --- FEEDBACK DISPLAY ---
if "last" in st.session_state:
    r = st.session_state.last
    st.markdown("### 📊 Interview Feedback")
    
    # Score Row
    a, b, c, d = st.columns(4)
    with a: st.markdown(f'<div class="score-box"><div class="small">Impact Score</div><div class="score-val">{r.get("impact_score",0)}/100</div></div>', unsafe_allow_html=True)
    with b: st.markdown(f'<div class="score-box"><div class="small">Technical</div><div class="score-val">{r.get("technical",0)}/10</div></div>', unsafe_allow_html=True)
    with c: st.markdown(f'<div class="score-box"><div class="small">Communication</div><div class="score-val">{r.get("communication",0)}/10</div></div>', unsafe_allow_html=True)
    with d: st.markdown(f'<div class="score-box"><div class="small">Role Relevance</div><div class="score-val">{r.get("role_relevance",0)}/10</div></div>', unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown("#### ✅ What Worked")
        for x in r.get("strengths", []): st.write("• " + str(x))
        st.markdown("#### ⚠️ What Was Missing")
        for x in r.get("gaps", []): st.write("• " + str(x))
    with right:
        st.markdown("#### 💡 Better Practice Answer")
        st.success(r.get("better_answer", "No practice answer returned."))
        st.markdown("#### 🔍 Evidence Verification")
        for x in r.get("verification", []): st.write("• " + str(x))

    if st.button("Continue to next adaptive question", use_container_width=True):
        st.rerun()

# --- FINAL REPORT ---
if len(st.session_state.history) >= count:
    st.markdown("---")
    st.markdown("## 🏁 Final Interview Report")
    avg_score = sum(json.loads(h["feedback"]).get("impact_score", 0) for h in st.session_state.history) / len(st.session_state.history)
    st.metric("Overall Interview Score", f"{avg_score:.1f}/100")
    st.success("Interview complete! You can review your feedback above or reset to practice again.")

with st.expander("📚 Evidence & RAG Context"):
    st.write(st.session_state.evidence)
with st.expander("🌐 Research Sources"):
    for s in st.session_state.get("research", {}).get("sources", []): 
        st.write(f"{s.get('title')} — {s.get('url')}")
