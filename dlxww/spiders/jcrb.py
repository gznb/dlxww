# -*- coding: utf-8 -*-
import scrapy
import re
import copy
import datetime
from dlxww.conf.time_conf import DATETIME_FORMAT_STR
from dlxww.tools.my_base_spider import MyBaseSpider


class JcrbSpider(MyBaseSpider):
    name = 'jcrb'
    spider_id = 11
    GspiderDomain = 'http://www.jcrb.com/'
    base_url = "http://search.jcrb.com/was5/web/search?channelid=245465&searchword=&biaoti=" \
               "&zuoze=&laiyuan=&idStartDate=&idEndDate=&andsen=&total={}&orsen=&exclude=&page={}"

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            meta['thisPage'] = 1
            meta['pagesize'] = 10
            yield scrapy.Request(url=self.base_url.format(meta['keyword'], meta['thisPage']), meta=meta)

    # jxsw
    def parse(self, response):
        if not response.url or 'exception' in response.url:  # 接收到url==''
            return None
        result_list = response.xpath('//td[@class="f"]')
        if result_list:
            for res in result_list:
                go_to_url = res.xpath('./font/a/@href').extract_first()
                if go_to_url is not None and 'jxsw' in go_to_url and go_to_url not in self.crawled_url_set:
                    yield scrapy.Request(url=go_to_url,
                                         callback=self.parse_item,
                                         errback=self.errback_httpbin,
                                         meta=response.meta)
        record_count = 0
        try:
            temp = re.search(r'recordCount=\d+', response.text)
            if temp is not None:
                record_count = int(temp.group().split('=')[1])
        except IndexError as err:
            self.logger.error(err)
            return None
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
        if response.meta['thisPage'] * response.meta['pagesize'] < record_count and self.contrast_page(response.meta):
            response.meta['thisPage'] += 1
            yield scrapy.Request(url=self.base_url.format(response.meta['keyword'], response.meta['thisPage']),
                                                                            meta=copy.deepcopy(response.meta))

    def parse_item(self, response):
        content = response.xpath('string(//div[@class="Custom_UnionStyle"])').extract_first()
        release_time = response.xpath('//*[@id="pubtime_baidu"]/text()').extract_first()
        title = response.xpath('/html/head/title/text()').extract_first()
        # print(response.meta['keyword'])
        # 处理时间, 转化为标准时间字符串格式
        if content is not None \
                and release_time is not None \
                and title is not None \
                and release_time \
                and content \
                and title:
            content = content.strip()
            title = title.strip()
            release_time = release_time[3:]
            try:
                release_time = datetime.datetime.strptime(release_time, DATETIME_FORMAT_STR)
            except ValueError as err:
                self.logger.error(err)
                return None
            item = self.get_item(keyword=response.meta['keyword'],
                                 order_id=response.meta['orderId'],
                                 url=response.url,
                                 title=title,
                                 content=content,
                                 release_time=release_time,
                                 spider_id=self.spider_id)  # spider_id　
            yield item

