import uuid
from pathlib import Path
from app.config import settings
from app.extract import mineru_parse, grobid_references, extract_entities
from app.stores import GraphStore,TextStore,VisualStore

def ingest(path: Path):
    graph=GraphStore()
    try:
        graph.setup()
        paper=mineru_parse(path,Path(settings.objects_dir))
        paper.references=grobid_references(path)
        graph.save_paper(paper)
        text=TextStore()
        for start in range(0,len(paper.paragraphs),64):
            batch=paper.paragraphs[start:start+64]
            text.upsert("paragraphs",[p.id for p in batch],[p.text for p in batch],[{"paper_id":paper.id,"page":p.page,"kind":"Paragraph"} for p in batch])
        tables=[v for v in paper.visuals if v.kind=="Table" and v.csv_text]
        if tables:text.upsert("tables",[v.id for v in tables],[v.csv_text for v in tables],[{"paper_id":paper.id,"page":v.page,"kind":"Table"} for v in tables])
        for para in paper.paragraphs:
            try:graph.save_extraction(para.id,extract_entities(para.text))
            except Exception as exc:print(f"Entity extraction failed {para.id}: {exc}")
        if settings.enable_visual:
            from app.visual import encode_image
            visual_store=VisualStore()
            for v in paper.visuals:
                vectors=encode_image(v.path)
                visual_store.upsert(str(uuid.uuid5(uuid.NAMESPACE_URL,v.id)),vectors,{"source_id":v.id,"paper_id":paper.id,"page":v.page,"path":v.path,"kind":v.kind})
        return {"paper_id":paper.id,"paragraphs":len(paper.paragraphs),"visuals":len(paper.visuals),"references":len(paper.references)}
    finally:graph.close()
