# -*- coding: utf-8 -*-
import copy
import datetime

import scrapy

from dlxww.conf.time_conf import DATETIME_FORMAT_STR
from dlxww.tools.my_base_spider import MyBaseSpider


class BaiduTiebaSpider(MyBaseSpider):
    name = 'baidu_tieba'
    spider_id = 3
    GspiderDomain = 'https://tieba.baidu.com/'
    base_url = "http://tieba.baidu.com/f/search/res?ie=utf-8&qw={}"
    next_go_base_url = "http://tieba.baidu.com{}"

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            yield scrapy.Request(url=self.base_url.format(meta['keyword']), meta=meta)

    def parse(self, response):
        result_list = response.xpath('//span[@class="p_title"]/a/@href').extract()
        for res in result_list:
            if res[0] == '/':
                go_to_url = self.next_go_base_url.format(res)
                if go_to_url not in self.crawled_url_set:
                    yield scrapy.Request(url=go_to_url,
                                         callback=self.parse_item,
                                         errback=self.errback_httpbin,
                                         meta=response.meta)
        # print(response.meta['thisPage'])
        next_url = response.xpath('//a[@class="next"]/@href').extract_first()
        if next_url is not None and self.contrast_page(response.meta):
            response.meta['thisPage'] += 1
            yield scrapy.Request(url=self.next_go_base_url.format(next_url),meta=copy.deepcopy(response.meta))

    def parse_item(self, response):
        title = response.xpath('/html/head/title/text()').extract_first()
        release_time = response.xpath('//div[contains(@class, "d_post_content_bold")]/'
                                      '../../../div[contains(@class, "j_lzl_wrapper")]'
                                      '/div/div[@class="post-tail-wrap"]/span[4]/text()').extract_first()
        content = response.xpath('//div[contains(@class, "d_post_content_bold")]/text()').extract_first()

        if title is not None and release_time is not None and content is not None:
            if release_time is not None:
                release_time = release_time.strip() + ':00'
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
