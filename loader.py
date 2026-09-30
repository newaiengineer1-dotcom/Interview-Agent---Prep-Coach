import re
from pypdf import PdfReader
from docx import Document

def extract_text(uploaded):
    if not uploaded: return ""
    name = getattr(uploaded, "name", "").lower()
    try:
        if name.endswith(".pdf"):
            pages=[]
            for i,p in enumerate(PdfReader(uploaded).pages,1):
                t=p.extract_text() or ""
                if t.strip(): pages.append(f"[PAGE {i}]\n{t}")
            return "\n\n".join(pages).strip()
        if name.endswith(".docx"):
            doc=Document(uploaded)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
        raw=uploaded.getvalue() if hasattr(uploaded,"getvalue") else uploaded
        return raw.decode("utf-8",errors="ignore").strip() if isinstance(raw,bytes) else str(raw).strip()
    except Exception as e:
        raise ValueError(f"Could not read {getattr(uploaded,'name','document')}: {e}")

def chunk_text(text, doc_name, doc_type, size=900, overlap=150):
    clean=re.sub(r"\s+"," ",text).strip()
    chunks=[]
    start=0
    while start < len(clean):
        end=min(len(clean),start+size)
        part=clean[start:end].strip()
        if part: chunks.append({"text":part,"doc_name":doc_name,"doc_type":doc_type,"page":_page(part)})
        if end==len(clean): break
        start=end-overlap
    return chunks

def _page(text):
    m=re.search(r"\[PAGE\s+(\d+)\]",text)
    return int(m.group(1)) if m else None

def build_index(resume_text, jd_text, resume_name="Resume", jd_name="Job Description"):
    chunks=chunk_text(resume_text,resume_name,"resume")+chunk_text(jd_text,jd_name,"jd")
    return RagIndex(chunks)

class RagIndex:
    def __init__(self,chunks):
        self.chunks=chunks
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.v=TfidfVectorizer(stop_words="english",ngram_range=(1,2),max_features=8000)
        corpus=[c["text"] for c in chunks] or ["empty"]
        self.m=self.v.fit_transform(corpus)
    def retrieve(self,query,k=5):
        if not self.chunks: return []
        from sklearn.metrics.pairwise import cosine_similarity
        q=self.v.transform([query])
        sims=cosine_similarity(q,self.m)[0]
        idx=sims.argsort()[::-1][:k]
        return [{**self.chunks[i],"score":round(float(sims[i]),3)} for i in idx if sims[i]>0.02]
    def context(self,query,k=5):
        rows=self.retrieve(query,k)
        if not rows: return "No matching evidence found."
        return "\n\n---\n\n".join(f"[{r['doc_type'].upper()} | {r['doc_name']} | page={r['page']}]\n{r['text']}" for r in rows)
