import pymupdf as fitz
import pytest
from app.parsing import parse_pdf
from app.retrieval import rrf
from app.generation import validate_answer

def test_chunks_cover_text_and_normalized_boxes(tmp_path):
    path = tmp_path / 'test.pdf'
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox((40, 40, 550, 700), 'Attention mechanisms process tokens. ' * 50)
    doc.save(path)
    pages, chunks = parse_pdf(path)
    assert pages == 1 and len(chunks) > 1
    assert all(len(c['text']) <= 500 for c in chunks)
    assert all(0 <= v <= 1 for c in chunks for box in c['bbox'] for v in box)
    assert chunks[0]['text'][-50:] == chunks[1]['text'][:50]

def test_rrf_deduplicates_and_rewards_agreement():
    assert [x['id'] for x in rrf([{'id':1},{'id':2}], [{'id':2},{'id':3}])] == [2,1,3]

def test_unknown_citation_rejected():
    with pytest.raises(ValueError):
        validate_answer({'answer':'claim', 'citations':['chunk_9']}, {'chunk_1'})

def test_empty_citations_rejected():
    with pytest.raises(ValueError):
        validate_answer({'answer':'claim', 'citations':[]}, {'chunk_1'})

@pytest.mark.asyncio
async def test_low_relevance_short_circuits_generation(monkeypatch):
    from app import main
    class Connection:
        async def fetchval(self,*args): return 1
    class Acquire:
        async def __aenter__(self): return Connection()
        async def __aexit__(self,*args): pass
    class Pool:
        def acquire(self): return Acquire()
    async def retrieval(*args): return [{'score':0.1}]
    async def generation(*args): pytest.fail('low relevance should short circuit')
    main.app.state.pool=Pool()
    main.app.state.provider=object()
    monkeypatch.setattr(main,'retrieve',retrieval)
    monkeypatch.setattr(main,'generate',generation)
    result=await main.ask(main.Question(document_id=1,question='unknown topic'))
    assert result['refused'] and result['citations']==[]

@pytest.mark.asyncio
async def test_provider_errors_return_502(monkeypatch):
    from app import main
    from openai import APIConnectionError
    import httpx
    from fastapi import HTTPException
    class Connection:
        async def fetchval(self,*args): return 1
    class Acquire:
        async def __aenter__(self): return Connection()
        async def __aexit__(self,*args): pass
    class Pool:
        def acquire(self): return Acquire()
    async def retrieval(*args): return [{'score':0.9}]
    async def generation(*args): raise APIConnectionError(request=httpx.Request('POST','https://example.com'))
    main.app.state.pool=Pool()
    main.app.state.provider=object()
    monkeypatch.setattr(main,'retrieve',retrieval)
    monkeypatch.setattr(main,'generate',generation)
    with pytest.raises(HTTPException) as error:
        await main.ask(main.Question(document_id=1,question='question'))
    assert error.value.status_code==502

@pytest.mark.asyncio
async def test_citations_use_database_coordinates(monkeypatch):
    from app import main
    from app.generation import GroundedAnswer
    class Connection:
        async def fetchval(self,*args): return 1
    class Acquire:
        async def __aenter__(self): return Connection()
        async def __aexit__(self,*args): pass
    class Pool:
        def acquire(self): return Acquire()
    async def retrieval(*args): return [{'id':42,'text':'Evidence','page_no':3,'bbox':'[[0.1,0.2,0.8,0.4]]','score':0.95}]
    async def generation(*args): return GroundedAnswer(answer='Claim',citations=['chunk_1'])
    main.app.state.pool=Pool()
    main.app.state.provider=object()
    monkeypatch.setattr(main,'retrieve',retrieval)
    monkeypatch.setattr(main,'generate',generation)
    result=await main.ask(main.Question(document_id=1,question='question'))
    assert result['citations'][0]['chunk_id']==42
    assert result['citations'][0]['page_no']==3
    assert result['citations'][0]['bbox']==[[0.1,0.2,0.8,0.4]]

def test_explicit_evidence_refusal_is_valid():
    result=validate_answer({'answer':'Evidence insufficient','citations':[],'refused':True},{'chunk_1'})
    assert result.refused
