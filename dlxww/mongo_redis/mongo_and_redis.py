import pymongo
import redis
from dlxww.conf.mongo_conf import MONGO_CONN_CONF
from dlxww.conf.redis_conf import REDIS_CONN_CONF
from dlxww.conf.time_conf import DATETIME_FORMAT_STR
import json


class MongoAndRedis(object):

    def __init__(self, *args, **kwargs):
        client_str = 'mongodb://{0}:{1}@{2}:{3}/{4}'.format(
            MONGO_CONN_CONF['username'],
            MONGO_CONN_CONF['password'],
            MONGO_CONN_CONF['host'],
            MONGO_CONN_CONF['port'],
            MONGO_CONN_CONF['dbName']
        )
        self.str_format_time = DATETIME_FORMAT_STR
        self.client = pymongo.MongoClient(client_str)
        self.db = self.client[MONGO_CONN_CONF['dbName']]
        # 连接到各个mongodb集合
        self.order_client = self.db['d2_order_model']
        self.result_client = self.db['d2_result_model']
        self.emotion_client = self.db['d2_emotional_model']
        self.spider_client = self.db['d2_spider_model']

        # 连接  redis
        self.conn = redis.Redis(host=REDIS_CONN_CONF['host'],
                                port=REDIS_CONN_CONF['port'],
                                password=REDIS_CONN_CONF['password'],
                                db=REDIS_CONN_CONF['db'])
        # 单例数据
        self.order_list = list()
        self.crawled_url_set = set()
        self.emotion_word_dict = dict()

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if not hasattr(MongoAndRedis, '_instance'):
            MongoAndRedis._instance = MongoAndRedis(*args, **kwargs)
        return MongoAndRedis._instance

    def get_emotion_word_dict(self):
        """
        得到 情感词词典
        :return:
        """
        # 约定的标记，如果为0表示被更新了
        emotion_word_flag = self.conn.get('EMOTION_WORD_FLAG')
        # 如果说，被更新了，或者是本来里面就没有值了，需要重新去数据库里面读一遍
        if not emotion_word_flag or not self.emotion_word_dict:
            self.conn.set('EMOTION_WORD_FLAG', 1)
            self.emotion_word_dict = dict()
            self.get_emotion_word_from_redis()
        return self.emotion_word_dict

    def get_emotion_word_from_redis(self):
        """
        # 生成一个词库字典
        :return: emotion_dict
        """
        # 如果有直接返回
        # redis 中没有，就去 mongo里面找
        if self.conn.exists('EMOTION_DICT') == 0:
            self.get_emotion_word_from_mongo()
            self.conn.hmset('EMOTION_DICT', self.emotion_word_dict)
        else:
            emotion_dict = self.conn.hgetall('EMOTION_DICT')
            for k, v in emotion_dict.items():
                self.emotion_word_dict[k.decode('utf-8')] = v.decode('utf-8')

    def get_emotion_word_from_mongo(self):
        # 只得到词和词性
        result = self.emotion_client.find({'GemotionalDeleted': 0},
                                          {'_id': 0, 'GemotionalName': 1, 'GemotionalAttribute': 1})
        for res in result:
            self.emotion_word_dict[res['GemotionalName']] = res['GemotionalAttribute']

    def get_order_list(self):
        order_list_flag = self.conn.get('ORDER_LIST_FLAG')

        if not order_list_flag or not self.order_list:
            self.conn.set('ORDER_LIST_FLAG', 1)
            self.order_list = list()
            self.get_order_list_from_redis()
        return self.order_list

    def get_order_list_from_redis(self):
        """
        # 得到  订单列表
        :return: order_list
        """
        if self.conn.exists('ORDER_LIST') == 0:
            self.get_order_list_from_mongo()
            for jj in self.order_list:
                self.conn.lpush('ORDER_LIST', json.dumps(jj))
        else:
            get_order_list_json = self.conn.lrange('ORDER_LIST', 0, self.conn.llen('ORDER_LIST') - 1)
            for res in get_order_list_json:
                self.order_list.append(json.loads(res))

    def get_order_list_from_mongo(self):
        # 这里面可能出现连接问题
        result = self.order_client.find({'GorderDeleted': 0}, {'_id': 0})
        for res in result:
            d = {
                'orderId': res['GorderId'],
                'orderName': res['GorderName'],
                'userTelephone': res['GuserTelephone'],
                'orderCreateTime': res['GorderCreateTime'].strftime(self.str_format_time),
                'orderRemainingTimes': res['GorderRemainingTimes'],
                'orderLastTime': res['GorderLastTime'].strftime(self.str_format_time),
                'orderSpiderList': res['GorderSpiderList'],
                'word': {
                    "count": len(res['GorderKeywordList']),
                    'list': res['GorderKeywordList'],
                },
                'negative': {
                    'count': len(res['GorderNegativeList']),
                    'list': res['GorderNegativeList']
                }
            }
            self.order_list.append(d)

    def get_crawled_url_set(self):
        """
        得到 以爬url集合
        :return:
        """
        crawled_url_set_flag = self.conn.get('CRAWLED_URL_SET_FLAG')
        if not crawled_url_set_flag or not self.crawled_url_set:
            self.crawled_url_set = 1
            self.crawled_url_set = set()
            self.get_crawled_form_redis()
        return self.crawled_url_set

    def get_crawled_form_redis(self):
        """
        :return:
        """
        if self.conn.exists('CRAWLED_URL') == 0:
            self.get_crawled_form_mongo()
            for url in self.crawled_url_set:
                self.conn.sadd('CRAWLED_URL', url)
        else:
            crawled_url_set_b = self.conn.smembers('CRAWLED_URL')
            self.crawled_url_set = {x.decode('utf-8') for x in crawled_url_set_b}

    def get_crawled_form_mongo(self):
        """
        :return: 已经存在的url列表
        """
        crawled_url_list = self.result_client.find({'GresultDeleted': 0}, {'_id': 0, 'GresultRealUrl': 1})
        self.crawled_url_set = {x['GresultRealUrl'] for x in crawled_url_list}
