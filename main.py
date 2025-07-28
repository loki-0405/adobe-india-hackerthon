import streamlit as st
import json
import fitz  # PyMuPDF
import time
import re
from datetime import datetime
from io import BytesIO


# Set up the page layout and title
st.set_page_config(page_title="Document Analysis Tool", layout="wide")
st.title("PDF Document Analyzer")

# ----------------- PDF Text Extraction Functions ----------------- #

def extract_text_from_pdf(pdf_file):
    """Reads text content from PDF along with formatting details"""
    pdf_doc = fitz.open(stream=pdf_file, filetype="pdf")
    extracted_content = []
    
    # Limit to first 50 pages to avoid very long processing
    max_pages = min(len(pdf_doc), 50)
    
    for current_page in range(max_pages):
        page_blocks = pdf_doc[current_page].get_text("dict")["blocks"]
        
        for block in page_blocks:
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                for text_span in line["spans"]:
                    clean_text = text_span["text"].strip()
                    
                    # Skip empty or very short text fragments
                    if not clean_text or len(clean_text) <= 1:
                        continue
                        
                    extracted_content.append({
                        "text": clean_text,
                        "size": text_span["size"],
                        "font": text_span["font"],
                        "flags": text_span.get("flags", 0),
                        "page": current_page + 1,
                        "bbox": text_span["bbox"]
                    })
    
    pdf_doc.close()
    return extracted_content


# ----------------- Document Structure Analysis ----------------- #

