# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class XlistItem(scrapy.Item):
    status = scrapy.Field() # downloaded, purchase or subscription required 
    filename = scrapy.Field()
    start_url = scrapy.Field()
    end_url = scrapy.Field()

