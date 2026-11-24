import hashlib, re, json
from pathlib import Path
import fitz, httpx
from app.config import settings
from app.models import Paper, Section, Paragraph, Visual, Extraction

def parse_pdf(path: Path, object_dir: Path) -> Paper:
    raw=path.read_bytes(); digest=hashlib.sha256(raw).hexdigest(); pid=digest[:24]
    # Working local fallback; MinerU adapter can replace this with richer layout output.
    doc=fitz.open(stream=raw,filetype="pdf")
    sections=[Section(id=f"{pid}:s0",title="Document",order=0)]
    paragraphs=[]; visuals=[]
    dest=object_dir/pid; dest.mkdir(parents=True,exist_ok=True)
    for page_num,page in enumerate(doc,1):
        blocks=page.get_text("blocks",sort=True)
        for idx,block in enumerate(blocks):
            if len(block)<5 or not isinstance(block[4],str):continue
            text=" ".join(block[4].split())
            if len(text)<30:continue
            paragraphs.append(Paragraph(id=f"{pid}:p{page_num}-{idx}",section_id=sections[0].id,text=text,page=page_num))
        for j,img in enumerate(page.get_images(full=True)):
            try:
                pix=fitz.Pixmap(doc,img[0]);
                if pix.n>4:pix=fitz.Pixmap(fitz.csRGB,pix)
                filename=dest/f"page{page_num}-image{j}.png";pix.save(filename)
                visuals.append(Visual(id=f"{pid}:v{page_num}-{j}",section_id=sections[0].id,kind="Figure",path=str(filename),page=page_num))
            except Exception:pass
    title=doc.metadata.get("title") or path.stem
    doc.close()
    return Paper(id=pid,title=title,sha256=digest,source_name=path.name,sections=sections,paragraphs=paragraphs,visuals=visuals)

def grobid_references(path: Path):
    # GROBID accepts full PDF for best bibliography and DOI resolution.
    try:
        with httpx.Client(timeout=180) as client:
            r=client.post(settings.grobid_url.rstrip('/')+'/api/processReferences',files={"input":(path.name,path.read_bytes(),"application/pdf")})
            r.raise_for_status()
        from xml.etree import ElementTree as ET
        root=ET.fromstring(r.text);ns={"t":"http://www.tei-c.org/ns/1.0"}
        refs=[]
        for b in root.findall('.//t:biblStruct',ns):
            doi=next((x.text for x in b.findall('.//t:idno',ns) if x.attrib.get('type','').lower()=='doi'),None)
            arxiv=next((x.text for x in b.findall('.//t:idno',ns) if x.attrib.get('type','').lower()=='arxiv'),None)
            title=b.find('.//t:title',ns)
            refs.append({"doi":doi,"arxiv_id":arxiv,"title":title.text if title is not None else None})
        return refs
    except (httpx.HTTPError,ET.ParseError):return []

def extract_entities(text: str) -> Extraction:
    if not settings.gemini_api_key:return Extraction()
    from google import genai
    client=genai.Client(api_key=settings.gemini_api_key)
    prompt=("Extract scientific entities and grounded relations from the text. "
        "Use only evidence explicitly present in text; relation endpoints must match extracted entity names. "
        "Allowed entity kinds: Method, Dataset, Model, Metric, Task, Concept. "
        "Allowed predicates: IMPROVES, USES, EVALUATES_ON, OUTPERFORMS, RELATED_TO.\nTEXT:\n"+text[:12000])
    response=client.models.generate_content(model=settings.gemini_model,contents=prompt,config={"response_mime_type":"application/json","response_schema":Extraction})
    return Extraction.model_validate_json(response.text)

def mineru_parse(path: Path, object_dir: Path) -> Paper:
    # Endpoint contract: POST /parse multipart(file) -> Paper-compatible JSON.
    # Adapt the response mapping to your pinned MinerU deployment/version.
    if not settings.mineru_url:return parse_pdf(path,object_dir)
    with httpx.Client(timeout=600) as client:
        r=client.post(settings.mineru_url.rstrip('/')+'/parse',files={"file":(path.name,path.read_bytes(),"application/pdf")})
        r.raise_for_status()
    return Paper.model_validate(r.json())
