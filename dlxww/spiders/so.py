# -*- coding: utf-8 -*-
import scrapy
from dlxww.tools.my_base_spider import MyBaseSpider
import datetime
import copy

class SoSpider(MyBaseSpider):
    name = 'so'
    GspiderDomain = 'https://www.so.com/'
    spider_id = 1
    base_url = "https://www.so.com/s?q={}"

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            yield scrapy.Request(url=self.base_url.format(meta['keyword']), meta=meta)

    def parse(self, response):
        # 出现下载异常
        if not response.url or 'exception' in response.url:
            return None
        result_list = response.xpath('//h3[contains(@class, "res-title")]')
        for res in result_list:
            real_url = res.xpath('./a/@href').extract_first()
            title = "".join(res.xpath('.//text()').extract()).strip()
            if real_url is not None and title is not None and real_url not in self.crawled_url_set:
                release_time = datetime.datetime.now()
                item = self.get_item(url=real_url,
                                     title=title,
                                     content='',
                                     keyword=response.meta['keyword'],
                                     release_time=release_time,
                                     spider_id=self.spider_id,
                                     order_id=response.meta['orderId'])
                yield item

        next_url = response.xpath('//a[@id= "snext"]/@href').extract_first()
        # print(response.meta['thisPage'])
        if next_url is not None and self.contrast_page(response.meta):
            response.meta['thisPage'] += 1
            yield scrapy.Request(
                "https://www.so.com{}".format(next_url),
                callback=self.parse,
                meta=copy.deepcopy(response.meta)
            )
