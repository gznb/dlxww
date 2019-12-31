# -*- coding: utf-8 -*-
import scrapy
import datetime
from dlxww.conf.time_conf import DATETIME_FORMAT_STR
from dlxww.tools.my_base_spider import MyBaseSpider
import copy

class ZgxxbSpider(MyBaseSpider):
    name = 'zgxxb'
    spider_id = 15
    GspiderDomain = 'http://www.zgxxb.com.cn/'
    base_url = "http://zhannei.baidu.com/cse/search?q={}&s=12798179019437337262&entry=1"
    next_base_url = "http://zhannei.baidu.com/cse/{}"

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            yield scrapy.Request(url=self.base_url.format(meta['keyword']), meta=meta)

    def parse(self, response):
        if not response.url or 'exception' in response.url:  # 接收到url==''
            return None
        result_list = response.xpath('//a[@cpos="title"]/@href').extract()
        if result_list:
            for res in result_list:
                go_to_url = res
                if go_to_url not in self.crawled_url_set:
                    yield scrapy.Request(url=go_to_url,
                                         callback=self.parse_item,
                                         errback=self.errback_httpbin,
                                         meta=response.meta)

        next_url = response.xpath('//a[contains(text(), "下一页>")]/@href').extract_first()
        # print(response.meta['thisPage'])
        if self.contrast_page(response.meta):
            response.meta['thisPage'] += 1
            yield scrapy.Request(url=self.next_base_url.format(next_url),
                                meta=copy.deepcopy(response.meta))

    def parse_item(self, response):
        content = ''.join(response.xpath('//td[@class="text"]/p[2]/text()').extract())
        release_time = response.xpath('//td[@class="font2"]/text()').extract_first()
        title = response.xpath('/html/head/title/text()').extract_first()[:-6]
        # print(response.meta['keyword'])
        if release_time is not None:
            release_time = release_time[5:]
            release_time = release_time.strip().replace('年', '-').replace('月', '-').replace('日', '').replace('  ', ' ')
        # 处理时间, 转化为标准时间字符串格式
        if content is not None and release_time is not None and title is not None and content and title:
            try:
                release_time = datetime.datetime.strptime(release_time, DATETIME_FORMAT_STR)
            except ValueError as err:
                self.logger.error(err)
                return None
            content = content.strip()
            title = title.strip()
            item = self.get_item(keyword=response.meta['keyword'],
                                 order_id=response.meta['orderId'],
                                 url=response.url,
                                 title=title,
                                 content=content,
                                 release_time=release_time,
                                 spider_id=self.spider_id)  # spider_id　
            yield item
