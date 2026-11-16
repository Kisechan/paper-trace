CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS documents (
 id bigserial PRIMARY KEY, filename text NOT NULL, path text NOT NULL UNIQUE,
 total_pages integer NOT NULL, sha256 text NOT NULL, created_at timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS document_chunks (
 id bigserial PRIMARY KEY, document_id bigint NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
 text text NOT NULL, embedding vector(1024) NOT NULL,
 search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
 page_no integer NOT NULL CHECK (page_no > 0), bbox jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS chunks_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_fts ON document_chunks USING gin(search_vector);
CREATE INDEX IF NOT EXISTS chunks_document ON document_chunks(document_id);
