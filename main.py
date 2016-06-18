# -*- coding: utf-8 -*-

from wox import Wox
from wox import WoxAPI
from stations import stations
from datetime import datetime
from collections import OrderedDict
import requests
import re

class Tickets(Wox):

    train_type = None  
    specific_train = None
    
    from_sta = None
    to_sta = None
    off_time = None
    
    help_info = [
        "第零个参数：可选，-h : 帮助, -d : 动车, -g : 高铁, -k : 快速, -t : 特快, -z : 直达",
        "第一个参数：出发站点的中文名",
        "第二个参数：目的站点的中文名",
        "第三个参数：具体时间，格式为：201674、2016/7/4、2016-7-4",
        "第四个参数，可选，具体的某个车次，如K1511"
    ]
    error_info = None
    
    def query(self, query):
        results = []        

        parser_result = self.parser(query)
        
        if not parser_result:  
            if self.error_info:
                results.append({
                    "Title": "出错啦",
                    "SubTitle": "{}".format(self.error_info),            
                    "IcoPath":"app.png"
                })
            else:
                for help_item in self.help_info:
                    results.append({
                    "Title": "帮助信息",
                    "SubTitle": "{}".format(help_item),            
                    "IcoPath":"app.png"
                })
        else:
            try:
                train_info = self.get_train_info()
                if not train_info:
                    results.append({
                        "Title": "火车票查询",
                        "SubTitle": "{}".format(self.error_info),            
                        "IcoPath":"app.png"
                    })
                    return results
                for item in train_info:
                    one_train = self.get_one_train(item)
                    if one_train:
                        results.append(one_train)
            except Exception:
                results = []
                results.append({
                        "Title": "火车票查询",
                        "SubTitle": "出错了：没有查到相关的票哦",            
                        "IcoPath":"app.png"
                })
        #self.debug(len(results))
        if len(results) == 0:
            results.append({
                        "Title": "火车票查询",
                        "SubTitle": "出错了：没有查到相关的票哦",            
                        "IcoPath":"app.png"
            })
        return results

    def get_one_train(self, item):
        one_train = {}
        one_train['Title'] = item['station_train_code']
        
        if self.specific_train and one_train['Title'] != self.specific_train:
            return None
        
        elif self.train_type and one_train['Title'][0].lower() not in self.train_type:
            return None
            
        else:
            #self.debug(item)
            sub_title = []
            sub_title.append('出发站: ') 
            sub_title.append(item['from_station_name'] + " @" )
            sub_title.append(item['start_time'])
            sub_title.append(' 到达站: ')
            sub_title.append(item['to_station_name'])
            sub_title.append(" @" + item['arrive_time'])
            sub_title.append(" 历时: " + item['lishi'])
            sub_title.append("\t\t")
            all_site_type = {
                'swz_num':"商务座",
                "tz_num":"特等座",
                "zy_num":"一等座",
                "ze_num":"二等座",
                "gr_num":"高级软卧",
                "rw_num":"软卧",
                "yw_num":"硬卧",
                "rz_num":"软座",
                "yz_num":"硬座",
                "wz_num":"无座",
                "qt_num":"其他"
            }
            all_site_info = {}
            
            for key, value in all_site_type.items():
                if item.get(key):
                    if item[key].isdigit():
                        all_site_info[value] = item[key]
                        
            if len(all_site_info) == 0:
                sub_title.append("没票啦！")
                
            else:
                for key, value in all_site_info.items():    
                    sub_title.append(" " + key + " : ")
                    sub_title.append(value)
                    
            one_train['SubTitle'] = " ".join(sub_title)
            one_train['IcoPath'] = "app.png"
            return one_train
        
    def get_train_info(self):
        url = r'https://kyfw.12306.cn/otn/lcxxcx/query'
        params = OrderedDict()
        params['purpose_codes'] = "ADULT"
        params['queryDate'] = self.off_time
        params['from_station'] = self.from_sta
        params['to_station'] = self.to_sta
        response = requests.get(url, params = params, verify = False)
        
        try:
            train_info = response.json()['data']['datas'] 
        except Exception as er:
            self.error_info = "没有查到相关的车次哦"
            return False
        return train_info
        
    def parser(self, query):
        all_parameter = query.split()
        
        all_type = "dgktz"
        if all_parameter[0][0] == "-":
            if all_parameter[0] == "-h":
                self.error_info = None
                return False
            train_type_tmp = all_parameter[0][1:]
            self.train_type = []
            for item in train_type_tmp:
                if item in all_type:
                    self.train_type.append(item)
            all_parameter = all_parameter[1:]
        
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
            self.error_info =  "时间格式错误"
            return False
        else:
            self.off_time = datetime.strftime(time_tmp, "%Y-%m-%d")
        
        if len(all_parameter) == 4:
            if not re.match(r"[KDGZT]\d+", all_parameter[3]):
                self.error_info = "车次不符合格式"
                return False
            self.specific_train = all_parameter[3]
            
        
        return True
          
        
if __name__ == "__main__":
    Tickets()