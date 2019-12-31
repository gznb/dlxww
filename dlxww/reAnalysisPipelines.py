from dlxww.mongo_redis.mongo_and_redis import MongoAndRedis
import re


class ReAnalysis(object):
    def __init__(self):
        self.MongoRedis = MongoAndRedis.get_instance()
        self.emotion_word_dict = self.MongoRedis.get_emotion_word_dict()
        emotion_word_list = list(self.emotion_word_dict.keys())
        self.pattern = '|'.join(emotion_word_list)
        self.trans = {
            '正面': 1,
            '中性': 0,
            '负面': -1
        }

    def process_item(self, item, spider):
        # 属性先设置为空
        item['GresultAttribute'] = None
        # 得到关键信息，如果有正文，则分析正文，否则分析标题
        info = '{} {}'.format(item['GresultDetailedInformating'], item['GresultTitle'])
        if info is not None and len(info) > 0:
            res_list = re.findall(self.pattern, info)
            sentiment = 0
            if res_list:
                for res in res_list:
                    sentiment += self.trans[self.emotion_word_dict[res]]
                if sentiment > 0:
                    item['GresultAttribute'] = '正面'
                elif sentiment == 0:
                    item['GresultAttribute'] = '中性'
                else:
                    item['GresultAttribute'] = '负面'
            else:
                item['GresultAttribute'] = '中性'
        else:
            # 如果既没有标题，也没有正文，则默认为中性
            item['GresultAttribute'] = '中性'
        return item
