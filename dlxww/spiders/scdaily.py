# -*- coding: utf-8 -*-
import scrapy
import re
import datetime
from dlxww.conf.time_conf import DATETIME_FORMAT_STR
from dlxww.tools.my_base_spider import MyBaseSpider
import copy


class ScdailySpider(MyBaseSpider):
    name = 'scdaily'
    spider_id = 14
    GspiderDomain = 'https://www.scdaily.cn/'
    base_url = "http://zhannei.baidu.com/cse/site?q=&cc=scdaily.cn&entry=1&q={}"
    next_base_url = "http://zhannei.baidu.com/cse/{}"

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            yield scrapy.Request(url=self.base_url.format(meta['keyword']), meta=meta)

    def parse(self, response):
        if not response.url or 'exception' in response.url:  # 接收到url==''
            return None
        result_list = response.xpath('//div[@id="results"]/div/h3/a/@href').extract()
        if result_list:
            for res in result_list:
                flag = res.split('.')[-1]
                if flag == 'shtml' or flag == 'htm':
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
        release_time = str()
        if response.url[-1] == 'm':
            title = response.xpath('//p[@class="title-d"]/text()').extract_first()
            content = ''.join(response.xpath('string(//td[@class="text"])').extract()).strip()
            re_rule_data = r'\d{4}年\d{2}月\d{2}'
            try:
                data = re.search(re_rule_data, response.text).group()
            except AttributeError as err:
                self.logger.error(err)
                return None
        else:
            title = response.xpath('//div[@id="frameContent"]/h3/text()').extract_first()
            content = ''.join(response.xpath('//p[@id="page_a"]/text()').extract()).strip()
            re_rule_data = r'\d{4}年\d{2}月\d{2}'
            try:
                # 这里可能为空
                data = re.search(re_rule_data, response.text).group()
            except AttributeError as err:
                self.logger.error(err)
                return None
        try:
            release_time = data.replace('年', '-').replace('月', '-').replace('日', '')
            release_time = '{} {}'.format(release_time, '00:00:00')
        except TypeError as err:
            self.logger.error(err)
            return None
        except Exception as err:
            self.logger.error('[未知错误]:{}'.format(err))
        # print(response.meta['keyword'])
        # 处理时间, 转化为标准时间字符串格式
        if content is not None and release_time is not None and title is not None and title and content:
            if release_time is not None:
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
