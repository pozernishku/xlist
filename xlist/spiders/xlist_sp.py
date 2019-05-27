# -*- coding: utf-8 -*-
import scrapy


class XlistSpSpider(scrapy.Spider):
    name = 'xlist_sp'
    allowed_domains = ['www.frontiersin.org']
    start_urls = ['https://www.frontiersin.org/']

    def parse(self, response):
        pass

