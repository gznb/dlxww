# -*- coding: utf-8 -*-
import re
import copy
import datetime

import scrapy
from urllib import parse as pr

from dlxww.conf.time_conf import DATETIME_FORMAT_STR
from dlxww.tools.my_base_spider import MyBaseSpider



class HuaxiaSpider(MyBaseSpider):
    name = 'huaxia'
    spider_id = 10
    GspiderDomain = 'http://www.huaxia.com/'
    base_url = "http://search.huaxia.com/?{}&page={}&sButton=2"

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            # 重写了当前页
            meta['thisPage'] = 1
            meta['pagesize'] = 20
            url_data = pr.urlencode({'sText': meta['keyword'].encode('ansi')})
            yield scrapy.Request(url=self.base_url.format(url_data, meta['thisPage']), meta=meta)

    def parse(self, response):
        if not response.url or 'exception' in response.url:  # 接收到url==''
            return None
        result_list = response.xpath('//a[@class="rLink1"]/@href').extract()
        if result_list:
            for res in result_list:
                go_to_url = res
                if go_to_url not in self.crawled_url_set:
                    yield scrapy.Request(url=go_to_url,
                                         callback=self.parse_item,
                                         errback=self.errback_httpbin,
                                         meta=response.meta)

        re_rule_record_count = r'共检索文档:(.*?)&nbsp;篇'
        try:
            record_count = int(re.findall(re_rule_record_count, response.text)[0])
        except TypeError as err:
            self.logger.error(err)
            return None
        except ValueError as err:
            self.logger.error(err)
            return None
        except Exception as err:
            self.logger.error('[未知错误]:{}'.format(err))
            return None
        if response.meta['thisPage'] * response.meta['pagesize'] < record_count and self.contrast_page(response.meta):
            meta = response.meta
            meta['thisPage'] += 1
            url_data = pr.urlencode({'sText': response.meta['keyword'].encode('ansi')})
            next_url = self.base_url.format(url_data, meta['thisPage'])
            yield scrapy.Request(url=next_url, meta=copy.deepcopy(meta))

    def parse_item(self, response):
        re_rule_data = r'(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2})'
        content = ''.join(response.xpath('//td[@id="oImg"]/p/text()').extract())
        release_time = re.findall(re_rule_data, response.text)
        title = response.xpath('//div[@class="Ftitle"]/strong/text()').extract_first()
        # print(response.meta['keyword'])
        # 处理时间, 转化为标准时间字符串格式
        if content is not None and release_time is not None and title is not None and release_time:
            if release_time is not None:
                release_time = release_time[0].strip() + ':00'
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
