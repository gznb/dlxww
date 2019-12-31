# -*- coding: utf-8 -*-
import scrapy
from dlxww.tools.my_base_spider import MyBaseSpider
import datetime
import copy

class SogouSpider(MyBaseSpider):
    name = 'sogou'
    GspiderDomain = 'https://www.sogou.com/'
    spider_id = 2
    base_url = "https://www.sogou.com/web?query={}"

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            yield scrapy.Request(url=self.base_url.format(meta['keyword']), meta=meta)

    def parse(self, response):
        # 出现下载异常
        if not response.url or 'exception' in response.url:
            return None

        result_url = response.xpath('//a[contains(text(), "快照")]/@href').extract()
        if result_url:
            for res in result_url:
                go_to_url = res
                yield scrapy.Request(url=go_to_url,
                                     callback=self.parse_item,
                                     errback=self.errback_httpbin,
                                     meta=response.meta)

        next_url = response.xpath('//a[contains(text(), "下一页")]/@href').extract_first()
        # print(response.meta['thisPage'])
        if next_url is not None and self.contrast_page(response.meta):
            response.meta['thisPage'] += 1
            next_url = 'https://www.sogou.com/web{}'.format(next_url)
            yield scrapy.Request(url=next_url, meta=response.meta)

    def parse_item(self, response):
        real_url = response.xpath('/html/body/div[1]/div/p/a/@href').extract_first()
        title = response.xpath('//*[@id="embeddiv"]/title/text()').extract_first()
        if real_url is not None and title is not None and real_url not in self.crawled_url_set:
            release_time = datetime.datetime.now()
            item = self.get_item(url=real_url,
                                 keyword=response.meta['keyword'],
                                 title=title,
                                 content='',
                                 release_time=release_time,
                                 order_id=response.meta['orderId'],
                                 spider_id=self.spider_id)
            yield item
        # elif real_url is None or title is None:
        #     print('搜狗搜索页面解析规则发生变化')
