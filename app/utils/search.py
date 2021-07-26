from pydantic import ValidationError
from typing import Union, List
import pathlib
from tqdm import tqdm

from app.utils.pdfs.pdf_extractor import process_lab_file
from app.core.types import Json


def search_pdfs(field, value, pdfs: List[Union[pathlib.Path, str]]):
    for p in tqdm(pdfs):
        try:
            pat = process_lab_file(open(p, 'rb').read(), 'pdf', do_checks=False)
            if value.lower() in pat[field].lower():
                return pat
        except ValidationError:
            pass

def search_pats(field, value, pats: List[Json]):
    for p in tqdm(pats):
        if value.lower() in p[field].lower():
            return p