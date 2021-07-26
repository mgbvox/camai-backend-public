from collections import defaultdict

import io
import pandas as pd
from typing import Union, List

from app.core.globals import CUE_IMPORT_FIELDS, PATIENT_EXPORT_FIELDS
from app.core.types import Json


def get_csv_data_from_pat(pat: Json, key: Union[str, List[str]], omit: List[str] = []):
    if key in omit:
        return None
    if isinstance(key, list):
        val = pat.get(key[0])
        for k in key[1:]:
            val = val.get(k) if val else None
        return val
    else:
        return pat.get(key)


def to_row(pat):
    row = defaultdict(None)
    for k_cue, k_pat in zip(CUE_IMPORT_FIELDS, PATIENT_EXPORT_FIELDS):
        row[k_cue] = get_csv_data_from_pat(pat, k_pat)
    return row

def df_to_bytes(df):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, engine='xlsxwriter', index=False)
    writer.save()
    xlsx_data = output.getvalue()
    return xlsx_data

def to_excel_bytes(pats: List[Json]) -> bytes:
    records = [to_row(p) for p in pats]
    df = pd.DataFrame.from_records(records)
    xlsx_data = df_to_bytes(df)
    return xlsx_data
