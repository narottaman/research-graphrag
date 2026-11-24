from fastapi import FastAPI,UploadFile,File,HTTPException
from pathlib import Path
import tempfile
from app.config import settings
from app.models import Query,Answer
from app.answer import answer
from app.ingest import ingest
app=FastAPI(title="Research GraphRAG",version="0.1.0")
@app.get('/health/live')
def live():return {"status":"ok"}
@app.post('/query',response_model=Answer)
def query(q:Query):return answer(q.question,q.mode)
@app.post('/ingest')
async def upload(file:UploadFile=File(...)):
    if not file.filename or not file.filename.lower().endswith('.pdf'):raise HTTPException(400,'PDF required')
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'upload.pdf';size=0
        with path.open('wb') as out:
            while chunk:=await file.read(1024*1024):
                size+=len(chunk)
                if size>settings.max_upload_mb*1024*1024:raise HTTPException(413,'PDF too large')
                out.write(chunk)
        if not path.read_bytes()[:5]==b'%PDF-':raise HTTPException(400,'Invalid PDF header')
        return ingest(path)
