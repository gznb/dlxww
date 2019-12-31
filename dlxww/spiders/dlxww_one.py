# -*- coding: utf-8 -*-
import scrapy
import datetime
from dlxww.conf.time_conf import DATETIME_FORMAT_STR
from dlxww.tools.my_base_spider import MyBaseSpider
import copy


class DlxwwOneSpider(MyBaseSpider):
    name = 'dlxww_one'
    spider_id = 5
    now_page = 1
    GspiderDomain = 'http://www.dlxww.com/'
    base_url = "http://php.dltv.cn/search/search.php?keyword={}&type=&channelcode=&time=&rank=&page={}"

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            yield scrapy.Request(url=self.base_url.format(meta['keyword'], self.now_page), meta=meta)

    def parse(self, response):
        if not response.url or 'exception' in response.url:  # 接收到url==''
            return None
        result_list = response.xpath('//a[@class="result_link live_list_news"]/@href').extract()
        if result_list:
            for res in result_list:
                go_to_url = res
                if go_to_url not in self.crawled_url_set:
                    yield scrapy.Request(url=go_to_url,
                                         callback=self.parse_item,
                                         errback=self.errback_httpbin,
                                         meta=response.meta)
        # else:
        #     print("大连新闻网页面规则可能发生变化")

        next_page_str = response.xpath('//a[@class="next"]/@href').extract_first()
        if next_page_str is not None:
            begin_index = next_page_str.index('(') + 1
            end_index = next_page_str.rindex(')')
            next_page = int(next_page_str[begin_index:end_index])
            next_url = self.base_url.format(response.meta['keyword'], next_page)
            # print(response.meta['thisPage'])
            if self.contrast_page(response.meta):
                response.meta['thisPage'] += 1
                yield scrapy.Request(url=next_url, meta=copy.deepcopy(response.meta))

    def parse_item(self, response):
        content = response.xpath('string(//div[@class="newspic_cont"])').extract_first()
        release_time = response.xpath('//span[@class="time"]/text()').extract_first()
        title = response.xpath('//div[@class="newspic_box"]/h2/text()').extract_first()
        # print(response.meta['keyword'])
        # 处理时间, 转化为标准时间字符串格式
        if content is not None and release_time is not None and title is not None:
            if release_time is not None:
                release_time = release_time.strip() + ':00'
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
        # elif content is None or release_time is None or title is None:
        #     print("大连新闻网页面解析规则发生变化")