# -*- coding: utf-8 -*-
# Run spider from command line:
# scrapy crawl xlist_sp -s LOG_FILE=output.log
import scrapy
import os
import re
import csv
from urllib.parse import urlparse
from xlist.items import XlistItem

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

        for file_number, ref in enumerate(self.refs[82:83], 1): #[55:82]
            yield scrapy.Request(ref, self.parse, 
                                dont_filter=True, 
                                meta={'download_timeout': 180,  # 500
                                      'file_number': str(file_number),
                                      'start_url': ref}) # , 'max_retry_times': 20

    def parse(self, response):
        start_domain = urlparse(response.meta.get('start_url'))
        start_domain = '{uri.netloc}'.format(uri=start_domain)
        end_domain = urlparse(response.url)
        end_domain = '{uri.netloc}'.format(uri=end_domain)
        href_name = self.filename_regex.sub('_', ''.join(response.url.split('/')[-1:]))
        href_name = href_name if href_name[-4:].lower() == '.pdf' else href_name + '.pdf'
        filename = response.meta.get('file_number') + '_' + href_name

        if response.status >= 500 and response.status < 600:
            yield XlistItem(status='server error' + str(response.status),
                            filename=filename,
                            start_url=response.meta.get('start_url'),
                            end_url=response.url)

        if response.headers.get('Content-Type', def_val=b'').decode() in ['application/pdf', 'application/octet-stream']:
            with open('./docs/' + filename, 'wb') as f:
                f.write(response.body)

            status = 'downloaded' if start_domain not in ['diabetesed.net'] else 'downloaded (filter by country exists)'

            yield XlistItem(status=status,
                            filename=filename,
                            start_url=response.meta.get('start_url'),
                            end_url=response.url)
        else:
            self.log('>>> Not a PDF file ' + response.url)

            if start_domain == 'annals.org':
                yield XlistItem(status='purchase or subscription required',
                                filename='',
                                start_url=response.meta.get('start_url'),
                                end_url=response.url)
            # TODO handle (Google)
            elif start_domain == 'books.google.com':
                yield XlistItem(status='google books store',
                                filename='',
                                start_url=response.meta.get('start_url'),
                                end_url=response.url)
            elif start_domain in ['cancerres.aacrjournals.org', 'care.diabetesjournals.org', 'dmm.biologists.org']:
                ca_href = response.xpath('//a[@data-trigger="full-text.pdf"]/@href').get(default='')
                yield response.follow(ca_href, self.parse, dont_filter=True, meta=response.meta)

# //a[contains(@href, "full.pdf")]/@href