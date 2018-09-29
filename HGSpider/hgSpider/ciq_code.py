import requests


class CiqSpider(object):
    def __init__(self):
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

        self.postdata.update(s_hsCode=2941909013)
        http_res = self.session.post(self.url, data=self.postdata, timeout=20)
        print('http_res = ', http_res.text)

    def run(self):
        self.get_ciq_code()


if __name__ == "__main__":
    a = CiqSpider()
    a.run()

