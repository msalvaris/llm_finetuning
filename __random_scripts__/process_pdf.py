from pypdf import PdfReader
import ipdb
from rich.progress import track
import json

def _generate_blocks(pdf_fname:str,num_characters:int=600):
    reader = PdfReader(pdf_fname)
    for page in track(reader.pages, description="Processing pages..."):
        str_text = page.extract_text()
        total = len(str_text)
        start = 0
        end = num_characters
        while end-start>int(0.3*num_characters):
            yield str_text[start:end]
            # increment by half the number of character per batch
            start += int(num_characters/2)
            end += int(num_characters/2)
            if end>total:
                end = total


def main(pdf_fname:str, jsonl_fname:str):
    with open(jsonl_fname, "w", encoding="utf-8") as f:
        for block in _generate_blocks(pdf_fname, num_characters=400):
            record = {
                "input":block,
                "output":""
            }
            json_record = json.dumps(record)
            f.write(json_record + '\n')


if __name__=="__main__":
    main(".data/2403.03507.pdf", ".data/galore.jsonl")