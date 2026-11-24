"""Offline Leiden clustering on a paper citation projection; optional dependencies."""
from app.stores import GraphStore,TextStore
from app.config import settings

def rebuild():
    import igraph as ig, leidenalg
    graph=GraphStore()
    try:
        with graph.driver.session() as s:
            rows=list(s.run('MATCH (a:Paper)-[:CITES]->(b:Paper) RETURN a.id AS a,b.id AS b'))
            papers=[r['id'] for r in s.run('MATCH (p:Paper) RETURN p.id AS id')]
        if not papers:return []
        index={id:i for i,id in enumerate(papers)}
        g=ig.Graph(n=len(papers),edges=[(index[r['a']],index[r['b']]) for r in rows],directed=False)
        partition=leidenalg.find_partition(g,leidenalg.RBConfigurationVertexPartition,seed=42)
        summaries=[]
        for community,members in enumerate(partition):
            ids=[papers[i] for i in members]
            with graph.driver.session() as s:
                titles=[r['title'] for r in s.run('MATCH (p:Paper) WHERE p.id IN $ids RETURN p.title AS title LIMIT 40',ids=ids)]
            summary='Topic cluster containing: '+ '; '.join(titles)
            if settings.gemini_api_key:
                from google import genai
                try:
                    summary=genai.Client(api_key=settings.gemini_api_key).models.generate_content(model=settings.gemini_model,contents='Summarize the research theme shared by these paper titles; avoid unsupported claims: '+summary).text or summary
                except Exception:pass
            cid=f'community:{community}'
            with graph.driver.session() as s:
                s.run('MERGE (c:Community {id:$cid}) SET c.summary=$summary WITH c MATCH (p:Paper) WHERE p.id IN $ids MERGE (p)-[:IN_COMMUNITY]->(c)',cid=cid,summary=summary,ids=ids).consume()
            summaries.append((cid,summary))
        store=TextStore()
        store.upsert('communities',[x[0] for x in summaries],[x[1] for x in summaries],[{'kind':'Community'} for _ in summaries])
        return summaries
    finally:graph.close()
if __name__=='__main__':print(len(rebuild()))
