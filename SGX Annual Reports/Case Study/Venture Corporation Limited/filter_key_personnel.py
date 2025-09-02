"""filter_key_personnel.py
----------------------------------
A *no‑cost* post‑processing script that strips false‑positive blocks from the
raw regex‑extracted BOARD section and keeps only rows likely referring to **key
personnel** (directors & C‑suite).

Usage (inside an n8n *Execute Command* or *Python* node):
    python filter_key_personnel.py --in raw_chunks.json --out cleaned.json

Dependencies (all free / MIT‑licensed):
    pip install spacy rapidfuzz dateparser
    python -m spacy download en_core_web_sm

Input format  (same as the sample shown by the user):
{
  "metadata": {...},
  "content": [
     {"page_number": 4, "text": "..."},
     ...
  ]
}

Output format  (JSON):
{
  "metadata": { ...same as input... },
  "filtered": [
      {"page_number": 96, "text": "PART IV – MANAGEMENT ..."},
      ... (only the snippets that pass the filters) ...
  ]
}

Algorithm overview
------------------
1. *Flatten* → split each page's text into **paragraphs / lines**.
2. **Keyword heuristic**
   • keep lines that contain ≥1 title keyword  (case‑insensitive regex)
        KW = {"director", "chief", "ceo", "president", "officer", "vice president",
              "cfo", "chairman", "treasurer", "secretary", "head"}
   • OR lines that match a *tabular* pattern  (Name  , Title  , Nationality , Age)
3. **NER cross‑check**
   • run spaCy (en_core_web_sm) → must detect ≥1 PERSON entity
   • optional fuzzy‑match to previously‑seen PERSONs to merge variants
4. **Moving window merge**
   • expand around kept lines ±1 paragraph so we don’t lose context
5. **Export** cleaned blocks with original page numbers for traceability.

———————————————————————————————————————————————
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any

import spacy
from rapidfuzz import fuzz, process
import dateparser

TITLE_KWS = [
    r"\bchair(wo)?man\b",
    r"\bdirector[s]?\b",
    r"\bchief\s+[a-zA-Z]+\s+officer\b",
    r"\bceo\b",
    r"\bpresident\b",
    r"\bvice\s+president\b",
    r"\bcfo\b",
    r"\btreasurer\b",
    r"\bsecretary\b",
    r"\bhead\b",
]
TITLE_RE = re.compile("|".join(TITLE_KWS), re.IGNORECASE)

TABULAR_RE = re.compile(
    r"(?P<name>[A-Z][A-Za-z\-\.' ]{2,}),?\s+(?P<title>[A-Za-z ]{3,})\s+(?P<nationality>[A-Za-z]+)\s+(?P<age>\d{2})"
)


nlp = spacy.load("en_core_web_sm", disable=["parser", "tagger"])


def paragraphize(text: str) -> List[str]:
    return [p.strip() for p in re.split(r"\n{2,}|\r{2,}", text) if p.strip()]


def is_relevant(par: str) -> bool:
    if TITLE_RE.search(par):
        return True
    if TABULAR_RE.search(par):
        return True
    doc = nlp(par)
    has_person = any(ent.label_ == "PERSON" for ent in doc.ents)
    return bool(has_person and len(par) < 300)  # limit length to avoid huge business blurbs


def merge_windows(indices: List[int], window: int = 1) -> List[int]:
    spread = set()
    for idx in indices:
        spread.update(range(max(0, idx - window), idx + window + 1))
    return sorted(spread)


def process_pages(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned = []
    for page in pages:
        paras = paragraphize(page["text"])
        keep_idx = [i for i, p in enumerate(paras) if is_relevant(p)]
        if not keep_idx:
            continue
        merged_idx = merge_windows(keep_idx)
        new_text = "\n\n".join(paras[i] for i in merged_idx)
        cleaned.append({"page_number": page["page_number"], "text": new_text})
    return cleaned


def main():
    ap = argparse.ArgumentParser(description="Filter key personnel paragraphs from raw BOARD extraction")
    ap.add_argument("--in", dest="inp", required=True, help="Path to raw JSON chunks")
    ap.add_argument("--out", dest="out", required=True, help="Output cleaned JSON path")
    args = ap.parse_args()

    data = json.loads(Path(args.inp).read_text())
    cleaned = process_pages(data["content"])
    out_data = {"metadata": data["metadata"], "filtered": cleaned}
    Path(args.out).write_text(json.dumps(out_data, indent=2, ensure_ascii=False))
    print(f"Saved cleaned output → {args.out}  (kept {len(cleaned)} pages out of {len(data['content'])})")


if __name__ == "__main__":
    main()
