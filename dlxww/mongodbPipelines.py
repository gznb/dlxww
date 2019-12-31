from dlxww.mongo_redis.mongo_and_redis import MongoAndRedis


class MongodbPipeline(object):
    def __init__(self):
        # 建立MongoDB数据库连接
        self.MongoRedis = MongoAndRedis.get_instance()

    def process_item(self, item, spider):
        """
        :param item:
        :param spider:
        :return:
        """
        post_item = dict(item)

        # 如果有 则更新，可能是原本爬取过的后来被删除了
        # 可能是 原先分析算法垃圾，现在升级后的
        # self.MongoRedis.result_client.update_one({'GresultRealUrl': item['GresultRealUrl'],
        #                                           'GresultKeyword': item['GresultKeyword'],
        #                                           'GorderId': item['GorderId']
        #                                           }, {"$set": item}, upsert=True)
        # 单纯将url 作为唯一标识
        if not self.MongoRedis.conn.sismember('CRAWLED_URL', item['GresultRealUrl']):
            self.MongoRedis.result_client.insert(item)
            self.MongoRedis.conn.sadd('CRAWLED_URL', item['GresultRealUrl'])
        return item
