# -*- coding: utf-8 -*-
import scrapy
import datetime
from dlxww.conf.time_conf import DATETIME_FORMAT_STR
from dlxww.tools.my_base_spider import MyBaseSpider
import copy

class TianyaLuntanSpider(MyBaseSpider):
    name = 'tianya_luntan'
    base_url = "https://search.tianya.cn/bbs?q={}&pn={}"
    GspiderDomain = 'https://bbs.tianya.cn/'
    spider_id = 4

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            meta['thisPage'] = 1
            yield scrapy.Request(url=self.base_url.format(meta['keyword'], meta['thisPage']), meta=meta)

    def parse(self, response):
        if not response.url or 'exception' in response.url:  # 接收到url==''
            return None
        result_list = response.xpath('//div[@class="searchListOne"]/ul/li/div/h3/a/@href').extract()
        if result_list:
            for res in result_list:
                go_to_url = res
                if go_to_url not in self.crawled_url_set:
                    yield scrapy.Request(url=go_to_url,
                                         callback=self.parse_item,
                                         errback=self.errback_httpbin,
                                         meta=response.meta)
        # print(response.meta['thisPage'])
        if self.contrast_page(response.meta):
            response.meta['thisPage'] += 1
            next_url = self.base_url.format(response.meta['keyword'], response.meta['thisPage'])
            yield scrapy.Request(url=next_url, meta=copy.deepcopy(response.meta))

    def parse_item(self, response):
        content = ''.join(response.xpath('//div[@class="bbs-content clearfix"]/text()').extract()).strip()
        release_time = response.xpath('//div[contains(@class, "js-bbs-act")]/@js_replytime').extract_first()
        title = response.xpath('//span[@class="s_title"]/span/text()').extract_first()

        if content is not None and release_time is not None and title is not None:
            if release_time is not None:
                release_time = release_time[:-2]
                try:
                    release_time = datetime.datetime.strptime(release_time, DATETIME_FORMAT_STR)
                except ValueError as err:
                    self.logger.error(err)
                    return None
            content = content.strip()
            item = self.get_item(keyword=response.meta['keyword'],
                                 order_id=response.meta['orderId'],
                                 url=response.url,
                                 title=title,
                                 content=content,
                                 release_time=release_time,
                                 spider_id=self.spider_id)  # spider_id　
            yield item
