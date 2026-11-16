.PHONY: up down sample ingest test eval
up:
	docker compose up -d --build
down:
	docker compose down
sample:
	mkdir -p data/pdfs
	curl --fail --location --retry 3 https://arxiv.org/pdf/1706.03762 -o data/pdfs/attention-is-all-you-need.pdf.part
	mv data/pdfs/attention-is-all-you-need.pdf.part data/pdfs/attention-is-all-you-need.pdf
ingest:
	docker compose exec api python ingest.py /data/pdfs/attention-is-all-you-need.pdf
test:
	cd backend && uv run --python 3.11 pytest -q
	cd frontend && npm run build
eval:
	docker compose exec api python evaluate.py --document-id 1 --dataset /evaluation/dataset.json --output /evaluation/results.json
