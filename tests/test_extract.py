from pathlib import Path
import fitz
from app.extract import parse_pdf

def test_pdf_fallback(tmp_path):
    doc=fitz.open();page=doc.new_page();page.insert_text((72,72),'A research paper with a sufficiently long paragraph for testing.');path=tmp_path/'sample.pdf';doc.save(path);doc.close()
    paper=parse_pdf(path,tmp_path/'objects')
    assert paper.paragraphs and paper.paragraphs[0].page==1
    assert paper.sha256 and paper.sections
