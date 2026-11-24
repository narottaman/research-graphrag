from app.config import settings
from app.models import Evidence
from app.stores import GraphStore,TextStore,VisualStore

def rrf(lists,k=60):
    scores={}
    for group in lists:
        for rank,id in enumerate(group,1):scores[id]=scores.get(id,0)+1/(k+rank)
    return sorted(scores,key=lambda x:-scores[x])

def choose_mode(question,requested):
    if requested!='auto':return requested
    return 'deep' if any(x in question.lower() for x in ('compare','evolution','across papers','survey','relationship','trend','why')) else 'shallow'

def retrieve(question,mode='auto',limit=None):
    mode=choose_mode(question,mode);limit=limit or settings.retrieval_limit
    graph=GraphStore()
    try:
        text=TextStore()
        graph_ids=graph.search(question,deep=(mode=='deep'),limit=limit*3)
        para=text.query('paragraphs',question,n=limit*3)
        tables=text.query('tables',question,n=limit*2)
        visual=[]
        if settings.enable_visual:
            from app.visual import encode_query
            visual=VisualStore().search(encode_query(question),limit=limit*2)
        visual_ids=[x['meta']['source_id'] for x in visual]
        ordered=rrf([graph_ids,[x['id'] for x in para],[x['id'] for x in tables],visual_ids])[:limit]
        graph_meta=graph.metadata(ordered)
        cache={x['id']:x for x in para+tables}
        for x in text.get('paragraphs',[i for i in ordered if i not in cache]):cache[x['id']]=x
        for x in text.get('tables',[i for i in ordered if i not in cache]):cache[x['id']]=x
        evidence=[]
        for id in ordered:
            item=cache.get(id,{})
            m=graph_meta.get(id,{})
            meta=item.get('meta',{})
            if not m and not meta:continue
            evidence.append(Evidence(id=id,paper_id=m.get('paper_id') or meta.get('paper_id',''),text=item.get('text') or m.get('caption') or '',page=m.get('page') or meta.get('page',1),kind=meta.get('kind') or (m.get('labels') or ['Figure'])[-1],path=m.get('path'),score=1/(1+ordered.index(id))))
        return evidence,mode
    finally:graph.close()
