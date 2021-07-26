from tika import parser  # pip install tika
import regex as re
from datetime import datetime
from dateparser import parse


def split_pages(content: str):
    return [i.strip() for i in re.split(r'GeneXpert®.*Page \d* of \d*', content.strip())]


def get_sample_id(page):
    match = re.search(r'Sample ID: (.*)', page)
    if match:
        return match.group(1)


def get_positivity(page):
    match = re.search(r'Test Result: SARS-CoV-2 (.*)', page)
    if match:
        return match.group(1)


def get_start_time(page):
    match = re.search(r'Start Time: (.*)', page)
    if match:
        dt = parse(match.group(1)).isoformat()
        return dt


class CepheidParser:
    def __init__(self, file_buffer):
        self.raw = parser.from_buffer(file_buffer)

    def extract_results(self):
        pages = split_pages(self.raw['content'])
        results = []
        for page in pages:
            result_data = {'test_id': get_sample_id(page),
                           'test_performed_datetime': get_start_time(page),
                           'test_reported_datetime': datetime.now().isoformat(),
                           'positive': get_positivity(page)
                           }
            results.append(result_data)
        return results