def analyze_document_structure(text_elements):
    """Identifies titles and headings in the document"""
    if not text_elements:
        return [], "No Title Found"
    
    # Calculate average font size for reference
    all_sizes = [item["size"] for item in text_elements]
    average_size = sum(all_sizes) / len(all_sizes)
    
    # Get sorted list of unique font sizes
    unique_font_sizes = sorted(set(all_sizes), reverse=True)
    
    def clean_text(text_string):
        """Normalizes text by removing extra spaces"""
        return re.sub(r'\s+', ' ', text_string.strip())
    
    def could_be_title(text_item, size, page_num, flags_value):
        """Determines if text is likely the document title"""
        # Titles usually appear early in the document
        if page_num > 2:
            return False
        
        # Should be among the largest text in document
        if size < max(all_sizes) * 0.9:
            return False
            
        word_count = len(text_item.split())
        # Titles are typically between 3-25 words
        if word_count < 3 or word_count > 25:
            return False
            
        # Filter out common false positives
        if re.match(r'^\d+\.?\s', text_item):
            return False
        if text_item.lower().startswith(('page', 'chapter')):
            return False
            
        return True
    
    def looks_like_heading(text_item, size, page_num, flags_value):
        """Checks if text matches heading characteristics"""
        normalized_text = clean_text(text_item)
        
        # Length filters for headings
        if len(normalized_text) < 2 or len(normalized_text) > 150:
            return False
            
        word_count = len(normalized_text.split())
        if word_count > 20:  # Too long for a heading
            return False
            
        # Patterns that indicate non-headings
        non_heading_patterns = [
            r'^\d+$', r'^page\s+\d+', r'^figure\s+\d+', 
            r'^table\s+\d+', r'^\w{1,2}$', r'^[^\w\s]+$',
            r'^\d{4}$', r'^www\.', r'@'
        ]
        
        if any(re.match(p, normalized_text.lower()) for p in non_heading_patterns):
            return False
            
        # Formatting clues
        is_bold = bool(flags_value & 16)
        larger_than_normal = size > average_size * 1.15
        
        # Common heading patterns
        heading_patterns = [
            r'^\d+\.?\s+[A-Z]', r'^\d+\.\d+\.?\s+[A-Z]',
            r'^\d+\.\d+\.\d+\.?\s+[A-Z]', r'^\d+\.\d+\.\d+\.\d+\.?\s+[A-Z]',
            r'^[A-Z][a-z]+(\s+[A-Z&][a-z]*)*:?\s*$', r'^[A-Z][A-Z\s&]+:?\s*$',
            r'^Appendix\s+[A-Z]', r'^Phase\s+[IVX]',
            r'^For\s+(each|the)\s+[A-Z]', r'^\d+\.\s+[A-Z]'
        ]
        
        matches_pattern = any(re.match(p, normalized_text) for p in heading_patterns)
        
        # Keywords often found in headings
        common_heading_words = [
            'summary', 'background', 'introduction', 'conclusion',
            'abstract', 'references', 'methodology', 'approach',
            'requirements', 'evaluation', 'timeline', 'milestones',
            'appendix', 'phase', 'business', 'plan'
        ]
        
        contains_keyword = any(w in normalized_text.lower() for w in common_heading_words)
        ends_with_colon = normalized_text.endswith(':')
        
        # Score the heading likelihood
        heading_score = 0
        if is_bold: heading_score += 2
        if matches_pattern: heading_score += 3
        if larger_than_normal: heading_score += 1
        if contains_keyword: heading_score += 2
        if ends_with_colon: heading_score += 1
        if size >= average_size * 1.3: heading_score += 1
        
        return heading_score >= 4
    
    def determine_heading_level(text_item, size, page_num):
        """Classifies heading hierarchy level"""
        clean_text = re.sub(r'\s+', ' ', text_item.strip())
        
        # First check numbering patterns
        if re.match(r'^\d+\.?\s+[A-Z]', clean_text):
            return "H1"
        elif re.match(r'^\d+\.\d+\.?\s+', clean_text):
            return "H2"
        elif re.match(r'^\d+\.\d+\.\d+\.?\s+', clean_text):
            return "H3"
        elif re.match(r'^\d+\.\d+\.\d+\.\d+\.?\s+', clean_text):
            return "H4"
        
        # Special cases
        if re.match(r'^Appendix\s+[A-Z]:', clean_text):
            return "H2"
        elif re.match(r'^Phase\s+[IVX]+:', clean_text):
            return "H3"
        elif re.match(r'^For\s+(each|the)\s+[A-Z]', clean_text):
            return "H4"
        elif re.match(r'^\d+\.\s+[A-Z]', clean_text):
            return "H3"
        
        # Fallback to size-based classification
        if len(unique_font_sizes) >= 4:
            size_rank = unique_font_sizes.index(size) if size in unique_font_sizes else len(unique_font_sizes) - 1
            
            if size_rank == 0:
                return "H1"
            elif size_rank == 1:
                return "H2"
            elif size_rank == 2:
                return "H3"
            else:
                return "H4"
        else:
            # Simple size thresholds
            if size >= average_size * 1.4:
                return "H1"
            elif size >= average_size * 1.25:
                return "H2"
            elif size >= average_size * 1.1:
                return "H3"
            else:
                return "H4"
    
    # Find potential title candidates
    possible_titles = []
    for element in text_elements:
        if could_be_title(element["text"], element["size"], element["page"], element["flags"]):
            possible_titles.append({
                "text": clean_text(element["text"]),
                "size": element["size"],
                "page": element["page"]
            })
    
    # Select the most likely title
    doc_title = "Untitled Document"
    if possible_titles:
        # Prefer larger text on earlier pages
        best_candidate = max(possible_titles, key=lambda x: (x["size"] * 1000 - x["page"]))
        doc_title = best_candidate["text"]
    
    # Identify heading candidates
    potential_headings = []
    processed_texts = set()
    
    for element in text_elements:
        text_cleaned = clean_text(element["text"])
        text_lower = text_cleaned.lower()
        
        # Skip duplicates and the title itself
        if text_lower in processed_texts or text_lower == doc_title.lower():
            continue
        
        if looks_like_heading(element["text"], element["size"], element["page"], element["flags"]):
            heading_type = determine_heading_level(element["text"], element["size"], element["page"])
            potential_headings.append({
                "text": text_cleaned,
                "level": heading_type,
                "page": element["page"],
                "size": element["size"]
            })
            processed_texts.add(text_lower)
    
    # Sort headings by page and size
    potential_headings.sort(key=lambda x: (x["page"], -x["size"]))
    
    # Final filtering of headings
    confirmed_headings = []
    for heading in potential_headings:
        text_content = heading["text"]
        
        # Additional quality checks
        if (len(text_content.split()) >= 2 and \
           not re.match(r'^\d+$', text_content) and \
           not text_content.lower() in ['page', 'figure', 'table'] and \
           len(text_content.strip()) >= 3):
            confirmed_headings.append({
                "level": heading["level"],
                "text": text_content,
                "page": heading["page"]
            })
    
    return confirmed_headings, doc_title


# ----------------- Section Splitting Function ----------------- #

def split_document_by_sections(pdf_file, filename):
    """Divides PDF into logical sections by page"""
    pdf_document = fitz.open(stream=pdf_file, filetype="pdf")
    document_sections = []

    for page_num in range(len(pdf_document)):
        page_content = []
        page_data = pdf_document[page_num].get_text("dict")
        
        for content_block in page_data["blocks"]:
            if "lines" not in content_block:
                continue
                
            for text_line in content_block["lines"]:
                for text_span in text_line["spans"]:
                    line_content = text_span["text"].strip()
                    if line_content:
                        page_content.append(line_content)

        full_page_text = " ".join(page_content)
        document_sections.append({
            "document": filename,
            "start_page": page_num + 1,
            "end_page": page_num + 1,
            "section_title": full_page_text[:80],
            "refined_text": full_page_text,
            "level": "auto"
        })

    pdf_document.close()
    return document_sections


