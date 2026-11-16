from contextlib import asynccontextmanager
import json
import logging
import asyncpg
import httpx
from openai import OpenAIError
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .config import settings
from .providers import Provider
from .retrieval import retrieve
from .generation import generate

@asynccontextmanager
async def lifespan(app):
    app.state.pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=8)
    app.state.provider = Provider()
    yield
    await app.state.provider.close()
    await app.state.pool.close()
app = FastAPI(title='Paper Trace', lifespan=lifespan)
class Question(BaseModel):
    document_id: int = Field(gt=0)
    question: str = Field(min_length=1,max_length=2000)
@app.get('/health')
async def health():
    async with app.state.pool.acquire() as conn:
        await conn.fetchval('SELECT 1')
    return {'status':'ok'}
@app.get('/documents')
async def documents():
    async with app.state.pool.acquire() as conn:
        return [dict(r) for r in await conn.fetch('SELECT id,filename,total_pages FROM documents ORDER BY id')]
@app.get('/documents/{document_id}/pdf')
async def pdf(document_id:int):
    async with app.state.pool.acquire() as conn:
        name = await conn.fetchval('SELECT path FROM documents WHERE id=$1',document_id)
    if not name:
        raise HTTPException(404,'Document not found')
    path = (settings.pdf_dir / name).resolve()
    if path.parent != settings.pdf_dir.resolve() or not path.is_file():
        raise HTTPException(404,'PDF unavailable')
    return FileResponse(path,media_type='application/pdf')
@app.post('/ask')
async def ask(body:Question):
    async with app.state.pool.acquire() as conn:
        exists = await conn.fetchval('SELECT 1 FROM documents WHERE id=$1',body.document_id)
    if not exists:
        raise HTTPException(404,'Document not found')
    try:
        rows = await retrieve(app.state.pool,app.state.provider,body.question,body.document_id)
        if not rows or max(r['score'] for r in rows) < settings.relevance_threshold:
            return {'answer':'论文中的证据不足以回答这个问题。','citations':[],'refused':True}
        answer = await generate(app.state.provider,body.question,rows)
    except (httpx.HTTPError, OpenAIError, ValueError) as exc:
        logging.warning('Provider or output validation failed: %s',type(exc).__name__)
        raise HTTPException(502,'模型服务暂时不可用或引用校验失败，请重试。') from exc
    if answer.refused:
        return {"answer":answer.answer,"citations":[],"refused":True}
    citations=[]
    for label in dict.fromkeys(answer.citations):
        row=rows[int(label.split('_')[1])-1]
        citations.append({'label':label,'chunk_id':row['id'],'page_no':row['page_no'],'bbox':json.loads(row['bbox']) if isinstance(row['bbox'],str) else row['bbox'],'text':row['text'],'score':row['score']})
    return {'answer':answer.answer,'citations':citations,'refused':False}
