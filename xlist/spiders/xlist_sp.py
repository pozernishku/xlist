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
        modify = lambda s: s.replace('/abs/', '/pdf/') if 'https://aasldpubs.onlinelibrary.wiley.com/doi/abs/' in s or 'https://onlinelibrary.wiley.com/doi/abs/' in s or 'https://www.atsjournals.org/doi/abs/' in s or 'https://www.physiology.org/doi/abs/' in s else \
                           s.replace('/full/', '/pdf/') if 'https://febs.onlinelibrary.wiley.com/doi/full/' in s or 'https://onlinelibrary.wiley.com/doi/full/' in s or 'https://www.ahajournals.org/doi/full/' in s else s
            
        for row in reader:
            ref = ''.join(row)
            ref = modify(ref)
            domain = urlparse(ref)
            refs.append(ref)
            domain = '{uri.netloc}'.format(uri=domain)
            unique_domains.add(domain)

    allowed_domains = list(unique_domains)

    def start_requests(self):
        frm = int(getattr(self, 'frm', None))
        to = int(getattr(self, 'to', None))

        os.makedirs('./docs/', exist_ok=True)

        for file_number, ref in enumerate(self.refs[frm:to], 1): #[2500:2674]
            yield scrapy.Request(ref, self.parse, errback=self.errback_httpbin,
                                dont_filter=True, 
                                meta={'download_timeout': 180,  # 500
                                      'file_number': str(file_number),
                                      'start_url': ref}) # , 'max_retry_times': 20

    def errback_httpbin(self, failure):
        request = failure.request
        yield XlistItem(status=repr(failure),
                filename='',
                start_url=request.url,
                end_url=request.url)

    def parse(self, response):
        start_domain = urlparse(response.meta.get('start_url'))
        start_domain = '{uri.netloc}'.format(uri=start_domain)
        end_domain = urlparse(response.url)
        end_domain = '{uri.netloc}'.format(uri=end_domain)
        href_name = self.filename_regex.sub('_', ''.join(response.url.split('/')[-1:]))
        href_name = href_name if href_name[-4:].lower() == '.pdf' else href_name + '.pdf'
        href_name = href_name[:-4] if href_name[-9:].lower() == '.docx.pdf' else href_name
        href_name = href_name if len(href_name) <= 200 else href_name[-200:]
        filename = response.meta.get('file_number') + '_' + href_name

        if response.status >= 500 and response.status < 600:
            yield XlistItem(status='server error ' + str(response.status),
                            filename=filename,
                            start_url=response.meta.get('start_url'),
                            end_url=response.url)

        has_doc = False
        content_type = response.headers.get('Content-Type', def_val=b'').decode()
        for typ in ['application/pdf', 'application/octet-stream', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            has_doc = True if typ in content_type else False
            if has_doc: 
                break

        if has_doc:
            with open('./docs/' + filename, 'wb') as f:
                f.write(response.body)

            status = 'downloaded' if start_domain not in ['diabetesed.net'] else 'downloaded (filter by country exists)'

            yield XlistItem(status=status,
                            filename=filename,
                            start_url=response.meta.get('start_url'),
                            end_url=response.url)
        else:
            self.log('>>> Not a direct PDF file ' + response.url)

            # TODO handle science.sciencemag.org (not all pdfs (two items) are under paid subscription)
            if start_domain in ['annals.org', 'science.sciencemag.org', 'stm.sciencemag.org', 'www.aaapjournals.info', 
                                'www.asmscience.org', 'www.discoverymedicine.com', 'aap.onlinelibrary.wiley.com', 'jamanetwork.com',
                                'journals.lww.com', 'pubs.acs.org', 'pubs.rsc.org', 'www.annualreviews.org', 'www.ingentaconnect.com', 
                                'www.wageningenacademic.com'] \
                                or response.meta.get('start_url') in ['https://aasldpubs.onlinelibrary.wiley.com/doi/pdf/10.1002/mnfr.201100630',
                                                    'https://aasldpubs.onlinelibrary.wiley.com/doi/pdf/10.1097/00054725-200105000-00010',
                                                    'https://bpspubs.onlinelibrary.wiley.com/doi/pdf/10.1002/ibd.20101', 
                                                    'https://journals.sagepub.com/doi/abs/10.1177/0884533615609896',
                                                    'https://journals.sagepub.com/doi/full/10.1177/0884533612452012',
                                                    'https://journals.sagepub.com/doi/pdf/10.3181/00379727-217-44228',
                                                    'https://content.iospress.com/articles/journal-of-alzheimers-disease/jad161141',
                                                    'https://dial.uclouvain.be/pr/boreal/object/boreal:142887',
                                                    'https://dial.uclouvain.be/pr/boreal/object/boreal:168539',
                                                    'https://dial.uclouvain.be/pr/boreal/object/boreal:178988',
                                                    'https://europepmc.org/abstract/med/11780370',
                                                    'https://europepmc.org/abstract/med/15123070',
                                                    'https://europepmc.org/abstract/med/354629',
                                                    'https://library.wur.nl/WebQuery/wurpubs/fulltext/40600', 
                                                    'https://nyaspubs.onlinelibrary.wiley.com/doi/abs/10.1196/annals.1309.005',
                                                    'https://onlinelibrary.wiley.com/doi/abs/10.1002/(SICI)1097-0010(19990301)79:3%3C390::AID-JSFA258%3E3.0.CO;2-0',
                                                    'https://onlinelibrary.wiley.com/doi/abs/10.1002/(SICI)1098-2302(199909)35:2%3C146::AID-DEV7%3E3.0.CO;2-G', 
                                                    'https://www.amjmed.com/article/0002-9343(64)90202-5/pdf',
                                                    'https://www.degruyter.com/view/j/jpme.1998.26.issue-3/jpme.1998.26.3.186/jpme.1998.26.3.186.xml',
                                                    'https://www.futuremedicine.com/doi/abs/10.2217/14622416.7.7.1077',
                                                    'https://www.futuremedicine.com/doi/abs/10.2217/17460913.2.3.285',
                                                    'https://www.futuremedicine.com/doi/abs/10.2217/pgs.10.157',
                                                    'https://www.gastro.theclinics.com/article/S0889-8553(10)00133-0/abstract', 
                                                    'https://www.jstor.org/stable/3799192', 
                                                    'https://www.karger.com/Article/Abstract/146245',
                                                    'https://www.karger.com/Article/Abstract/239391',
                                                    'https://www.karger.com/Article/Abstract/339182',
                                                    'https://www.karger.com/Article/Abstract/443360',
                                                    'https://www.karger.com/Article/Abstract/89775',
                                                    'https://www.karger.com/Article/Abstract/92555', 
                                                    'https://www.nrcresearchpress.com/doi/abs/10.1139/f79-169',
                                                    'https://www.nrcresearchpress.com/doi/abs/10.1139/f80-009',
                                                    'https://www.nrcresearchpress.com/doi/abs/10.1139/f94-190',
                                                    'https://www.nrcresearchpress.com/doi/abs/10.1139/m74-188'
                                                    ]:
                yield XlistItem(status='purchase or subscription required',
                                filename='',
                                start_url=response.meta.get('start_url'),
                                end_url=response.url)

            # TODO handle (Google)
            elif start_domain in ['books.google.com', 'scholar.google.com']:
                yield XlistItem(status='google books store',
                                filename='',
                                start_url=response.meta.get('start_url'),
                                end_url=response.url)

            elif start_domain in ['ehp.niehs.nih.gov']:
                yield response.follow(response.meta.get('start_url').replace('/full/','/pdf/'), 
                                      self.parse, dont_filter=True, meta=response.meta)
            
            elif start_domain in ['www.karger.com'] and 'FullText' in response.meta.get('start_url'):
                yield response.follow(response.meta.get('start_url').replace('/FullText/','/PDF/'), 
                                      self.parse, dont_filter=True, meta=response.meta)

            elif start_domain in ['europepmc.org']:
                id = response.meta.get('start_url').split('/')[-1].upper()
                href_pattern = 'https://europepmc.org/backend/ptpmcrender.fcgi?accid={id}&blobtype=pdf'.format(id=id)
                yield response.follow(href_pattern, self.parse, dont_filter=True, meta=response.meta)

            elif start_domain in ['library.wur.nl']:
                go_href = response.xpath('//a[contains(@class, "externallink pdf")]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['synapse.koreamed.org', 'www.cambridge.org']:
                go_href = response.xpath('//a[contains(@href, ".pdf")]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['pediatrics.aappublications.org']:
                go_href = response.xpath('//div/a[@class="aap-download-pdf link-icon"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['peerj.com']:
                go_href = response.xpath('//a[@class="article-download-pdf"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['www.frontiersin.org']:
                go_href = response.xpath('//a[@class="download-files-pdf action-link"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['www.em-consulte.com']:
                go_href = response.xpath('//a[text()="Access to the PDF text"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['www.agajournals.org', 'www.ajog.org', 'www.alzheimersanddementia.com', 
                                  'www.annalsthoracicsurgery.org', 'www.atherosclerosis-journal.com', 'www.biologicalpsychiatryjournal.com',
                                  'www.cghjournal.org', 'www.clinicaltherapeutics.com', 'www.dldjournalonline.com', 'www.fertstert.org', 'www.jaad.org']:
                go_href = response.xpath('//a[@class="pdfLink"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['link.springer.com']:
                go_href = response.xpath('//div/a[@data-track-action="Pdf download"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['onlinelibrary.wiley.com']:
                yield XlistItem(status='purchase or subscription required',
                                filename='',
                                start_url=response.meta.get('start_url'),
                                end_url=response.url)

            elif start_domain in ['journals.sagepub.com']:
                go_href = response.xpath('//*[@id="openAccessSideMenu"]/span[2]/div/a/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['eje.bioscientifica.com']:
                go_href = response.xpath('//p[@class="pdf-js-inline-view-download-message"]/a/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['cancerres.aacrjournals.org', 'care.diabetesjournals.org', 'dmm.biologists.org', 'mbio.asm.org']:
                go_href = response.xpath('//a[@data-trigger="full-text.pdf"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['iovs.arvojournals.org']:
                go_href = response.xpath('//li/a[@id="pdfLink"]/@data-article-url').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['www.cell.com']:
                go_href = response.xpath('//a[@class="article-tools__ctrl article-tools__item__pdf"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['journals.plos.org']:
                go_href = response.xpath('//*[@id="downloadPdf"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['embomolmed.embopress.org', 'msb.embopress.org', 'www.biochemj.org']:
                go_href = response.xpath('//a[contains(@href, "full.pdf")][@target="_blank"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)
            
            elif start_domain in ['bmcbiol.biomedcentral.com', 'bmccomplementalternmed.biomedcentral.com', 
                                  'bmcgastroenterol.biomedcentral.com', 'bmcgenomics.biomedcentral.com', 'bmcimmunol.biomedcentral.com',
                                  'bmcmedicine.biomedcentral.com', 'bmcmicrobiol.biomedcentral.com', 'bmcpharmacoltoxicol.biomedcentral.com',
                                  'aacijournal.biomedcentral.com', 'clinicalepigeneticsjournal.biomedcentral.com',
                                  'clinicalmolecularallergy.biomedcentral.com', 'genesandnutrition.biomedcentral.com', 
                                  'genomebiology.biomedcentral.com', 'genomemedicine.biomedcentral.com', 
                                  'genomemedicine.biomedcentral.com', 'gutpathogens.biomedcentral.com', 
                                  'infectagentscancer.biomedcentral.com', 'jasbsci.biomedcentral.com', 'jissn.biomedcentral.com',
                                  'lipidworld.biomedcentral.com', 'microbialcellfactories.biomedcentral.com', 'microbiomejournal.biomedcentral.com',
                                  'molecularneurodegeneration.biomedcentral.com', 'nutritionandmetabolism.biomedcentral.com', 
                                  'nutritionj.biomedcentral.com', 'translational-medicine.biomedcentral.com']:
                go_href = response.xpath('//p/a[@id="articlePdf"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['bmjopen.bmj.com', 'fn.bmj.com', 'gut.bmj.com', 'www.bmj.com']:
                go_href = response.xpath('//p/a[@class="article-pdf-download"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['www.pnas.org']:
                go_href = response.xpath('//a[@data-trigger="tab-pdf"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['academic.oup.com']:
                go_href = response.xpath('//a[@class="al-link pdf article-pdfLink"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)
            
            elif start_domain in ['www.nature.com']:
                go_href = response.xpath('//div/a[@data-track-action="download pdf"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['www.sciencedirect.com']:
                go_href = response.xpath('//div[@class="PdfDownloadButton"]/a/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required or other download problem',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['www.ncbi.nlm.nih.gov']: # blocks by IP number
                go_href = response.xpath('//a[contains(@href, ".pdf")][contains(text(), "PDF")]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='purchase or subscription required or no PDF found',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['www.thieme-connect.com']:
                go_href = response.xpath('//a[@id="pdfLink"]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='no attached document found',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['patents.google.com']:
                go_href = response.xpath('//a[contains(@href, ".pdf")]/@href').get(default='')
                if go_href:
                    yield response.follow(go_href, self.parse, dont_filter=True, meta=response.meta)
                else:
                    yield XlistItem(status='no attached document found',
                                    filename='',
                                    start_url=response.meta.get('start_url'),
                                    end_url=response.url)

            elif start_domain in ['search.ebscohost.com']: # html save
                filename = filename + '.html' if not filename.endswith('.pdf') else filename[:-4] + '.html'
                with open('./docs/' + filename, 'wb') as f:
                    f.write(response.body)

                status = 'downloaded' if start_domain not in ['diabetesed.net'] else 'downloaded (filter by country exists)'
                yield XlistItem(status=status,
                                filename=filename,
                                start_url=response.meta.get('start_url'),
                                end_url=response.url)

            # No documents found
            elif start_domain in ['www.diva-portal.org', 'www.jimmunol.org', 'pdfs.semanticscholar.org', 'pubag.nal.usda.gov'] \
                                 or response.meta.get('start_url') in ['https://cora.ucc.ie/bitstream/handle/10468/117/VM_?sequence=1',
                                                                       'https://infoscience.epfl.ch/record/199332/files/annurev-genet-111212-133343.pdf',
                                                                       'https://medicine.tamhsc.edu/cimr/pdfs/Jayaraman-NatComm-2014.pdf', 
                                                                       'https://www.mdpi.com/2072-6643/5/4/1417/htm?__hstc=3584879.1bb630f9cde2cb5f07430159d50a3c91.1522886401936.1522886401937.1522886401938.1&__hssc=3584879.1.1522886401939&__hsfp=1773666937',
                                                                       'https://www.mdpi.com/2072-6643/7/4/2839/htm']: 
                yield XlistItem(status='no attached document found',
                                filename='',
                                start_url=response.meta.get('start_url'),
                                end_url=response.url)
            
            # Other download problem (see later)
            elif start_domain in ['www.gastrojournal.org', 'www.hindawi.com', 'www.jacionline.org', 
                                  'www.jci.org', 'www.journalofdairyscience.org', 'www.journal-of-hepatology.eu', 'www.jpeds.com', 
                                  'www.mayoclinicproceedings.org',
                                  'www.physiology.org', 'www.tandfonline.com']: 
                yield XlistItem(status='other download problem',
                                filename='',
                                start_url=response.meta.get('start_url'),
                                end_url=response.url)
            
            # Access restricted by IP number
            elif start_domain in ['www.int-res.com']: 
                yield XlistItem(status='access restricted by IP number',
                                filename='',
                                start_url=response.meta.get('start_url'),
                                end_url=response.url)

