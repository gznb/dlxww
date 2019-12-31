# -*- coding: utf-8 -*-
import copy
import datetime

import scrapy

from dlxww.conf.time_conf import DATETIME_FORMAT_STR
from dlxww.tools.my_base_spider import MyBaseSpider


class BeijingReviewSpider(MyBaseSpider):
    name = 'beijing_review'
    GspiderDomain = 'http://www.beijingreview.com.cn/'
    base_url = "http://was.cipg.org.cn/was5/web/search?searchword={}&channelid=223314"
    next_base_url = "http://was.cipg.org.cn/was5/web/{}"
    spider_id = 6

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            yield scrapy.Request(url=self.base_url.format(meta['keyword']), meta=meta)

    def parse(self, response):
        if not response.url or 'exception' in response.url:  # 接收到url==''
            return None
        result_list = response.xpath(
            '//a[starts-with(@href, "http://www.beijingreview.com.cn/bjreview_cn")]/@href').extract()
        if result_list:
            for res in result_list:
                go_to_url = res.replace('bjreview_cn/', '')
                if go_to_url not in self.crawled_url_set:
                    yield scrapy.Request(url=go_to_url,
                                         callback=self.parse_item,
                                         errback=self.errback_httpbin,
                                         meta=response.meta)
        # print(response.meta['thisPage'])
        next_url = response.xpath('//a[contains(text(), "下一页")]/@href').extract_first()
        if next_url is not None and self.contrast_page(response.meta):
            response.meta['thisPage'] += 1
            yield scrapy.Request(url=self.next_base_url.format(next_url),
                                 meta=copy.deepcopy(response.meta))

    def parse_item(self, response):
        content = ''.join(response.xpath('//div[@id="mid"]//p/text()').extract()[:-4]).strip()
        release_time = response.xpath('//meta[@name="publishdate"]/@content').extract_first()
        title = response.xpath('/html/head/title/text()').extract_first()

        if content is not None and release_time is not None and title is not None and content:
            if release_time is not None:
                release_time = release_time + ' 00:00:00'
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

