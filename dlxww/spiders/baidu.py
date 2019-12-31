# -*- coding: utf-8 -*-
import copy
import datetime

import scrapy

from dlxww.tools.is_contain_chinese import CheckString
from dlxww.tools.my_base_spider import MyBaseSpider



class BaiduSpider(MyBaseSpider):
    name = 'baidu'
    GspiderDomain = 'https://www.baidu.com/'
    spider_id = 0
    check = CheckString()
    base_url = "http://www.baidu.com.cn/s?wd={}"

    def start_requests(self):
        # 得到订单列表
        meta_list = self.get_start_meta()
        for meta in meta_list:
            yield scrapy.Request(url=self.base_url.format(meta['keyword']), meta=meta)

    def parse(self, response):
        # 出现异常
        if not response.url or 'exception' in response.url:
            return None

        result_url = response.xpath('//a[contains(text(), "百度快照")]/@href').extract()
        if result_url:
            for res in result_url:
                go_to_url = res
                yield scrapy.Request(url=go_to_url,
                                     callback=self.parse_item,
                                     errback=self.errback_httpbin,
                                     meta=response.meta)

        next_url = response.xpath('//a[contains(text(), "下一页>")]/@href').extract_first()
        # print(response.meta['thisPage'])
        if next_url is not None and self.contrast_page(response.meta):
            response.meta['thisPage'] += 1
            next_url = 'http://www.baidu.com.cn{}'.format(next_url)
            yield scrapy.Request(url=next_url, meta=copy.deepcopy(response.meta))

    def parse_item(self, response):
        real_url = response.xpath('//*[@id="bd_snap_note"]/a/@href').extract_first()
        title = response.xpath('/html/body/div[4]/title/text()').extract_first()
        if title is not None:
            title = title.strip().replace('\n', '').replace('\r', '').replace('\t', '')
        # 因为这里是快照的原因，直接获取的是当前快照的url地址，因此只能从里面解析，看看能不能得到快照对应的原来网页的地址
        if real_url is not None \
                and not self.check.is_contain_chinese(real_url) \
                and title is not None \
                and real_url not in self.crawled_url_set:
            release_time = datetime.datetime.now()
            item = self.get_item(keyword=response.meta['keyword'],
                                 url=real_url,
                                 title=title,
                                 content='',
                                 order_id=response.meta['orderId'],
                                 release_time=release_time,
                                 spider_id=self.spider_id)

            yield item
