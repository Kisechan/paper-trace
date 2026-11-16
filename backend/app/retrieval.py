import asyncio
import json

def rrf(*rankings):
    scores, rows = {}, {}
    for ranking in rankings:
        for rank, row in enumerate(ranking, 1):
            key = row['id']
            rows[key] = dict(row)
            scores[key] = scores.get(key,0) + 1/(60+rank)
    return [dict(rows[key], rrf_score=scores[key]) for key in sorted(scores, key=lambda k:-scores[k])]

async def retrieve(pool, provider, query, document_id, mode='hybrid'):
    vector = json.dumps((await provider.embed([query]))[0])
    async def dense():
        async with pool.acquire() as conn:
            return await conn.fetch('SELECT id,text,page_no,bbox,document_id,1-(embedding <=> $1::vector) AS score FROM document_chunks WHERE document_id=$2 ORDER BY embedding <=> $1::vector LIMIT 15',vector,document_id)
    async def sparse():
        async with pool.acquire() as conn:
            return await conn.fetch("SELECT id,text,page_no,bbox,document_id FROM document_chunks, websearch_to_tsquery('english',$1) q WHERE document_id=$2 AND search_vector @@ q ORDER BY ts_rank_cd(search_vector,q) DESC LIMIT 15",query,document_id)
    if mode == 'vector':
        return [dict(r) for r in (await dense())[:5]]
    a,b = await asyncio.gather(dense(),sparse())
    return await provider.rerank(query,rrf(a,b))
