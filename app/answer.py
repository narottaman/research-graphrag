from app.config import settings
from app.models import Answer
from app.retrieve import retrieve

def answer(question,mode='auto'):
    evidence,chosen=retrieve(question,mode)
    if not evidence:return Answer(answer="No indexed evidence found. I cannot substantiate an answer.",evidence=[],mode=chosen)
    excerpts='\n\n'.join(f"[{i}] paper={e.paper_id} page={e.page} kind={e.kind}\n{e.text[:3500]}" for i,e in enumerate(evidence,1))
    if not settings.gemini_api_key:
        return Answer(answer="Evidence retrieved; configure GEMINI_API_KEY to generate a grounded synthesis.\n\n"+excerpts[:6000],evidence=evidence,mode=chosen)
    from google import genai
    from google.genai import types
    client=genai.Client(api_key=settings.gemini_api_key)
    prompt=("Answer using ONLY the provided evidence. Cite each factual assertion using [number] corresponding to evidence. "
        "State when evidence is insufficient. Do not invent citations.\nQuestion: "+question+"\nEvidence:\n"+excerpts)
    # Images are included only when local evidence paths are available; large files should be downsampled upstream.
    contents=[prompt]
    for e in evidence[:5]:
        if e.path:
            try:
                from pathlib import Path
                data=Path(e.path).read_bytes()
                contents.append(types.Part.from_bytes(data=data,mime_type='image/png'))
            except OSError:pass
    result=client.models.generate_content(model=settings.gemini_model,contents=contents)
    return Answer(answer=result.text or "Model returned no answer.",evidence=evidence,mode=chosen)
