# -*- coding: utf-8 -*-

from wox import Wox
from wox import WoxAPI
from stations import stations
from datetime import datetime
from collections import OrderedDict
import requests
import re


class Tickets(Wox):
    from_sta = None
    to_sta = None
    off_time = None
    specific_train = None
    # 分别用来存储出发站、目的站、出发日期以及筛选车次

    result_score = 200
    # 用来存储结果的优先级。于未知原因，如果不手动排序，最终结果不是按时间来排序的。

    help_info = [
        "第一个参数：出发站点的中文名",
        "第二个参数：目的站点的中文名",
        "第三个参数：具体时间，格式为：201674、2016/7/4、2016-7-4",
        "第四个参数，可选，用来筛选车次，从头开始匹配，如k, k1,k151。前面的字母有[KDGZT]"
    ]
    error_info = None

    def query(self, query):
        results = []
        parser_result = self.parser(query)

        if not parser_result:
            if self.error_info:  # 用来显示错误信息
                results.append({
                    "Title": "出错啦",
                    "SubTitle": "{}".format(self.error_info),
                    "IcoPath": "info.png"
                })
            else:  # parser函数对帮助信息和错误信息都返回False，在这里进行区分
                for help_item in self.help_info:
                    results.append({
                        "Title": "帮助信息",
                        "SubTitle": "{}".format(help_item),
                        "IcoPath": "info.png"
                    })
        else:
            try:  # 防止可能出现的错误
                train_info = self.get_train_info()
                if not train_info:  # 如果没有得到车票的信息
                    results.append({
                        "Title": "火车票查询",
                        "SubTitle": "{}".format(self.error_info),
                        "IcoPath": "info.png"
                    })
                    return results

                for item in train_info:  # 读取每列车的信息
                    one_train = self.get_one_train(item)
                    if one_train:
                        results.append(one_train)

            except Exception as s:  # 虽然不标准但还是这样写了
                results = []
                results.append({
                    "Title": "火车票查询",
                    "SubTitle": "出错了：没有查到相关的票哦",
                    "IcoPath": "info.png"
                })

        if len(results) == 0:
            results.append({
                "Title": "火车票查询",
                "SubTitle": "出错了：没有查到相关的票哦",
                "IcoPath": "info.png"
            })
        return results

    def get_one_train(self, item):
        one_train = {}

        # 不能买的
        if item['canWebBuy'] == 'N':
            return None

        # 如果加了可选参数就判断是否是符合要求的车次
        if self.specific_train and not item['station_train_code'].startswith(self.specific_train):
            return None

        one_train['Title'] = item['station_train_code']

        # 一列车的具体信息
        sub_title = []
        sub_title.append('出发站: ')
        sub_title.append(item['from_station_name'] + " @")
        sub_title.append(item['start_time'])
        sub_title.append(' 到达站: ')
        sub_title.append(item['to_station_name'])
        sub_title.append(" @" + item['arrive_time'])
        sub_title.append(" 历时: " + item['lishi'])
        sub_title.append("\t\t")
        all_site_type = {
            'swz_num': "商务座",
            "tz_num": "特等座",
            "zy_num": "一等座",
            "ze_num": "二等座",
            "gr_num": "高级软卧",
            "rw_num": "软卧",
            "yw_num": "硬卧",
            "rz_num": "软座",
            "yz_num": "硬座",
            "wz_num": "无座",
            "qt_num": "其他"
        }

        all_site_info = {}
        for key, value in all_site_type.items():
            if item.get(key):
                if item[key].isdigit():  # 只显示有票的信息
                    all_site_info[value] = item[key]

        if len(all_site_info) == 0:
            sub_title.append("没票啦！")

        else:
            for key, value in all_site_info.items():
                sub_title.append(" " + key + " : ")
                sub_title.append(value)

        one_train['SubTitle'] = " ".join(sub_title)
        one_train['IcoPath'] = "info.png"

        # 进行排序，Score越大，越靠前，在这里除法时间越早，Score越大
        one_train['Score'] = self.result_score
        self.result_score -= 1

        return one_train

    def get_train_info(self):
        url = r'https://kyfw.12306.cn/otn/lcxxcx/query'
        params = OrderedDict()  # 必须是按照下面的顺序传递参数
        params['purpose_codes'] = "ADULT"
        params['queryDate'] = self.off_time
        params['from_station'] = self.from_sta
        params['to_station'] = self.to_sta

        response = requests.get(url, params=params, verify=False)

        try:
            train_info = response.json()['data']['datas']
        except KeyError as er:
            self.error_info = "没有查到相关的车次哦"
            return False

        return train_info

    def parser(self, query):
        all_parameter = query.split()

        if all_parameter[0] == "-h":
            self.error_info = None  # 用None来表示是帮助信息而不是出错信息
            return False

        if len(all_parameter) < 3:
            self.error_info = "参数数量不足"
            return False

        tmp = stations.get(all_parameter[0])
        if not tmp:
            self.error_info = "未知起始地"
            return False
        self.from_sta = tmp

        tmp = stations.get(all_parameter[1])
        if not tmp:
            self.error_info = "未知目的地"
            return False
        self.to_sta = tmp

        self.off_time = all_parameter[2]
        if "-" in self.off_time:
            time_format = "%Y-%m-%d"
        elif "/" in self.off_time:
            time_format = "%Y/%m/%d"
        else:
            time_format = "%Y%m%d"
        try:
            time_tmp = datetime.strptime(self.off_time, time_format)
        except ValueError as s:
            self.error_info = "时间格式错误"
            return False

        else:
            self.off_time = datetime.strftime(time_tmp, "%Y-%m-%d")

        if len(all_parameter) == 4:
            if not re.match(r"[KDGZT]\d*", all_parameter[3].upper()):
                self.error_info = "车次不符合格式"
                return False

            self.specific_train = all_parameter[3].upper()

        return True


if __name__ == "__main__":
    Tickets()
