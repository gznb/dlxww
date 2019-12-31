# -*- coding: utf-8 -*-
import copy
import json
from json.decoder import JSONDecodeError
import re
import datetime

import scrapy

from dlxww.conf.time_conf import DATETIME_FORMAT_STR
from dlxww.tools.my_base_spider import MyBaseSpider


class ChinaDailySpider(MyBaseSpider):
    name = 'china_daily'
    base_url = 'http://newssearch.chinadaily.com.cn/rest/cn/search?keywords={}' \
               '&sort=dp&page={}&curType=story&type=&channel=&source='
    GspiderDomain = 'http://www.chinadaily.com.cn/'
    now_page = 0
    spider_id = 7

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            yield scrapy.Request(url=self.base_url.format(meta['keyword'], self.now_page), meta=meta)

    def parse(self, response):
        if not response.url or 'exception' in response.url:  # 接收到url==''
            return None
        try:
            get_data = json.loads(response.body)
        except JSONDecodeError as err:
            print(err)
        now_page = int(re.search(r'page=\d+', response.url).group().split('=')[1])

        total_pages = int(get_data['totalPages'])

        result_list = get_data['content']
        for res in result_list:
            title = res['title']
            content = res['plainText']
            release_time = res['pubDateStr'] + ':00'
            url = res['url']
            if url not in self.crawled_url_set:
                try:
                    release_time = datetime.datetime.strptime(release_time, DATETIME_FORMAT_STR)
                except ValueError as err:
                    self.logger.error(err)
                    return None
                item = self.get_item(keyword=response.meta['keyword'],
                                     order_id=response.meta['orderId'],
                                     url=url,
                                     title=title,
                                     content=content,
                                     release_time=release_time,
                                     spider_id=self.spider_id)  # spider_id　
                yield item
        # print(response.meta['thisPage'])
        if (now_page + 1) < total_pages and self.contrast_page(response.meta):
            response.meta['thisPage'] += 1
            yield scrapy.Request(url=self.base_url.format(response.meta['keyword'], now_page + 1),
                                 callback=self.parse,
                                 meta=copy.deepcopy(response.meta))
