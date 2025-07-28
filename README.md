# Adobe India Hackathon 2025 – Connecting the Dots Challenge

## 🚀 Overview

This repository contains solutions for **Round 1A** (PDF Outline Extraction) and **Round 1B** (Persona-Based PDF Analysis) of the Adobe India Hackathon 2025. The goal is to transform static PDFs into intelligent, interactive documents using structured extraction and analysis.

---

## 📁 Folder Structure

├── Dockerfile # Docker config file
├── .dockerignore # Ignore virtual env and build files
├── requirements # Python dependencies list (rename to requirements.txt)
├── main.py # Main script for Challenge 1A (Outline Extraction)
├── main2.py # Script for Challenge 1B (Persona-based Analysis)
├── main3.py # Optional UI module (e.g., Streamlit or Flask app)
├── venv/ # Virtual environment (ignored in Docker)
├── README.md # This documentation file
├── README-1A.md # Separate README for Challenge 1A
├── README-1B.md # Separate README for Challenge 1B
└── approach_explanation.md # Methodology write-up (300–500 words)


---

## 🧠 Challenge 1A – PDF Outline Extraction

### 🎯 Objective

Extract a structured outline (Title, H1, H2, H3 headings with page numbers) from input PDF files and output them in JSON format.

### ✅ Requirements

- Input: PDF files (up to 50 pages) in `/app/input`
- Output: JSON files in `/app/output`, matching schema
- No hardcoded content, network calls, or dependencies over 200MB
- Runtime < 10 seconds, fully offline, CPU-only

### 🏗️ Build and Run


docker build --platform linux/amd64 -t outline-extractor .
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output:/app/output --network none outline-extractor


🤖 Challenge 1B – Persona-Based Document Analysis
🎯 Objective
Analyze multiple documents based on a given persona and job-to-be-done, extracting the most relevant sections and ranking them.

✅ Requirements
Input:

PDFs

Persona description

Job definition

Output: JSON containing:

Metadata

Important sections (with title, page, rank)

Sub-section analysis

Constraints: No internet, < 1GB model, < 60s runtime

🏗️ Build and Run

docker build --platform linux/amd64 -t persona-analyzer .
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none persona-analyzer
📦 Dependencies
Listed in the requirements file (should be renamed to requirements.txt), including:

pdfplumber

pdfminer.six

PyMuPDF

spacy / nltk (for NLP tasks)

jsonschema

streamlit (optional for web UI)

📝 Output Format
Challenge 1A (Example):

{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 },
    { "level": "H3", "text": "History of AI", "page": 3 }
  ]
}
Challenge 1B (Simplified Example):

{
  "metadata": {
    "persona": "Investment Analyst",
    "job_to_be_done": "Analyze R&D trends",
    "timestamp": "2025-07-28T14:00:00Z"
  },
  "extracted_sections": [
    {
      "document": "report2024.pdf",
      "page": 15,
      "section_title": "R&D Spend Analysis",
      "importance_rank": 1
    }
  ],
  "sub_section_analysis": [
    {
      "document": "report2024.pdf",
      "page": 15,
      "refined_text": "The company increased R&D investment by 15% over 3 years."
    }
  ]
}
📚 Additional Notes
Ensure Dockerfiles are compatible with --platform linux/amd64.

No GPU required.

No internet calls during execution.

Ensure Docker runs successfully on AMD64 CPU with 8 CPUs & 16 GB RAM.

📌 Instructions Recap

# 1A Outline Extractor
docker build -t outline-extractor .
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none outline-extractor

# 1B Persona Analyzer
docker build -t persona-analyzer .
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none persona-analyzer