# ----------------- User Interface Setup ----------------- #

# Create two tabs for different functionalities
tab1, tab2 = st.tabs(["Document Structure", "Persona Analysis"])

# ======= Document Structure Tab ======= #
with tab1:
    st.subheader("PDF Structure Extraction")
    uploaded_file = st.file_uploader("Choose PDF file", type=["pdf"], key="pdf-uploader")
    
    if uploaded_file:
        st.write(f"**Selected file:** {uploaded_file.name}")
        if st.button("Analyze Document Structure"):
            progress = st.progress(0)
            for percent in range(101):
                time.sleep(0.01)
                progress.progress(percent)
            
            file_stream = BytesIO(uploaded_file.read())
            extracted_text = extract_text_from_pdf(file_stream)
            document_headings, main_title = analyze_document_structure(extracted_text)
            
            st.success("Analysis complete!")
            st.markdown(f"### Document Title: {main_title}")
            st.markdown("### Document Headings")
            
            for heading in document_headings:
                st.write(f"- **Page {heading['page']}** [{heading['level']}]: {heading['text']}")
            
            # Prepare JSON output
            result_data = {
                "title": main_title,
                "outline": document_headings
            }
            
            st.markdown("### Analysis Results (JSON)")
            st.json(result_data)
            
            # Download button for results
            st.download_button(
                label="Download Results",
                data=json.dumps(result_data, indent=2),
                file_name="document_structure.json",
                mime="application/json"
            )

# ======= Persona Analysis Tab ======= #
with tab2:
    st.subheader("Role-Based Document Analysis")
    
    role_input = st.text_input("Your Role (e.g., Project Manager)")
    task_description = st.text_input("Your Task (e.g., Review project timeline)")
    uploaded_files = st.file_uploader("Upload PDF documents", type="pdf", 
                                    accept_multiple_files=True, key="multi-upload")
    
    if role_input and task_description and uploaded_files:
        if st.button("Find Relevant Sections"):
            progress_bar = st.progress(0)
            for pct_complete in range(101):
                time.sleep(0.005)
                progress_bar.progress(pct_complete)
            
            all_doc_sections = []
            for document in uploaded_files:
                doc_stream = BytesIO(document.read())
                all_doc_sections.extend(split_document_by_sections(doc_stream, document.name))
            
            # Create search keywords from inputs
            search_terms = set((task_description + " " + role_input).lower().split())
            important_sections = []
            
            for section in all_doc_sections:
                section_words = set(section["section_title"].lower().split())
                match_count = len(search_terms & section_words)
                
                if match_count:
                    important_sections.append({
                        "document": section["document"],
                        "start_page": section["start_page"],
                        "section_title": section["section_title"],
                        "importance_rank": 0,  # Temporary value
                        "refined_text": section["refined_text"][:1000]
                    })
            
            # Sort and select top sections
            important_sections.sort(key=lambda s: (
                -len(set(s["section_title"].lower().split()) & search_terms),
                s["document"],
                s["start_page"]
            ))
            
            top_sections = important_sections[:5]
            for i, section in enumerate(top_sections, 1):
                section["importance_rank"] = i
            
            st.success(f"Found {len(top_sections)} relevant sections")
            
            for i, section in enumerate(top_sections, 1):
                with st.expander(f"Section {i}: {section['section_title']} (Page {section['start_page']})"):
                    st.write(f"**Document:** {section['document']}")
                    st.write(f"**Relevance Rank:** {section['importance_rank']}")
                    st.write(f"**Content Preview:** {section['refined_text'][:300]}...")
            
            # Prepare final output
            analysis_results = {
                "metadata": {
                    "documents_analyzed": [doc.name for doc in uploaded_files],
                    "user_role": role_input,
                    "user_task": task_description,
                    "analysis_date": datetime.now().isoformat()
                },
                "relevant_sections": [
                    {
                        "document": sec["document"],
                        "section_title": sec["section_title"],
                        "rank": sec["importance_rank"],
                        "page": sec["start_page"]
                    } for sec in top_sections
                ],
                "section_contents": [
                    {
                        "document": sec["document"],
                        "content_sample": sec["refined_text"].strip(),
                        "page": sec["start_page"]
                    } for sec in top_sections
                ]
            }
            
            st.subheader("Analysis Report (JSON Format)")
            st.json(analysis_results)
            
            st.download_button(
                label="Download Full Report",
                data=json.dumps(analysis_results, indent=2),
                file_name="document_analysis_report.json",
                mime="application/json"
            )