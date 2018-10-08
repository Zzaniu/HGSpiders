import json
import random
import time

import requests

from conf import settings
from lib import aniusql
from lib.log import getSpiderLogger
log = getSpiderLogger()


class CiqSpider(object):
    def __init__(self):
        self.sql = aniusql.Sql(settings.DATABASES_GOLD_8_1)
        self.url = "http://service.bjciq.gov.cn/ciq_entServiceSystem_ENT//framework/ciqCodeAjax/QueryCIQRelateHS/list.do"
        self.session = requests.session()
        self.session.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "service.bjciq.gov.cn",
            "Origin": "http://service.bjciq.gov.cn",
            "Pragma": "no-cache",
            "Referer": "http://service.bjciq.gov.cn/ciq_entServiceSystem/framework/ciqCode/QueryCIQRelateHS/listshow.do",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        self.postdata = {
            "sEcho": "2",
            "iColumns": "5",
            "sColumns": "",
            "iDisplayStart": "0",
            "iDisplayLength": "10",
            "mDataProp_0": "",
            "mDataProp_1": "hsCode",
            "mDataProp_2": "hsCname",
            "mDataProp_3": "statCode",
            "mDataProp_4": "statCname",
            "iSortCol_0": "1",
            "sSortDir_0": "asc",
            "iSortingCols": "1",
            "bSortable_0": "false",
            "bSortable_1": "true",
            "bSortable_2": "true",
            "bSortable_3": "true",
            "bSortable_4": "true",
            "s_hsCode": "",
            "s_statCode": "",
            "tag": "",
        }

    def get_ciq_code(self):
        count = 0
        index = 0
        ret = self.sql.raw_sql('SELECT COUNT(*) from Commodity ')
        if ret.get('status'):
            count = ret['ret_tuples'][0][0]
        for i in range(0, count, 50):
            codets_list = self.sql.select('Commodity', 'codets', limit=[i, 50])
            for codets in codets_list:
                self.postdata.update(s_hsCode=codets.get('codets'))
                http_res = self.session.post(self.url, data=self.postdata, timeout=20)
                for data in json.loads(http_res.text).get('aaData'):
                    HsCode = data.get('statCode')[0:10]
                    CiqCode = data.get('statCode')[-3:]
                    GoodsName = data.get('statCname')
                    # 如果该记录已经存在则跳过
                    ret = self.sql.select('HsCiqCode', '1', where={'HsCode': HsCode, 'CiqCode': CiqCode}, limit=[0,1])
                    if ret:
                        continue
                    else:
                        self.sql.insert('HsCiqCode', HsCode=HsCode, CiqCode=CiqCode, GoodsName=GoodsName)
                        index += 1
                        log.info('新增HsCiqCode记录，HsCode={}, CiqCode={}, GoodsName={}'.format(HsCode, CiqCode, GoodsName))
                # time.sleep(random.randint(2, 4))
        log.info('共更新HsCiqCode记录{}条'.format(index))

    def run(self):
        self.get_ciq_code()


if __name__ == "__main__":
    a = CiqSpider()
    a.run()

