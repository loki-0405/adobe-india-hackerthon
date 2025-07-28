import streamlit as st
import json
import fitz  # PyMuPDF
import time
import re
from datetime import datetime
from io import BytesIO


st.set_page_config(page_title="Challenge 1 - Document Insights", layout="wide")
st.title("📘 Adobe Challenge : Document Analysis")


# ----- Helper: Read Text From PDF ----- #
def get_pdf_content(file_data):
    pdf = fitz.open(stream=file_data, filetype="pdf")
    content = []
    for page_num in range(min(len(pdf), 50)):
        blocks = pdf[page_num].get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text and len(text) > 1:
                            content.append({
                                "text": text,
                                "size": span["size"],
                                "font": span["font"],
                                "flags": span.get("flags", 0),
                                "page": page_num + 1,
                                "bbox": span["bbox"]
                            })
    pdf.close()
    return content


# ----- Precise Helper: Detect Titles and Headings ----- #
def identify_structure(text_items):
    if not text_items:
        return [], "Untitled Document"
    
    font_sizes = [item["size"] for item in text_items]
    avg_size = sum(font_sizes) / len(font_sizes)
    
    # Get font size distribution for better classification
    unique_sizes = sorted(set(font_sizes), reverse=True)
    
    def clean_heading_text(text):
        """Clean and normalize heading text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def is_title_candidate(text, size, page, flags):
        """Identify potential document titles"""
        if page > 2:  # Titles are usually on first 2 pages
            return False
        
        # Must be one of the largest fonts in the document
        if size < max(font_sizes) * 0.9:
            return False
        
        # Should be reasonably long (titles are descriptive)
        word_count = len(text.split())
        if word_count < 3 or word_count > 25:
            return False
        
        # Avoid common non-title patterns
        if re.match(r'^\d+\.?\s', text) or text.lower().startswith(('page', 'chapter')):
            return False
        
        return True
    
    def is_heading_candidate(text, size, page, flags):
        """Identify potential headings with strict criteria"""
        text_clean = clean_heading_text(text)
        
        # Length filters
        if len(text_clean) < 2 or len(text_clean) > 150:
            return False
        
        word_count = len(text_clean.split())
        if word_count > 20:  # Headings shouldn't be too long
            return False
        
        # Skip obvious non-headings
        skip_patterns = [
            r'^\d+$',  # Just numbers
            r'^page\s+\d+',  # Page numbers
            r'^figure\s+\d+',  # Figure references
            r'^table\s+\d+',  # Table references
            r'^\w{1,2}$',  # Very short abbreviations
            r'^[^\w\s]+$',  # Only punctuation
            r'^\d{4}$',  # Years
            r'^www\.',  # URLs
            r'@',  # Email addresses
        ]
        
        if any(re.match(pattern, text_clean.lower()) for pattern in skip_patterns):
            return False
        
        # Check for heading indicators
        is_bold = bool(flags & 16)
        is_larger = size > avg_size * 1.15
        
        # Structural patterns that indicate headings
        heading_patterns = [
            r'^\d+\.?\s+[A-Z]',  # "1. Introduction"
            r'^\d+\.\d+\.?\s+[A-Z]',  # "1.1 Section"
            r'^\d+\.\d+\.\d+\.?\s+[A-Z]',  # "1.1.1 Subsection"
            r'^\d+\.\d+\.\d+\.\d+\.?\s+[A-Z]',  # "1.1.1.1 Sub-subsection"
            r'^[A-Z][a-z]+(\s+[A-Z&][a-z]*)*:?\s*$',  # Title Case with optional colon
            r'^[A-Z][A-Z\s&]+:?\s*$',  # ALL CAPS
            r'^Appendix\s+[A-Z]',  # Appendix sections
            r'^Phase\s+[IVX]',  # Phase sections
            r'^For\s+(each|the)\s+[A-Z]',  # Question-style headings
            r'^\d+\.\s+[A-Z]',  # Numbered list items that are headings
        ]
        
        matches_pattern = any(re.match(pattern, text_clean) for pattern in heading_patterns)
        
        # Common heading keywords
        heading_keywords = [
            'summary', 'background', 'introduction', 'conclusion', 'abstract',
            'references', 'methodology', 'approach', 'requirements', 'evaluation',
            'timeline', 'milestones', 'appendix', 'phase', 'business', 'plan'
        ]
        
        has_keyword = any(keyword in text_clean.lower() for keyword in heading_keywords)
        ends_with_colon = text_clean.endswith(':')
        
        # Scoring system - be more restrictive
        score = 0
        if is_bold: score += 2
        if matches_pattern: score += 3
        if is_larger: score += 1
        if has_keyword: score += 2
        if ends_with_colon: score += 1
        if size >= avg_size * 1.3: score += 1
        
        # Must meet minimum threshold
        return score >= 4
    
    def classify_heading_level(text, size, page):
        """Classify heading levels based on patterns and size"""
        text_clean = clean_heading_text(text)
        
        # Pattern-based classification (most reliable)
        if re.match(r'^\d+\.?\s+[A-Z]', text_clean):
            return "H1"
        elif re.match(r'^\d+\.\d+\.?\s+', text_clean):
            return "H2"
        elif re.match(r'^\d+\.\d+\.\d+\.?\s+', text_clean):
            return "H3"
        elif re.match(r'^\d+\.\d+\.\d+\.\d+\.?\s+', text_clean):
            return "H4"
        
        # Special document-specific patterns
        if re.match(r'^Appendix\s+[A-Z]:', text_clean):
            return "H2"
        elif re.match(r'^Phase\s+[IVX]+:', text_clean):
            return "H3"
        elif re.match(r'^For\s+(each|the)\s+[A-Z]', text_clean):
            return "H4"
        elif re.match(r'^\d+\.\s+[A-Z]', text_clean):  # Numbered items in appendix
            return "H3"
        
        # Size-based classification as fallback
        if len(unique_sizes) >= 4:
            size_rank = unique_sizes.index(size) if size in unique_sizes else len(unique_sizes) - 1
            
            if size_rank == 0:
                return "H1"
            elif size_rank == 1:
                return "H2"
            elif size_rank == 2:
                return "H3"
            else:
                return "H4"
        else:
            # Simple size-based fallback
            if size >= avg_size * 1.4:
                return "H1"
            elif size >= avg_size * 1.25:
                return "H2"
            elif size >= avg_size * 1.1:
                return "H3"
            else:
                return "H4"
    
    # Step 1: Find title candidates
    title_candidates = []
    for item in text_items:
        if is_title_candidate(item["text"], item["size"], item["page"], item["flags"]):
            title_candidates.append({
                "text": clean_heading_text(item["text"]),
                "size": item["size"],
                "page": item["page"]
            })
    
    # Select the best title
    title = "Untitled Document"
    if title_candidates:
        # Prefer larger text on earlier pages
        best_title = max(title_candidates, key=lambda x: (x["size"] * 1000 - x["page"]))
        title = best_title["text"]
    
    # Step 2: Find heading candidates
    heading_candidates = []
    seen_texts = set()
    
    for item in text_items:
        text_clean = clean_heading_text(item["text"])
        text_lower = text_clean.lower()
        
        # Skip duplicates and the title
        if text_lower in seen_texts or text_lower == title.lower():
            continue
        
        if is_heading_candidate(item["text"], item["size"], item["page"], item["flags"]):
            level = classify_heading_level(item["text"], item["size"], item["page"])
            heading_candidates.append({
                "text": text_clean,
                "level": level,
                "page": item["page"],
                "size": item["size"]
            })
            seen_texts.add(text_lower)
    
    # Sort headings by page and then by position
    heading_candidates.sort(key=lambda x: (x["page"], -x["size"]))
    
    # Final filtering - remove any remaining noise
    final_headings = []
    for heading in heading_candidates:
        # Additional quality checks
        text = heading["text"]
        
        # Skip very generic or short text that might have passed through
        if (len(text.split()) >= 2 and 
            not re.match(r'^\d+$', text) and
            not text.lower() in ['page', 'figure', 'table'] and
            len(text.strip()) >= 3):
            final_headings.append({
                "level": heading["level"],
                "text": text,
                "page": heading["page"]
            })
    
    return final_headings, title


# ----- Helper: Section-Wise PDF Parser ----- #
def split_pdf_into_sections(file_data, file_name):
    pdf = fitz.open(stream=file_data, filetype="pdf")
    sections = []

    for page in range(len(pdf)):
        page_text = []
        for block in pdf[page].get_text("dict")["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        line_text = span["text"].strip()
                        if line_text:
                            page_text.append(line_text)

        full_text = " ".join(page_text)
        sections.append({
            "document": file_name,
            "start_page": page + 1,
            "end_page": page + 1,
            "section_title": full_text[:80],
            "refined_text": full_text,
            "level": "auto"
        })

    pdf.close()
    return sections


# ----- UI Tabs Setup ----- #
tab_structure, tab_analysis = st.tabs(["🔹 Challenge 1A", "🔸 Challenge 1B"])


# ======= Challenge 1A ======= #
with tab_structure:
    st.subheader("📑 Extract PDF Structure")
    uploaded_pdf = st.file_uploader("Upload a PDF file", type=["pdf"], key="structure-upload")

    if uploaded_pdf:
        st.markdown(f"**Uploaded File:** {uploaded_pdf.name}")
        if st.button("Start Extraction"):
            progress_bar = st.progress(0)
            for i in range(101):
                time.sleep(0.01)
                progress_bar.progress(i)

            pdf_stream = BytesIO(uploaded_pdf.read())
            text_data = get_pdf_content(pdf_stream)
            headings_list, detected_title = identify_structure(text_data)

            st.success("Extraction completed.")
            st.markdown(f"### 📘 Detected Title: {detected_title}")
            st.markdown("### 📋 Detected Headings")
            for heading in headings_list:
                st.markdown(f"- **Page {heading['page']}** [{heading['level']}]: {heading['text']}")

            output_data = {
                "title": detected_title,
                "outline": headings_list
            }

            st.markdown("### 📦 JSON Output")
            st.json(output_data)
            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(output_data, indent=2),
                file_name="outline.json",
                mime="application/json"
            )


# ======= Challenge 1B ======= #
with tab_analysis:
    st.header("🔸 Persona-Specific Section Insights")
    user_persona = st.text_input("Enter Persona (e.g., Marketing Manager)")
    job_description = st.text_input("Describe the Task (e.g., Launch a campaign for a new product)")
    multiple_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True, key="analysis-upload")

    if user_persona and job_description and multiple_files:
        if st.button("Run Analysis"):
            progress_bar = st.progress(0)
            for i in range(101):
                time.sleep(0.005)
                progress_bar.progress(i)

            all_sections = []
            for doc in multiple_files:
                stream = BytesIO(doc.read())
                all_sections.extend(split_pdf_into_sections(stream, doc.name))

            keyword_set = set((job_description + " " + user_persona).lower().split())
            relevant_sections = []

            for section in all_sections:
                title_words = set(section["section_title"].lower().split())
                match_score = len(keyword_set & title_words)
                if match_score:
                    relevant_sections.append({
                        "document": section["document"],
                        "start_page": section["start_page"],
                        "section_title": section["section_title"],
                        "importance_rank": 0,  # will update later
                        "refined_text": section["refined_text"][:1000]
                    })

            # Sort and rank top 5
            relevant_sections.sort(key=lambda sec: (-len(set(sec["section_title"].lower().split()) & keyword_set), sec["document"], sec["start_page"]))
            relevant_sections = relevant_sections[:5]
            for idx, sec in enumerate(relevant_sections):
                sec["importance_rank"] = idx + 1

            st.success(f"Top {len(relevant_sections)} relevant sections identified")
            for idx, section in enumerate(relevant_sections, 1):
                with st.expander(f"#{idx}: {section['section_title']} (Page {section['start_page']})"):
                    st.markdown(f"**Document:** {section['document']}")
                    st.markdown(f"**Rank:** {section['importance_rank']}")
                    st.markdown(f"**Summary:** {section['refined_text'][:300]}...")

            final_result = {
                "metadata": {
                    "input_documents": [doc.name for doc in multiple_files],
                    "persona": user_persona,
                    "job_to_be_done": job_description,
                    "processing_timestamp": datetime.now().isoformat()
                },
                "extracted_sections": [
                    {
                        "document": sec["document"],
                        "section_title": sec["section_title"],
                        "importance_rank": sec["importance_rank"],
                        "page_number": sec["start_page"]
                    } for sec in relevant_sections
                ],
                "subsection_analysis": [
                    {
                        "document": sec["document"],
                        "refined_text": sec["refined_text"].strip(),
                        "page_number": sec["start_page"]
                    } for sec in relevant_sections
                ]
            }

            st.subheader("📄 Final Output (JSON Preview)")
            st.json(final_result)
            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(final_result, indent=2),
                file_name="challenge1B_output.json",
                mime="application/json"
            )
