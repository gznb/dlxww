# -*- coding: utf-8 -*-
import scrapy
import copy
import re
import datetime
from dlxww.conf.time_conf import DATETIME_FORMAT_STR
from dlxww.tools.my_base_spider import MyBaseSpider


class JwbSpider(MyBaseSpider):
    name = 'jwb'
    spider_id = 12
    now_page = 1
    GspiderDomain = 'http://epaper.jwb.com.cn/jwb/'
    base_url = "http://fullsearch.cnepaper.com/" \
               "FullSearch.aspx?__VIEWSTATE=" \
               "%2FwEPDwULLTE4NTgxMDgzMjQPZBYCAgEPZBYCAgMPDxYCHgtSZWNvcmRjb3VudAI6ZGRkBnmrrfT" \
               "%2BJ0SfUGW2018PgunzXKk%3D" \
               "&__VIEWSTATEGENERATOR=4F4D99FC" \
               "&__EVENTTARGET=AspNetPager1&__EVENTARGUMENT={}" \
               "&__EVENTVALIDATION=" \
               "%2FwEWBQLsuaP7DwKMwc%2FlAQK2hea3DQL4p5WKCgLY0YCrAePnRmxNOyQRKgeJxfRNPEQtszId&search_text={}" \
               "&Txt_SiteStart=&Txt_SiteEnd=&lblPaperID=1068"

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            meta['thisPage'] = 1
            meta['pagesize'] = 10
            yield scrapy.Request(url=self.base_url.format(meta['thisPage'], meta['keyword']), meta=meta)

    def parse(self, response):
        if not response.url or 'exception' in response.url:  # 接收到url==''
            return None
        result_list = response.xpath('//ol[@id="need"]/li/span/a/@href').extract()
        if result_list:
            for res in result_list:
                go_to_url = res
                if go_to_url not in self.crawled_url_set:
                    yield scrapy.Request(url=go_to_url,
                                         callback=self.parse_item,
                                         errback=self.errback_httpbin,
                                         meta=response.meta)

        record_count = int(response.xpath('//b[@id="statNum"]/text()').extract_first())
        # print(response.meta['thisPage'])
        if response.meta['thisPage'] * response.meta['pagesize'] < record_count and self.contrast_page(response.meta):
            response.meta['thisPage'] += 1
            next_url = self.base_url.format(response.meta['thisPage'], response.meta['keyword'])
            yield scrapy.Request(url=next_url, meta={'keyword': copy.deepcopy(response.meta)})

    def parse_item(self, response):
        content_list = response.xpath('//div[@id="ozoom"]/founder-content/text()').extract()
        content_list += response.xpath('//div[@id="ozoom"]/founder-content/p/text()').extract()
        content = ''.join(content_list)
        re_data_rule = r'\d{4}-\d{2}-\d{2}'
        release_time = re.search(re_data_rule, response.text)
        if release_time:
            release_time = release_time.group()
        title = response.xpath('//p[@class="BSHARE_TEXT"]/text()').extract_first()
        if content is not None and release_time is not None and title is not None and release_time:
            content = content.strip()
            title = title.strip()
            release_time = '{} {}'.format(release_time, '00:00:00')
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

