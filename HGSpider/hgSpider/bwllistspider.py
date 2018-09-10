#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-08-7 11:54:13
# @Author  : Zzaniu (Zzaniu@126.com)
# @Link    : http://example.org
# @Version : $Id$


import json
import random
import time
from conf import settings
from hgSpider.basecls import BaseCls
from lib.mail import error_2_send_email
from lib.log import getSpiderLogger

log = getSpiderLogger()


class BwlListSpider(BaseCls):
    def __init__(self, *args, **kwargs):
        super(BwlListSpider, self).__init__(*args, **kwargs)
        self.CookieUrl = settings.BWLCOOKIE_URL
        self.RealUrl = settings.BWLREAL_URL

    @error_2_send_email
    def update_bwlist_db(self, gdsSeqno, response_dict):
        ret = False
        print("response_dict = ", response_dict)
        for data in response_dict['rows']:
            if int(data['gdsSeqNo']) > gdsSeqno:
                d = {
                    'GdsSeqno': data.get('gdsSeqNo'),
                    'GdsMtno': data.get('gdsMtno'),
                    'Gdecd': data.get('gdecd'),
                    'GdsNm': data.get('gdsNm'),
                    'GdsSpcfModelDesc': data.get('gdsSpcfModelDesc'),
                    'Natcd': data.get('natCd'),
                    'DclUnitcd': data.get('dclUnitCd'),
                    'LawfUnitcd': data.get('lawfUnitCd'),
                    'DclUprcAmt': data.get('dclUprcAmt'),
                    'DclCurrcd': data.get('dclCurrCd'),
                    'LimitDate': data.get('limitDate'),
                    'BwlList2Head': 1,
                }
                self.sql.insert('BwlListType', **d)
                log.info('已更新备案序号：{}'.format(data['gdsSeqNo']))
            else:
                ret = True
        return ret

    def get_local_db_max_gdsseqno(self):
        _sql = 'SELECT max(GdsSeqno) as gdsSeqno FROM BwlListType'
        ret = self.sql.raw_sql(_sql)
        if ret.get('status'):
            gdsSeqno = ret['ret_tuples'][0][0]
            return gdsSeqno

    def update_local_db_info(self):
        gdsSeqno = self.get_local_db_max_gdsseqno()
        for page in range(1, 10):
            response_dict = self.get_info(page)
            print("response_dict = ", response_dict)
            if self.update_bwlist_db(gdsSeqno, response_dict):
                _gdsSeqno = self.get_local_db_max_gdsseqno()
                if _gdsSeqno and _gdsSeqno > gdsSeqno:
                    log.info('备案序号已更新至 {}'.format(_gdsSeqno))
                else:
                    log.info('海关今日暂未更新备案序号..')
                return
            else:
                log.info('海关今日更新备案序号超过50条，5~10秒后将继续爬取第{}页数据..'.format(page + 1))
                time.sleep(random.randint(5, 10))
                continue

    @error_2_send_email
    def get_info(self, page):
        headers = {
            'Host': 'app.singlewindow.cn',
            'Origin': 'http://app.singlewindow.cn',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Upgrade-Insecure-Requests': '1',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
            'Referer': 'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwl?sysId=Z8&flag=view&seqNo=201800000000006402&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/emspubserver/&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/emspubserver/'
        }
        postdata = {
            "page": {"curPage": page, "pageSize": 50},
            "queryType": "B", "operType": "0", "seqNo": "201800000000006402",
        }
        self.session.headers.update(headers)
        self.session.cookies.update(self.get_cookie())
        http_res = self.session.post(self.RealUrl, data=json.dumps(postdata), timeout=10)
        try:
            response_dict = json.loads(http_res.text)
            return response_dict
        except:
            self.session.cookies.update(self.get_cookie(LOCAL_COOKIE_FLG=False))
            http_res = self.session.post(self.RealUrl, data=json.dumps(postdata), timeout=10)
            try:
                response_dict = json.loads(http_res.text)
                return response_dict
            except:
                return None
