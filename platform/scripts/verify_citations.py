"""Recheck short excerpts against original PDFs/DOCX, never cached transcripts.

This verifies text/locations/source hashes, not interpretation of a citation.
Run from platform: .venv/Scripts/python.exe scripts/verify_citations.py
"""
from pathlib import Path
import hashlib
import json
import re
import sys
import unicodedata
import fitz
from docx import Document

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent


def normalize(value):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', value)).strip()


def run():
    specification = json.loads((BASE / 'scripts/citation-specification.json').read_text(encoding='utf-8'))
    sources, hashes, rows = {}, {}, []
    for citation in specification:
        path = ROOT / citation['file']
        if citation['file'] not in sources:
            sources[citation['file']] = fitz.open(path) if citation['type'] == 'pdf' else Document(path)
            hashes[citation['file']] = hashlib.sha256(path.read_bytes()).hexdigest()
        source = sources[citation['file']]
        assert hashes[citation['file']] == citation['source_sha256'], f'Source changed: {path.name}'
        if citation['type'] == 'pdf':
            location = f"PDF page {citation['pdf_page']}"
            text = source[citation['pdf_page'] - 1].get_text()
        else:
            location = f"paragraph {citation['paragraph']} (one-based, including blanks)"
            text = source.paragraphs[citation['paragraph'] - 1].text
        assert normalize(citation['excerpt']) in normalize(text), f"Excerpt missing: {citation['id']}, {location}"
        rows.append({**citation, 'verified': True,
                     'verification_method': 'Original source; PyMuPDF/python-docx; SHA-256; NFKC and whitespace normalization'})
        print(f"{citation['id']}: {location} verified")
    for source in sources.values():
        if isinstance(source, fitz.Document):
            source.close()
    (BASE / 'artifacts/citation-evidence.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(rows)} excerpts verified in {len(sources)} original documents.')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run()
