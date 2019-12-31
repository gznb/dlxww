# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ResultItem(scrapy.Item):
    """
    这是标准 模式
    """
    _id = scrapy.Field()
    GresultKeyword = scrapy.Field()                    # 当前搜索引擎所需搜索的关键词
    GresultRealUrl = scrapy.Field()                    # 网页的真实 url地址
    GresultTitle = scrapy.Field()                      # 网页 title
    GresultDetailedInformating = scrapy.Field()        # 可用于情感分析的文本信息   
    GresultNowTime = scrapy.Field()                    # 当前信息的得到时间
    GresultReleaseTime = scrapy.Field()                # 当前网页的发布时间
    
    GorderId = scrapy.Field()                          # 订单id
    GspiderId = scrapy.Field()                         # 爬虫id

    GresultAttribute = scrapy.Field()                  # 当前网页的属性   
    GresultScore = scrapy.Field()                     # 评分
    GresultDeleted = scrapy.Field()
