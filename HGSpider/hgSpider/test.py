import json
import os

import requests

from conf import settings

if __name__ == "__main__":
    if os.path.exists(settings.COOKIE_DIR):
        with open(settings.COOKIE_DIR, "r") as f:
            cookie = json.load(f)
    session = requests.session()
    session.cookies.update(cookie)
    url = 'http://sz.singlewindow.cn/dyck/swProxy/nptsserver/sw/ems/npts/eml/emlGoodsQueryService'
    seqNo = '201800000000002523'
    headers = {
        "Host": "sz.singlewindow.cn",
        "Connection": "keep-alive",
        "Content-Length": "133",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": "http://sz.singlewindow.cn",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "http://sz.singlewindow.cn/dyck/swProxy/nptsserver/sw/ems/npts/eml?flag=view&seqNo={}&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/nptsserver/&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/nptsserver/".format(seqNo),
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    data = {"gdsMtno": "", "gdecd": "", "gdsNm": "", "page": {"curPage": 1, "pageSize": 50}, "operType": "0",
            "seqNo": seqNo, "queryType": "Exg"}
    res = session.post(url=url, headers=headers, data=json.dumps(data), timeout=10)
    print(res.text)
