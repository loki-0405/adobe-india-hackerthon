# Adobe-India-Hackerthon25

# 🧠 Adobe India Hackathon 2025 – All-In-One Solution

## 🚀 Connecting the Dots Challenge

Welcome to our submission for the Adobe India Hackathon 2025. This repository includes:

- ✅ Challenge 1A: PDF Outline Extraction Engine
- ✅ Challenge 1B: Persona-Driven Document Intelligence System

---

## 📁 Repository Structure

Adobe-Challenge-main/
├── Dockerfile                # Docker config file
├── .dockerignore             # Ignore virtual env and other files
├── requirements              # Python dependencies list (should rename to requirements.txt)
├── main.py                   # Likely main script for PDF outline extraction
├── main2.py                  # Possibly script for Challenge 1B
├── main3.py                  # Possibly script for Streamlit UI or other module
├── venv/                     # Python virtual environment (ignored in Docker)

## 🧠 Challenge 1A – PDF Outline Extraction

### ✅ Objective

Extract structured content from raw PDFs, including:
- Title
- Hierarchical headings: **H1**, **H2**, and **H3**
- Page numbers

### 📦 Build & Run (Dockerized)

# 1. Build the Docker image
docker build --platform linux/amd64 -t adobe-react .

# 2. Run the container (replace $(pwd) with full path if on Windows CMD)

docker run -p 80:80 adobe-react


📝 Output Format (JSON)
json
Copy
Edit
{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 },
    { "level": "H3", "text": "History of AI", "page": 3 }
  ]
}


👤 Challenge 1B – Persona-Driven Document Intelligence
🧩 Objective
Given:

A collection of PDFs (3–10)

A Persona (e.g., researcher, student)

A Job-to-be-done (e.g., summarize, extract key sections)

Your system should:

Understand which sections are relevant based on the persona and task

Output the most important sections with ranks and highlights

📦 Run the Script (Local or in Docker)
Update the Docker CMD to:

CMD ["python", "main2.py"]
Then run similarly as 1A:

# 2. Run the container (replace $(pwd) with full path if on Windows CMD)

docker run -p 80:80 adobe-react

{
  "metadata": {
    "documents": ["file1.pdf", "file2.pdf"],
    "persona": "Investment Analyst",
    "job_to_be_done": "Summarize R&D and revenue trends",
    "timestamp": "2025-07-28T14:32:00Z"
  },
  "sections": [
    {
      "document": "file1.pdf",
      "page": 12,
      "section_title": "Revenue Growth 2023",
      "importance_rank": 1
    }
  ],
  "subsection_analysis": [
    {
      "document": "file2.pdf",
      "page": 18,
      "refined_text": "Company invested 15% in R&D, highest in 5 years..."
    }
  ]
}
🧾 Dependencies
Ensure all dependencies are in requirements.txt:

pdfminer.six
PyPDF2
streamlit           # Optional for UI
🎨 Optional UI – Streamlit (main3.py)
If main3.py is a Streamlit frontend:

Local run:

streamlit run main3.py
Dockerfile (add this CMD if using main3.py in Docker):
dockerfile
Copy
Edit
CMD ["streamlit", "run", "main3.py", "--server.port=8501", "--server.address=0.0.0.0"]
✅ Validation Checklist
 All PDFs in /input processed

 Output JSONs in /output, schema-compliant

 Executes in < 10s (for 50 pages)

 Model (if any) under 200MB

 Internet access disabled

 Fully containerized with Docker


