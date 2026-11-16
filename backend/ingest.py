import argparse
import asyncio
import hashlib
import json
import time
from pathlib import Path
import asyncpg
from app.config import settings
from app.parsing import parse_pdf
from app.providers import Provider

async def ingest(path):
    started = time.perf_counter()
    path = Path(path).resolve()
    if path.parent != settings.pdf_dir.resolve():
        raise ValueError('Place PDFs directly inside PDF_DIR before ingestion')
    pages, chunks = parse_pdf(path)
    if not chunks:
        raise ValueError('PDF contains no extractable text; OCR required')
    parsed = time.perf_counter()
    provider = Provider()
    try:
        vectors = await provider.embed([c['text'] for c in chunks])
    finally:
        await provider.close()
    embedded = time.perf_counter()
    conn = await asyncpg.connect(settings.database_url)
    try:
        async with conn.transaction():
            await conn.execute('SELECT pg_advisory_xact_lock(hashtext($1))',path.name)
            doc_id = await conn.fetchval('INSERT INTO documents(filename,path,total_pages,sha256) VALUES($1,$2,$3,$4) ON CONFLICT(path) DO UPDATE SET total_pages=EXCLUDED.total_pages,sha256=EXCLUDED.sha256 RETURNING id',path.name,path.name,pages,hashlib.sha256(path.read_bytes()).hexdigest())
            await conn.execute('DELETE FROM document_chunks WHERE document_id=$1',doc_id)
            await conn.executemany('INSERT INTO document_chunks(document_id,text,embedding,page_no,bbox) VALUES($1,$2,$3::vector,$4,$5::jsonb)',[(doc_id,c['text'],json.dumps(v),c['page_no'],json.dumps(c['bbox'])) for c,v in zip(chunks,vectors)])
        return dict(document_id=doc_id,pages=pages,chunks=len(chunks),parse_seconds=parsed-started,embedding_seconds=embedded-parsed,total_seconds=time.perf_counter()-started)
    finally:
        await conn.close()
if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('pdf')
    print(json.dumps(asyncio.run(ingest(parser.parse_args().pdf)),indent=2))
