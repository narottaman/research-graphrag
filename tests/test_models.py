from app.models import Extraction,Entity,Relation,Query
from app.retrieve import rrf,choose_mode
from pydantic import ValidationError
import pytest

def test_extraction_validation():
    e=Extraction(entities=[Entity(name='BERT',kind='Model')],relations=[])
    assert e.entities[0].name=='BERT'
    with pytest.raises(ValidationError): Entity(name='bad',kind='Unknown')
def test_rrf_merges_rankings():
    assert rrf([['a','b'],['b','c']])[0]=='b'
def test_router():
    assert choose_mode('Compare methods across papers','auto')=='deep'
    assert choose_mode('Define attention','auto')=='shallow'
def test_query_minimum_length():
    with pytest.raises(ValidationError):Query(question='a')
