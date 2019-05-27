# -*- coding: utf-8 -*-
# Run spider from command line:
# scrapy crawl xlist_sp -s LOG_FILE=output.log
import scrapy
import os
import re
import csv
from urllib.parse import urlparse

class XlistSpSpider(scrapy.Spider):
    name = 'xlist_sp'

    filename_regex = re.compile(r"[*?>|<\\:/\"]", re.MULTILINE)
    unique_domains = set()
    refs = []
    with open('Full-List-Links.csv', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            domain = urlparse(''.join(row))
            refs.append(''.join(row))
            domain = '{uri.netloc}'.format(uri=domain)
            unique_domains.add(domain)

    allowed_domains = list(unique_domains)

    def start_requests(self):
        os.makedirs('./docs/', exist_ok=True)

        for file_number, ref in enumerate(self.refs[:], 1): # Change file count here
            yield scrapy.Request(ref, self.parse, dont_filter=True, meta={'download_timeout': 300, 'file_number': str(file_number)}) # , 'max_retry_times': 20

    def parse(self, response):
        if response.headers.get('Content-Type', def_val=b'').decode() == 'application/pdf':
            href_name = self.filename_regex.sub('_', ''.join(response.url.split('/')[-1:]))
            href_name = href_name if href_name[-4:].lower() == '.pdf' else href_name + '.pdf'
            filename = response.meta.get('file_number') + '_' + href_name

            with open('./docs/' + filename, 'wb') as f:
                f.write(response.body)
        else:
            self.log('>>> Not a pdf file: ' + response.url)

