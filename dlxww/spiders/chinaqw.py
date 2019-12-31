# -*- coding: utf-8 -*-
import re
import json
import datetime
import scrapy
from dlxww.conf.time_conf import DATETIME_FORMAT_STR
from dlxww.tools.my_base_spider import MyBaseSpider
import copy
from json.decoder import JSONDecodeError


class ChinaqwSpider(MyBaseSpider):
    name = 'chinaqw'
    spider_id = 8
    GspiderDomain = 'http://sou.chinaqw.com/'
    base_url = "http://sou.chinaqw.com/search?q={}&start={}"

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            yield scrapy.Request(url=self.base_url.format(meta['keyword'], 0), meta=meta)

    def parse(self, response):
        # print(response.url)
        if not response.url or 'exception' in response.url:  # 接收到url==''
            return None
        re_rule_data = r'result=(.*?);'
        re_rule_page = r'sup=(.*?);'
        try:
            get_data = json.loads(re.findall(re_rule_data, response.text)[0])
            get_page = json.loads(re.findall(re_rule_page, response.text)[0])
        except TypeError as err:
            self.logger.error(err)
            return None
        except JSONDecodeError as err:
            self.logger.error(err)
            return None
        try:
            result_list = get_data['data']['hits']['hits']
        except KeyError as err:
            self.logger.error(err)
            return None

        for res in result_list:

            try:
                url = res['_source']['url_1']
                title = res['_source']['title']
                content = res['_source']['content']
                release_time = res['_source']['pubtime'].replace('年', '-').replace('月', '-').replace('日', '') + ':00'
            except KeyError as err:
                self.logger.error(err)
                return None
            try:
                release_time = datetime.datetime.strptime(release_time, DATETIME_FORMAT_STR)
            except ValueError as err:
                self.logger.error(err)
                return None

            if url not in self.crawled_url_set:

                item = self.get_item(keyword=response.meta['keyword'],
                                     order_id=response.meta['orderId'],
                                     url=url,
                                     title=title,
                                     content=content,
                                     release_time=release_time,
                                     spider_id=self.spider_id)  # spider_id　
                yield item

        try:
            total_pages = int(get_data['data']['hits']['total'])
            now_page = int(get_page['start'])
            page_size = int(get_page['pageSize'])
        except TypeError as err:
            self.logger.error(err)
            return None
        except ValueError as err:
            self.logger.error(err)
            return None
        except Exception as err:
            self.logger.error('[未知错误]:{}'.format(err))
            return None
        # print(response.meta['thisPage'])
        if now_page + page_size < total_pages and self.contrast_page(response.meta):
            response.meta['thisPage'] += 1
            # print(now_page)
            # print(self.base_url.format(response.meta['keyword'], (now_page+1)*10))
            yield scrapy.Request(url=self.base_url.format(response.meta['keyword'], now_page + page_size),
                                 callback=self.parse,
                                 meta=copy.deepcopy(response.meta))
