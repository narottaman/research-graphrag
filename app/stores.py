from pathlib import Path
from neo4j import GraphDatabase
import chromadb
from qdrant_client import QdrantClient, models
from app.config import settings
from app.embedding import embed

class GraphStore:
    def __init__(self):
        self.driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    def close(self): self.driver.close()
    def setup(self):
        statements = [
            "CREATE CONSTRAINT paper_id IF NOT EXISTS FOR (n:Paper) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT section_id IF NOT EXISTS FOR (n:Section) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT paragraph_id IF NOT EXISTS FOR (n:Paragraph) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT figure_id IF NOT EXISTS FOR (n:Figure) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT table_id IF NOT EXISTS FOR (n:Table) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE",
            "CREATE INDEX paper_doi IF NOT EXISTS FOR (n:Paper) ON (n.doi)",
            "CREATE INDEX paper_arxiv IF NOT EXISTS FOR (n:Paper) ON (n.arxiv_id)",
        ]
        with self.driver.session() as s:
            for stmt in statements: s.run(stmt).consume()
    def save_paper(self, paper):
        with self.driver.session() as s:
            s.run("MERGE (p:Paper {id:$id}) SET p.title=$title,p.sha256=$sha,p.source_name=$source,p.doi=$doi,p.arxiv_id=$arxiv",id=paper.id,title=paper.title,sha=paper.sha256,source=paper.source_name,doi=paper.doi,arxiv=paper.arxiv_id).consume()
            for sec in paper.sections:
                s.run("MATCH (p:Paper {id:$pid}) MERGE (s:Section {id:$sid}) SET s.title=$title,s.ordinal=$ord MERGE (p)-[:CONTAINS]->(s)",pid=paper.id,sid=sec.id,title=sec.title,ord=sec.order).consume()
            for para in paper.paragraphs:
                s.run("MATCH (s:Section {id:$sid}) MERGE (n:Paragraph {id:$id}) SET n.page=$page,n.chroma_id=$id,n.paper_id=$pid MERGE (s)-[:CONTAINS]->(n)",sid=para.section_id,id=para.id,page=para.page,pid=paper.id).consume()
            for v in paper.visuals:
                if v.kind not in ("Figure","Table"): continue
                label = v.kind  # validated enum; never arbitrary Cypher
                s.run(f"MATCH (s:Section {{id:$sid}}) MERGE (n:{label} {{id:$id}}) SET n.page=$page,n.path=$path,n.caption=$caption,n.qdrant_id=$id,n.chroma_id=$id,n.paper_id=$pid MERGE (s)-[:CONTAINS]->(n)",sid=v.section_id,id=v.id,page=v.page,path=v.path,caption=v.caption,pid=paper.id).consume()
            for ref in paper.references:
                doi=(ref.get("doi") or "").lower().strip()
                arxiv=(ref.get("arxiv_id") or "").strip()
                if doi or arxiv:
                    s.run("MATCH (a:Paper {id:$id}) MATCH (b:Paper) WHERE b.id <> a.id AND (($doi <> '' AND toLower(b.doi)=$doi) OR ($arxiv <> '' AND b.arxiv_id=$arxiv)) MERGE (a)-[:CITES]->(b)",id=paper.id,doi=doi,arxiv=arxiv).consume()
    def save_extraction(self, paragraph_id, extraction):
        with self.driver.session() as s:
            for e in extraction.entities:
                key=e.kind.lower()+":"+e.name.strip().casefold()
                s.run("MATCH (p:Paragraph {id:$pid}) MERGE (e:Entity {id:$key}) SET e.name=$name,e.kind=$kind MERGE (p)-[:MENTIONS]->(e)",pid=paragraph_id,key=key,name=e.name,kind=e.kind).consume()
            lookup={e.name.casefold():e for e in extraction.entities}
            for r in extraction.relations:
                a=lookup.get(r.source.casefold()); b=lookup.get(r.target.casefold())
                if not a or not b: continue
                ak=a.kind.lower()+":"+a.name.strip().casefold(); bk=b.kind.lower()+":"+b.name.strip().casefold()
                s.run("MATCH (a:Entity {id:$ak}),(b:Entity {id:$bk}),(p:Paragraph {id:$pid}) MERGE (a)-[r:RELATES {predicate:$predicate,source_paragraph:$pid}]->(b) SET r.evidence=$evidence",ak=ak,bk=bk,pid=paragraph_id,predicate=r.predicate,evidence=r.evidence).consume()
    def search(self, query, deep=False, limit=30):
        # Entity lexical seed; vector retrieval independently handles missed mentions.
        cypher = """MATCH (e:Entity) WHERE toLower(e.name) CONTAINS toLower($term)
        MATCH (p:Paragraph)-[:MENTIONS]->(e)
        OPTIONAL MATCH (s:Section)-[:CONTAINS]->(p)
        RETURN DISTINCT p.id AS id LIMIT $limit"""
        terms=[t for t in query.split() if len(t)>4][:5]
        ids=[]
        with self.driver.session() as s:
            for term in terms:
                ids += [r['id'] for r in s.run(cypher,term=term,limit=limit)]
            if deep and ids:
                rows=s.run("MATCH (p:Paragraph) WHERE p.id IN $ids MATCH (s:Section)-[:CONTAINS]->(p)<-[:CONTAINS*1..2]-(root) MATCH (root)-[:CONTAINS*1..2]->(other:Paragraph) RETURN DISTINCT other.id AS id LIMIT $limit",ids=ids[:limit],limit=limit)
                ids += [r['id'] for r in rows]
        return list(dict.fromkeys(ids))[:limit]
    def metadata(self, ids):
        if not ids: return {}
        with self.driver.session() as s:
            rows=s.run("MATCH (n) WHERE n.id IN $ids AND (n:Paragraph OR n:Figure OR n:Table) RETURN n.id AS id,n.paper_id AS paper_id,n.page AS page,labels(n) AS labels,n.path AS path",ids=ids)
            return {r['id']:dict(r) for r in rows}

