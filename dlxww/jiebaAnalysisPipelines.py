import jieba
from dlxww.mongo_redis.mongo_and_redis import MongoAndRedis


class JiebaAnalysis(object):
    def __init__(self):
        self.MongoRedis = MongoAndRedis.get_instance()
        self.emotion_word_dict = self.MongoRedis.get_emotion_word_dict()

    def process_item(self, item, spider):
        # 属性先设置为空
        item['GresultAttribute'] = None
        # 得到关键信息，如果有正文，则分析正文，否则分析标题
        info = item['GresultDetailedInformating']
        if info is None or len(info) < 1:
            info = item['GresultTitle']

        if info is not None and len(info) > 0:
            seg_list = jieba.cut(info, cut_all=True)

            item['GresultAttribute'] = None

            cut_list = "/ ".join(seg_list).split('/')

            for word in cut_list:
                word = word.strip()
                attribute = self.emotion_word_dict.get(word)
                if attribute is not None:
                    item['GresultAttribute'] = attribute
                # 如果发现是负面词就立马结束
                if item['GresultAttribute'] is not None and item['GresultAttribute'] == '负面':
                    break
            if item['GresultAttribute'] is None:
                item['GresultAttribute'] = '中性'
        else:
            # 如果既没有标题，也没有正文，则默认为中性
            item['GresultAttribute'] = '中性'
        return item
