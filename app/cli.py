import argparse,json
from pathlib import Path
from app.ingest import ingest
from app.answer import answer
p=argparse.ArgumentParser();p.add_argument('command',choices=['ingest','query']);p.add_argument('value');p.add_argument('--mode',default='auto')
a=p.parse_args()
print(json.dumps(ingest(Path(a.value)) if a.command=='ingest' else answer(a.value,a.mode).model_dump(),indent=2))
