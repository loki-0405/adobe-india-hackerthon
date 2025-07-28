# Approach Explanation – Adobe India Hackathon 2025

## 🧠 Challenge 1A: PDF Outline Extraction

### Objective
The goal of Challenge 1A is to extract a **structured outline** from a given PDF, including the **title**, and hierarchical **headings (H1, H2, H3)** with page numbers. The solution must run **offline inside a Docker container**, complete within **10 seconds** for a 50-page PDF, and produce a clean, JSON-formatted output.

### Methodology

We use a hybrid heuristic-based technique leveraging **layout analysis and font features**:

1. **Text Extraction**:
   - We use `pdfminer.six` and `PyMuPDF` (`fitz`) to extract text and associated font properties like size, weight, and position.

2. **Title Detection**:
   - The **title** is assumed to be the largest and boldest text block on the **first page** (often centered).
   - We filter out headers/footers using position thresholds.

3. **Heading Level Inference**:
   - **H1**: Larger font, bold, full line width, near top margin.
   - **H2**: Medium font, bold or semi-bold, sub-section-like pattern.
   - **H3**: Smaller bold text, indented or prefixed with bullets/numbers.

4. **Noise Removal**:
   - We filter out repeated headers/footers and watermarks using positional consistency.

5. **JSON Output**:
   - We structure the results with proper `"level"`, `"text"`, and `"page"` fields, as per the output schema.

---

## 👤 Challenge 1B: Persona-Driven Document Analysis

### Objective
Given a set of related PDFs, a **persona**, and a **job-to-be-done**, extract and prioritize the most relevant **sections and sub-sections** for the given user goal.

### Methodology

This is a content understanding task. Our pipeline works as follows:

1. **Preprocessing**:
   - Extract all sections and text blocks using a parser similar to Challenge 1A.
   - Clean and tokenize the content.

2. **Persona & Job Understanding**:
   - The provided **persona** and **task** are treated as queries.
   - We use **TF-IDF vectorization** and **cosine similarity** to compute semantic similarity between section texts and the job intent.

3. **Ranking**:
   - Each section and sub-section is scored and assigned an **importance_rank** based on similarity.
   - We also consider structural depth (e.g., H1 vs H3) to favor higher-level insights.

4. **Output Generation**:
   - The final JSON includes metadata, ranked section titles with page numbers, and highlighted text snippets relevant to the job.

---

## 🐳 Docker & Execution

The solution is fully containerized with Docker. It meets all hardware and runtime constraints (CPU only, ≤1GB RAM, ≤200MB model if used).

### Build Command

docker build --platform linux/amd64 -t adobe-outline .


docker run -p 80:80 adobe-react


