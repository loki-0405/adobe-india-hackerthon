import streamlit as st
import json
import fitz  # PyMuPDF
import time
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Challenge 1 - Document Insights", layout="wide")
st.title("📘 Adobe GenAI Challenge 1: Document Analysis")

# ---------- PDF Text Extraction ---------- #
def extract(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    out = []
    for i in range(min(len(doc), 50)):
        for blk in doc[i].get_text("dict")["blocks"]:
            if "lines" in blk:
                for ln in blk["lines"]:
                    for sp in ln["spans"]:
                        out.append({"text": sp["text"].strip(), "size": sp["size"], "font": sp["font"], "page": i + 1})
    doc.close()
    return out

# ---------- Heading Detection ---------- #
def detect(data):
    if not data: return [], "Untitled"
    sizes = [x["size"] for x in data]
    avg, mx = sum(sizes)/len(sizes), max(sizes)
    ttl = "Untitled"
    out = []
    for d in data:
        txt, sz, ft = d["text"], d["size"], d["font"].lower()
        if not txt or len(txt) < 3: continue
        if sz >= mx * 0.95 and ttl == "Untitled": ttl = txt
        elif sz > avg * 1.2 and ("bold" in ft or sz > avg * 1.5):
            lvl = "H1" if sz >= avg * 1.5 else "H2" if sz >= avg * 1.3 else "H3"
            out.append({"level": lvl, "text": txt, "page": d["page"]})
    return out, ttl

# ---------- Section Extractor ---------- #
def extract_sections(file_bytes, filename):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    sections = []
    for i in range(len(doc)):
        content = []
        for blk in doc[i].get_text("dict")["blocks"]:
            if "lines" in blk:
                for ln in blk["lines"]:
                    for sp in ln["spans"]:
                        txt = sp["text"].strip()
                        if txt: content.append(txt)
        full_text = " ".join(content)
        sections.append({
            "document": filename,
            "start_page": i + 1,
            "end_page": i + 1,
            "section_title": full_text[:80],
            "refined_text": full_text,
            "level": "auto"
        })
    doc.close()
    return sections

# ---------- UI Tabs ---------- #
tab1, tab2 = st.tabs(["🔹 Challenge 1A", "🔸 Challenge 1B"])

# ---------- Challenge 1A ---------- #
with tab1:
    st.subheader("📑 PDF Structure")
    pdf = st.file_uploader("Upload PDF", type=["pdf"], key="u1")
    if pdf:
        st.markdown(f"**File:** {pdf.name} ✅")
        if st.button("Extract Structure"):
            pb = st.progress(0)
            for i in range(101): time.sleep(0.01); pb.progress(i)
            file_bytes = BytesIO(pdf.read())
            data = extract(file_bytes)
            out, ttl = detect(data)
            st.success("Extraction Complete")
            st.markdown(f"### 📘 Title: {ttl}")
            st.markdown("### 📋 Outline")
            for x in out:
                st.markdown(f"- **Page {x['page']}** [{x['level']}]: {x['text']}")
            st.markdown("### 📦 JSON Output")
            res = {"title": ttl, "outline": out}
            st.json(res)
            st.download_button("📥 Download JSON", data=json.dumps(res, indent=2), file_name="outline.json", mime="application/json")

# ---------- Challenge 1B ---------- #
with tab2:
    st.header("🔸 Persona-Driven Analysis")
    persona = st.text_input("Enter Persona (e.g., Travel Planner)")
    task = st.text_input("Enter Job to be Done (e.g., Plan a trip for 10 friends)")
    files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True, key="pdf1")

    if persona and task and files:
        if st.button("Run Persona Analysis"):
            pb = st.progress(0)
            for i in range(101): time.sleep(0.005); pb.progress(i)

            all_parts = []
            for f in files:
                file_bytes = BytesIO(f.read())
                all_parts += extract_sections(file_bytes, f.name)

            keys = set((task + " " + persona).lower().split())
            matched = []
            for s in all_parts:
                if s["refined_text"]:
                    twords = set(s["section_title"].lower().split())
                    score = len(twords & keys)
                    if score:
                        matched.append({
                            "document": s["document"],
                            "start_page": s["start_page"],
                            "section_title": s["section_title"],
                            "importance_rank": 0,
                            "refined_text": s["refined_text"][:1000]
                        })

            matched.sort(key=lambda x: (-len(set(x["section_title"].lower().split()) & keys), x["document"], x["start_page"]))
            matched = matched[:5]
            for i, m in enumerate(matched): m["importance_rank"] = i + 1

            st.success(f"Top {len(matched)} sections selected")
            for i, sec in enumerate(matched, 1):
                with st.expander(f"#{i}: {sec['section_title']} (Page {sec['start_page']})"):
                    st.markdown(f"**Document:** {sec['document']}")
                    st.markdown(f"**Rank:** {sec['importance_rank']}")
                    st.markdown(f"**Summary:** {sec['refined_text'][:300]}...")

            output = {
                "metadata": {
                    "input_documents": [f.name for f in files],
                    "persona": persona,
                    "job_to_be_done": task,
                    "processing_timestamp": datetime.now().isoformat()
                },
                "extracted_sections": [
                    {
                        "document": x["document"],
                        "section_title": x["section_title"],
                        "importance_rank": x["importance_rank"],
                        "page_number": x["start_page"]
                    } for x in matched
                ],
                "subsection_analysis": [
                    {
                        "document": x["document"],
                        "refined_text": x["refined_text"].strip(),
                        "page_number": x["start_page"]
                    } for x in matched
                ]
            }

            st.subheader("📄 Output JSON Preview")
            st.json(output)
            st.download_button("📥 Download JSON", data=json.dumps(output, indent=2), file_name="challenge1B_output.json", mime="application/json")
