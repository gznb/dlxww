# -*- coding: utf-8 -*-
import json
import datetime
import scrapy
from dlxww.conf.time_conf import DATETIME_FORMAT_STR
from dlxww.tools.my_base_spider import MyBaseSpider
import copy

class GmwSpider(MyBaseSpider):
    name = 'gmw'
    spider_id = 9
    now_page = 1
    GspiderDomain = 'http://www.gmw.cn/'
    base_url = "http://search.gmw.cn/service/search.do?q={}" \
               "&c=n&cp={}" \
               "&tt=false&dateType=default&callback=jQuery17209299555373063526_1571810209084&_=1571810209150"

    def start_requests(self):
        meta_list = self.get_start_meta()
        for meta in meta_list:
            yield scrapy.Request(url=self.base_url.format(meta['keyword'], self.now_page), meta=meta)

    def parse(self, response):
        if not response.url or 'exception' in response.url:  # 接收到url==''
            return None
        try:
            begin_index = response.text.index('(') + 1
            end_index = response.text.rindex(')')
            get_data = json.loads(response.text[begin_index:end_index])
        except TypeError as err:
            self.logger.error(err)
            return None
        except KeyError as err:
            self.logger.error(err)
            return None
        except ValueError as err:
            self.logger.error(err)
            return None
        except Exception as err:
            self.logger.error('[未知错误]:'+err)
            return None

        try:
            result_list = get_data['result']['list']
            total_count = int(get_data['page']['totalCount'])
            current_page = int(get_data['page']['currentPage'])
            page_num_shown = int(get_data['page']['pageNumShown'])
        except KeyError as err:
            self.logger.error(err)
            return None
        except TypeError as err:
            self.logger.error(err)
            return None
        except Exception as err:
            self.logger.error('[未知错误]:{}'.format(err))
            return None
        for res in result_list:
            go_to_url = res.get('url')
            if go_to_url is not None and go_to_url not in self.crawled_url_set:
                yield scrapy.Request(url=go_to_url,
                                     callback=self.parse_item,
                                     errback=self.errback_httpbin,
                                     meta=response.meta)
        # print(response.meta['thisPage'])
        if current_page * page_num_shown < total_count and self.contrast_page(response.meta):
            response.meta['thisPage'] += 1
            next_url = self.base_url.format(response.meta['keyword'], current_page+1)
            yield scrapy.Request(url=next_url, meta=copy.deepcopy(response.meta))

    def parse_item(self, response):
        content = ''.join(response.xpath('//div[@class="u-mainText"]/p/text()').extract()).strip()
        release_time = response.xpath('//span[@class="m-con-time"]/text()').extract_first()
        title = response.xpath('//h1[@class="u-title"]/text()').extract_first()
        # print(response.meta['keyword'])
        # 处理时间, 转化为标准时间字符串格式
        if content is not None and release_time is not None and title is not None:
            title = title.strip()
            if release_time is not None:
                release_time = release_time.strip() + ':00'
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
