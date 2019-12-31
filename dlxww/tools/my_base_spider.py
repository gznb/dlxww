# -*- coding: utf-8 -*-
import scrapy
import copy
from dlxww.mongo_redis.mongo_and_redis import MongoAndRedis
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError
from dlxww.items import ResultItem
import datetime
from dlxww.conf.crawl_conf import MAX_PAGES

class MyBaseSpider(scrapy.Spider):

    MongoRedis = MongoAndRedis.get_instance()
    crawled_url_set = MongoRedis.get_crawled_url_set()

    def get_start_meta(self):
        # 得到meta列表
        order_list = self.MongoRedis.get_order_list()
        meta_list = []
        for order in order_list:
            keyword_list = order['word']['list']
            meta = {
                'orderId': order['orderId'],
                'lastTime': order['orderLastTime']
            }
            for keyword in keyword_list:
                meta['keyword'] = keyword
                meta['thisPage'] = 0
                meta['maxPage'] = MAX_PAGES
                meta_list.append(copy.deepcopy(meta))
                # return scrapy.Request(url=self.base_url.format(keyword, self.now_page), meta=copy.deepcopy(meta))
        return meta_list

    def errback_httpbin(self, failure):

        self.logger.error(repr(failure))
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)
        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)
        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

    def get_item(self, keyword, url, title, content, release_time, order_id, spider_id):
        item = ResultItem()
        item['GresultKeyword'] = keyword
        item['GresultRealUrl'] = url
        item['GresultTitle'] = title
        item['GresultDetailedInformating'] = content
        item['GresultNowTime'] = datetime.datetime.now()
        item['GresultReleaseTime'] = release_time
        item['GorderId'] = order_id
        item['GspiderId'] = spider_id
        item['GresultAttribute'] = None
        item['GresultScore'] = 0.5
        item['GresultDeleted'] = 0
        return item

    # 检查当前爬取的页面有没有超过10页，有的话，就不爬了
    def contrast_page(self, meta):
        return meta['thisPage'] <= meta['maxPage']

    def parse(self, response):
        pass