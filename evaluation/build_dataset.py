"""Versioned human-authored questions; expected facts checked against arXiv v7."""
import json
from pathlib import Path
facts = [
('What architecture does the paper propose?', 'Transformer', [1,2,3]),
('What BLEU does the big model achieve on English to German?', '28.4 BLEU', [1,8,9]),
('What English to French BLEU score is reported?', '41.8 BLEU', [1,8,9]),
('How many GPUs trained the models?', 'eight NVIDIA P100 GPUs', [7,8]),
('How many encoder layers are used?', 'N = 6', [3]),
('What is the model dimension of the base model?', '512', [3,5,9]),
('How many attention heads does the base model use?', '8', [5]),
('What is the dimension of each attention head?', '64', [5]),
('Why scale dot products by the square root of the key dimension?', 'Counteract large dot products and small softmax gradients', [4]),
('How does the decoder prevent attending to future positions?', 'Masking subsequent positions', [3,5]),
('What activation is used in the feed-forward network?', 'ReLU', [5]),
('What is the feed-forward inner dimension?', '2048', [5]),
('How are positional encodings computed?', 'Sine and cosine functions of different frequencies', [6]),
('Which optimizer is used?', 'Adam', [7]),
('How many warmup steps are used?', '4000', [7]),
('What label smoothing value is used?', '0.1', [8]),
('What dropout rate is used for the base model?', '0.1', [8,9]),
('How large is the English German training dataset?', '4.5 million sentence pairs', [7]),
('How long is the big model trained?', '3.5 days', [1,8]),
('What is the self-attention per-layer complexity?', 'O(n² d)', [6]),
]
unknown = [
'What accuracy does Transformer obtain on ImageNet?',
'What reinforcement learning reward model is used for RLHF?',
'What is the GPT-4 training parameter count?',
'What dose of aspirin does this paper recommend?',
'What was the stock price of NVIDIA on November 16 2026?',
]
rows=[dict(id=i+1,question=q,expected_answer=a,expected_pages=p,answerable=True) for i,(q,a,p) in enumerate(facts)]
rows += [dict(id=len(rows)+i+1,question=q,expected_answer='',expected_pages=[],answerable=False) for i,q in enumerate(unknown)]
Path(__file__).with_name('dataset.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
