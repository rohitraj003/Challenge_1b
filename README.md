# Adobe Hackathon – Connecting the Dots (Round 1B)

## 📌 Overview  
This repository contains the solution for **Round 1B: Persona-Driven Document Understanding** of the Adobe India Hackathon.  
It processes PDFs along with pre-generated outlines and ranks content sections based on a given **persona** and **job-to-be-done**.  
The solution runs fully offline, uses a local sentence-transformer model, and meets all hackathon constraints.

---

## 🛠 Approach  
* **PDF Parsing** – Uses `pdfplumber` to extract text page-wise.  
* **Outline Integration** – Reads outline JSON files (from Round 1A) to identify sections; falls back to naive heading detection if no outline exists.  
* **Persona & Job Matching** – Uses a locally stored **SentenceTransformer (all-MiniLM-L6-v2)** to compute semantic similarity between document sections and the persona/job description.  
* **Ranking** – Scores and ranks sections by importance, selecting top-k relevant parts.  
* **Output** – Produces a structured JSON with metadata, extracted sections, and subsection analysis.

---

## ✅ Results & Impact  
* **Contextual ranking** → Highlights sections most relevant to a persona’s needs.  
* **Offline-ready** → Embedding model is stored locally, no internet or GPU required.  
* **Modular pipeline** → Designed to integrate seamlessly with Round 1A outputs.

---

## 🖥 Build & Run  

### 1. Build Docker Image
```bash
docker build --platform linux/amd64 -t round1b:somerandomidentifier .
```

### 2. Run Container
```bash
docker run --rm `
   -v "${PWD}\input3:/app/input:ro" `
   -v "${PWD}\input3_json:/app/input_json:ro" `
   -v "${PWD}\output3:/app/output:rw" `
   --network none `
   round1b:latest
```

**Input:**
- Place your PDFs in the `input/` directory.
- Place corresponding outline JSON files (from Round 1A) in `input_json/`.
- Add `persona.txt` and `job.txt` in `input/` to customize ranking.

**Output:**
- Ranked and structured results will be saved as `round1b_output.json` in the `output/` directory.

---

## 📂 Repository Structure
```
.
├── Dockerfile
├── README.md
├── requirements.txt
├── round1b/
│   ├── main.py
│   └── models/
├── input/          # Place PDFs & persona.txt/job.txt here
├── input_json/     # Place outline JSON files here
└── output/         # Results (round1b_output.json) will be saved here
```