class TextStore:
    def __init__(self):
        client=chromadb.HttpClient(host=settings.chroma_host,port=settings.chroma_port)
        self.collections={name:client.get_or_create_collection(name,metadata={"hnsw:space":"cosine"}) for name in ("paragraphs","tables","communities","entities")}
    def upsert(self, collection, ids, documents, metadata):
        if ids: self.collections[collection].upsert(ids=ids,documents=documents,embeddings=embed(documents),metadatas=metadata)
    def query(self, collection, text, n=20):
        result=self.collections[collection].query(query_embeddings=embed([text]),n_results=n,include=["documents","metadatas","distances"])
        return [{"id":i,"text":d,"meta":m,"score":1-float(dist)} for i,d,m,dist in zip(result['ids'][0],result['documents'][0],result['metadatas'][0],result['distances'][0])]
    def get(self, collection, ids):
        if not ids:return []
        r=self.collections[collection].get(ids=ids,include=["documents","metadatas"])
        return [{"id":i,"text":d,"meta":m} for i,d,m in zip(r['ids'],r['documents'],r['metadatas'])]

class VisualStore:
    def __init__(self): self.client=QdrantClient(url=settings.qdrant_url)
    def ensure(self):
        if not self.client.collection_exists("visuals"):
            self.client.create_collection(collection_name="visuals",vectors_config={"patches":models.VectorParams(size=settings.visual_dim,distance=models.Distance.COSINE,multivector_config=models.MultiVectorConfig(comparator=models.MultiVectorComparator.MAX_SIM))})
    def upsert(self,id,patch_vectors,meta):
        self.ensure()
        self.client.upsert("visuals",points=[models.PointStruct(id=id,vector={"patches":patch_vectors},payload=meta)])
    def search(self,query_vectors,limit=10):
        self.ensure()
        r=self.client.query_points(collection_name="visuals",query=query_vectors,using="patches",limit=limit,with_payload=True)
        return [{"id":str(x.id),"score":x.score,"meta":x.payload} for x in r.points]
