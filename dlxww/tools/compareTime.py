import datetime
from dlxww.conf.time_conf import DATETIME_FORMAT_STR


def compare_time(time_a, time_b):
    """
    :param time_a:
    :param time_b:
    :return:
    """
    try:
        if isinstance(time_a, str):
            time_a = datetime.datetime.strptime(time_a, DATETIME_FORMAT_STR)
        if isinstance(time_b, str):
            time_b = datetime.datetime.strptime(time_b, DATETIME_FORMAT_STR)
    except ValueError as err:
        print(err)
        print("不是标准的时间字符串")
        return False
    else:
        # print(time_a, time_b)
        return time_a >= time_b