from pathlib import Path
import pymupdf as fitz

def parse_pdf(path: Path, size=500, overlap=50):
    if not 0 <= overlap < size:
        raise ValueError('overlap must be smaller than size')
    chunks = []
    with fitz.open(path) as pdf:
        for page_no, page in enumerate(pdf, 1):
            # Character offsets retain each intersecting line's physical rectangle.
            for block in page.get_text('dict', sort=True)['blocks']:
                if block['type'] != 0:
                    continue
                text, lines = '', []
                for line in block['lines']:
                    value = ''.join(span['text'] for span in line['spans']) + '\n'
                    start = len(text)
                    text += value
                    x0,y0,x1,y1 = line['bbox']
                    lines.append((start,len(text),[x0/page.rect.width,y0/page.rect.height,x1/page.rect.width,y1/page.rect.height]))
                for start in range(0, len(text), size-overlap):
                    end = min(start+size, len(text))
                    if text[start:end].strip():
                        chunks.append(dict(text=text[start:end], page_no=page_no, bbox=[b for a,z,b in lines if a < end and z > start]))
                    if end == len(text):
                        break
        return len(pdf), chunks
