import os, re, json, time, sys
from typing import List, Dict
import pdfplumber
from sentence_transformers import SentenceTransformer, util

# === Paths ===
if len(sys.argv) >= 4:
    PDF_DIR = sys.argv[1]
    OUTLINE_DIR = sys.argv[2]
    OUTPUT_DIR = sys.argv[3]
else:
    PDF_DIR = r"C:/Users/rohit/OneDrive/Desktop/pdf_Persona/input3"
    OUTLINE_DIR = r"C:/Users/rohit/OneDrive/Desktop/pdf_Persona/input3_json"
    OUTPUT_DIR = r"C:/Users/rohit/OneDrive/Desktop/pdf_Persona/output3"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Offline Model Path ===
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "all-MiniLM-L6-v2")
if not os.path.isdir(MODEL_PATH):
    print(f"‼ Model directory not found: {MODEL_PATH}")
    sys.exit(1)

MODEL = SentenceTransformer(MODEL_PATH)

CLEAN_RX = re.compile(r"[^\x00-\x7F]+")
WS_RX = re.compile(r"\s+")

def clean(txt: str) -> str:
    txt = CLEAN_RX.sub(" ", txt)
    return WS_RX.sub(" ", txt).strip()

def load_outline(pdf_name: str) -> Dict | None:
    stem = os.path.splitext(pdf_name)[0]
    candidates = {
        f"{stem}.json",
        f"{stem.replace(' ', '_')}.json",
        f"{stem.replace('_', ' ')}.json"
    }
    for c in candidates:
        p = os.path.join(OUTLINE_DIR, c)
        if os.path.isfile(p):
            with open(p, encoding='utf-8') as fh:
                return json.load(fh)
    return None

HEAD_RX = re.compile(r"^\s*(\d+\.)?[A-Z][A-Za-z0-9 ,:&\-]{0,120}$")

def by_outline(pdf_path: str, out_json: Dict, filename: str) -> List[Dict]:
    secs = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        heads = sorted(out_json.get("outline", []), key=lambda x: x["page"])
        heads.append({"page": total + 1})
        for i, h in enumerate(heads[:-1]):
            start, end = h["page"], heads[i+1]["page"] - 1
            txt = " ".join(clean(pdf.pages[p-1].extract_text() or "") for p in range(start, end+1))
            if txt:
                secs.append({
                    "document": filename,
                    "section_title": h["text"],
                    "page": start,
                    "text": txt
                })
    return secs

def naive_split(pdf_path: str, filename: str) -> List[Dict]:
    secs, cur = [], None
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for line in (page.extract_text() or "").splitlines():
                if HEAD_RX.match(line.strip()):
                    if cur and cur["text"]:
                        secs.append(cur)
                    cur = {"document": filename,
                           "section_title": clean(line),
                           "page": pno,
                           "text": ""}
                else:
                    if cur:
                        cur["text"] += " " + clean(line)
        if cur and cur["text"]:
            secs.append(cur)
    return secs

def rank(sections: List[Dict], persona: str, job: str, top_k: int = 10) -> List[Dict]:
    query = f"{persona} needs to {job}"
    q_emb = MODEL.encode(query, convert_to_tensor=True)
    embs = MODEL.encode([s["text"] for s in sections], convert_to_tensor=True)
    scores = util.cos_sim(q_emb, embs)[0].tolist()
    for s, sc in zip(sections, scores):
        s["score"] = sc
    sections.sort(key=lambda x: x["score"], reverse=True)
    for i, s in enumerate(sections, 1):
        s["importance_rank"] = i
        s.pop("score", None)
    return sections[:top_k]

def main():
    persona_path = os.path.join(PDF_DIR, "persona.txt")
    job_path = os.path.join(PDF_DIR, "job.txt")

    persona = open(persona_path, encoding="utf-8").read().strip() if os.path.exists(persona_path) else "Generic Persona"
    job = open(job_path, encoding="utf-8").read().strip() if os.path.exists(job_path) else "Understand the documents"

    all_secs, pdf_names = [], []
    for pdf in os.listdir(PDF_DIR):
        if not pdf.lower().endswith(".pdf"):
            continue
        pdf_names.append(pdf)
        pdf_path = os.path.join(PDF_DIR, pdf)
        outline = load_outline(pdf)
        secs = by_outline(pdf_path, outline, pdf) if outline else naive_split(pdf_path, pdf)
        all_secs.extend(secs)

    if not all_secs:
        print("‼ No text extracted from any PDF – aborting.")
        return

    ranked = rank(all_secs, persona, job, 10)

    output = {
        "metadata": {
            "input_documents": pdf_names,
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        },
        "extracted_sections": [
            {
                "document": s["document"],
                "section_title": s["section_title"],
                "importance_rank": s["importance_rank"],
                "page_number": s["page"]
            } for s in ranked[:5]
        ],
        "subsection_analysis": [
            {
                "document": s["document"],
                "refined_text": s["text"][:500],
                "page_number": s["page"]
            } for s in ranked[5:]
        ]
    }

    out_path = os.path.join(OUTPUT_DIR, "round1b_output.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=4, ensure_ascii=False)

    print("✅ wrote", out_path)

if __name__ == "__main__":
    main()
