import os,pytest
from app.stores import GraphStore,TextStore
@pytest.mark.skipif(os.getenv('RUN_INTEGRATION')!='1',reason='Requires docker compose services')
def test_live_stores():
    g=GraphStore()
    try:g.setup()
    finally:g.close()
    t=TextStore();t.upsert('paragraphs',['integration:test'],['graph retrieval integration'],[{'paper_id':'test','page':1,'kind':'Paragraph'}])
    assert any(x['id']=='integration:test' for x in t.query('paragraphs','graph retrieval',5))
