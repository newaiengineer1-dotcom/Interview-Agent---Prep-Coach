import io, os
import streamlit as st
from groq import Groq

CHAT_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
WHISPER_MODELS = ["whisper-large-v3-turbo", "whisper-large-v3"]

def get_api_key():
    try:
        if "GROQ_API_KEY" in st.secrets:
            return str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "").strip()

def get_client():
    key = get_api_key()
    if not key:
        st.error("GROQ_API_KEY is missing. Please add it to Streamlit Secrets or environment variables.")
        return None
    return Groq(api_key=key)

def call_groq(client, system_prompt, user_prompt, model=None, temperature=0.2, max_tokens=900):
    if not client:
        raise ValueError("Groq client not initialized. Check API key.")
    models = [model] if model else CHAT_MODELS
    last = None
    for name in models:
        try:
            r = client.chat.completions.create(
                model=name,
                messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
                temperature=temperature, max_tokens=max_tokens
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            last = e
    raise RuntimeError(f"Groq request failed on all configured models. Last error: {last}")

def transcribe(client, audio):
    if not client or not audio:
        return ""
    raw = audio.getvalue() if hasattr(audio, "getvalue") else audio
    bio = io.BytesIO(raw); bio.name = "candidate.webm"
    last = None
    for model in WHISPER_MODELS:
        try:
            bio.seek(0)
            r = client.audio.transcriptions.create(file=(bio.name,bio), model=model)
            return getattr(r, "text", str(r)).strip()
        except Exception as e:
            last = e
    raise RuntimeError(f"Speech transcription failed: {last}")
