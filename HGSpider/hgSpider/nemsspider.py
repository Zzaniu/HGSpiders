#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-08-13 09:50:44
# @Author  : zaniu (Zzaniu@126.com)
# @Version : $Id$
import copy
import json
import random
import time

import sys

from conf import settings
from hgSpider.basecls import BaseCls
from lib.mail import error_2_send_email
from lib.log import getSpiderLogger

log = getSpiderLogger()


class NemsSpider(BaseCls):
    """金二加工贸易电子帐册"""

    def __init__(self, *args, **kwargs):
        super(NemsSpider, self).__init__(*args, **kwargs)
        self.CookieUrl = settings.NEMSCOOKIE_URL
        self.RealUrl = r'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/atb/emsQueryListService'
        self.RealUrl2 = r'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/atb/emsDetailService'
        self.CompanyList = settings.NEMS_COMPANY_LIST

    @error_2_send_email
    def get_web_cookie(self):
        while not self.get_login_cookie():
            log.info('登陆失败，1S后重新登陆..')
            time.sleep(1)
        self.session.get('http://sz.singlewindow.cn/dyck/swProxy/deskserver/sw/deskIndex?menu_id=nems', timeout=20)
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'Referer': None,
        }
        self.session.headers.update(headers)
        self.session.get(self.CookieUrl, timeout=20)
        # self.session.cookies.update({"loginSignal": '0'})
        self.save_cookie()
        return self.session.cookies.get_dict()

    @error_2_send_email
    def update_nems_cm_list_db(self, gdsSeqno, response_dict):
        """更新单耗表体"""
        pass

    @error_2_send_email
    def update_nems_exg_list_info(self, nemsno, seqNo):
        gdsSeqno = self.get_local_db_max_gdsseqno('NemsExgList', seqNo)
        if gdsSeqno is None:
            gdsSeqno = 0
        page = 0
        while True:
            page += 1
            response_dict = self.get_nems_exg_list_info(page, seqNo)
            if self.update_exglist_db(gdsSeqno, response_dict):
                _gdsSeqno = self.get_local_db_max_gdsseqno('NemsExgList', seqNo)
                if _gdsSeqno and _gdsSeqno > gdsSeqno:
                    log.info('账册号{}的成品序号已更新至 {}'.format(nemsno, _gdsSeqno))
                else:
                    log.info('海关今日暂未更新账册号为{}的成品..'.format(nemsno))
                return
            else:
                wait_time = random.randint(5, 10)
                log.info('海关今日更新账册号{}的成品序号超过50条，{}秒后将继续爬取第{}页数据..'.format(nemsno, wait_time, page + 1))
                time.sleep(wait_time)
                continue

    @error_2_send_email
    def update_exglist_db(self, gdsSeqno, response_dict):
        ret = False
        for data in response_dict['rows']:
            if int(data['gdsseqno']) > gdsSeqno:
                d = {
                    'SEQNO': data.get('seqNo', ''),
                    'GDSSEQNO': data.get('gdsseqno'),
                    'GDSMTNO': data.get('gdsmtno', ''),
                    'GDECD': data.get('gdecd', ''),
                    'GDSNM': data.get('gdsNm', ''),
                    'ENDPRDGDSSPCFMODELDESC': data.get('endprdgdsspcfmodeldesc', ''),
                    'DCLUNITCD': data.get('dclunitcd', ''),
                    'LAWFUNITCD': data.get('lawfunitcd', ''),
                    'DCLUPRC': data.get('dcluprcamt', ''),
                    'DCLCURRCD': data.get('dclcurrcd', ''),
                    'DCLQTY': data.get('dclqty', ''),
                    'LVYRLFMODECD': data.get('lvyrlfmodecd', ''),
                    'ETPSEXEMARKCD': data.get('etpsexemarkcd', ''),
                    'MODFMARKCD': data.get('modfmarkcd', ''),
                    'VCLRPRIDINITQTY': data.get('vclrpridinitqty', ''),
                    'APPRMAXSURPQTY': data.get('apprmaxsurpqty', ''),
                    'QTYCNTRMARKCD': data.get('qtycntrmarkcd', ''),
                    'INDBTIME': data.get('indbtime', ''),
                    'CSTTNFLAG': data.get('csttnflag', ''),
                    'UCNSTQSNFLAG': data.get('ucnstqsnflag', ''),
                    'APPRMAXSURPQTY': data.get('apprmaxsurpqty', ''),
                }
                _d = copy.deepcopy(d)
                for k in _d:
                    if _d[k]:
                        pass
                    else:
                        d.pop(k)
                self.sql.insert('NemsExgList', **d)
                log.info('已更新成品序号：{}'.format(data['gdsseqno']))
                if 1 == int(data['gdsseqno']):
                    ret = True
            else:
                ret = True
        return ret

    @error_2_send_email
    def get_company_seqno(self):
        """查询页面结果字典的生成器，使用yield实现"""
        headers = {
            "Host": "sz.singlewindow.cn",
            "Connection": "keep-alive",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "http://sz.singlewindow.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
            "Content-Type": "application/json;charset=UTF-8",
            "Referer": "http://sz.singlewindow.cn/dyck/swProxy/nemsserver/sw/ems/nems/queryQualApplication?ngBasePath=http%3A%2F%2Fsz.singlewindow.cn%3A80%2Fdyck%2FswProxy%2Fnemsserver%2F",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        postdata = {"sysId": "95", "status": " ", "statusName": "全部", "selTradeCode": "", "etArcrpNo": "",
                    "seqNo": "", "bizopEtpsno": "", "bizopEtpsSccd": "", "inputDateStart": "", "inputDateEnd": "",
                    "inputCode": "4403180896"}
        self.session.headers.update(headers)
        self.session.cookies.update(self.get_cookie())
        for i in self.CompanyList:
            postdata['selTradeCode'] = i
            http_res = self.session.post(self.RealUrl, data=json.dumps(postdata), timeout=20)
            try:
                response_dict = json.loads(http_res.text)
                yield i, response_dict
            except:
                self.session.cookies.update(self.get_cookie(LOCAL_COOKIE_FLG=False))
                http_res = self.session.post(self.RealUrl, data=json.dumps(postdata), timeout=20)
                try:
                    response_dict = json.loads(http_res.text)
                    yield i, response_dict
                except:
                    raise Exception('获取公司seqNo失败，请检查程序...')

    @error_2_send_email
    def get_nems_head_info(self, seqNo):
        """获取表头数据"""
        headers = {
            "Host": "sz.singlewindow.cn",
            "Connection": "keep-alive",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "http://sz.singlewindow.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
            "Content-Type": "application/json;charset=UTF-8",
            "Referer": "http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/canadianTradeBooks?sysId=95&flag=view&seqNo={}&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/emspubserver/&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/emspubserver/".format(
                seqNo),
            "Accept-Language": "zh-CN,zh;q=0.9",
            'Cache-Control': None,
            'Content-Length': None,
        }
        postdata = {"seqNo": seqNo, "sysId": "95"}
        self.session.headers.update(headers)
        self.session.cookies.update(self.get_cookie())
        http_res = self.session.post(self.RealUrl2, data=json.dumps(postdata), timeout=20)
        return json.loads(http_res.text)

    @error_2_send_email
    def update_nems_head_db(self, nemsno, seqNo):
        """插入表头"""
        if self.sql.select('NemsHead', 'id', where={'SEQNO': seqNo}):
            log.info('账册号{}已存在表头数据'.format(nemsno))
            return True
        head_obj = self.get_nems_head_info(seqNo).get('data').get('nemsHead')
        d = {
            'SEQNO': head_obj.get('seqNo', ''),
            'EMSNO': head_obj.get('emsNo', ''),
            'ETPSPREENTNO': head_obj.get('etpspreentno', ''),
            'BIZOPETPSNO': head_obj.get('bizopetpsno', ''),
            'BIZOPETPSSCCD': head_obj.get('bizopetpssccd', ''),
            'BIZOPETPSNM': head_obj.get('bizopetpsnm', ''),
            'RCVGDETPSNO': head_obj.get('rcvgdetpsno', ''),
            'RVSNGDETPSSCCD': head_obj.get('rvsngdetpssccd', ''),
            'RCVGDETPSNM': head_obj.get('rcvgdetpsnm', ''),
            'DCLETPSNO': head_obj.get('dcletpsno', ''),
            'DCLETPSSCCD': head_obj.get('dcletpssccd', ''),
            'DCLETPSNM': head_obj.get('dcletpsnm', ''),
            'DCLETPSTYPECD': head_obj.get('dcletpstypecd', ''),
            'DCLTYPECD': head_obj.get('dcltypecd', ''),
            'EMSTYPECD': head_obj.get('emstypecd', ''),
            'APCRETNO': head_obj.get('apcretno', ''),
            'NETWKETPSARCRPNO': head_obj.get('netwketpsarcrpno', ''),
            'ACTLIMPTOTALAMT': head_obj.get('actlimptotalamt', ''),
            'ACTLEXPTOTALAMT': head_obj.get('actlexptotalamt', ''),
            'MTPCKITEMCNT': head_obj.get('mtpckitemcnt', ''),
            'ENDPRDITEMCNT': head_obj.get('endprditemcnt', ''),
            'MAXTOVRAMT': head_obj.get('maxtovramt', ''),
            'MASTERCUSCD': head_obj.get('mastercuscd', ''),
            'DCLTIME': head_obj.get('dcltime', ''),
            'INPUTETPSTYPECD': head_obj.get('inputetpstypecd', ''),
            'INPUTETPSSCCD': head_obj.get('inputetpssccd', ''),
            'INPUTETPSNM': head_obj.get('inputetpsnm', ''),
            'PUTRECAPPRTIME': head_obj.get('putrecapprtime', ''),
            'CHGAPPRTIME': head_obj.get('chgapprtime', ''),
            'RCNTVCLRTIME': head_obj.get('rcntvclrtime', ''),
            'INPUTTIME': head_obj.get('inputtime', ''),
            'UCNSDCLSEGCD': head_obj.get('ucnsdclsegcd', ''),
            'IMPMAXACCOUNT': head_obj.get('impmaxaccount', ''),
            'VCLRPRIDVAL': head_obj.get('vclrpridval', ''),
            'CHGTMSCNT': head_obj.get('chgtmscnt'),
            'FINISHVALIDDATE': head_obj.get('finishvaliddate', ''),
        }
        _d = copy.deepcopy(d)
        for k in _d:
            if _d[k]:
                pass
            else:
                d.pop(k)
        if self.sql.insert('NemsHead', **d):
            log.info('账册号{}已插入表头信息'.format(nemsno))
            return True
        else:
            log.error('账册号{}插入表头信息失败，请检查..'.format(nemsno))
            raise Exception('账册号{}插入表头信息失败，请检查..'.format(nemsno))

    def get_local_db_max_gdsseqno(self, tabname, seqNo):
        _sql = 'SELECT max(GDSSEQNO) as gdsSeqno FROM {} WHERE SEQNO = {}'.format(tabname, seqNo)
        ret = self.sql.raw_sql(_sql)
        if ret.get('status'):
            gdsSeqno = ret['ret_tuples'][0][0]
            return gdsSeqno

    def get_local_db_min_gdsseqno(self, tabname, seqNo):
        _sql = 'SELECT min(GDSSEQNO) as gdsSeqno FROM {} WHERE SEQNO = {}'.format(tabname, seqNo)
        ret = self.sql.raw_sql(_sql)
        if ret.get('status'):
            gdsSeqno = ret['ret_tuples'][0][0]
            return gdsSeqno

    def re_update_imglist_db(self, gdsSeqno, response_dict):
        ret = False
        for data in response_dict['rows']:
            if int(data['gdsseqno']) < gdsSeqno:
                d = {
                    'SEQNO': data.get('seqNo', ''),
                    'GDSSEQNO': data.get('gdsseqno'),
                    'GDSMTNO': data.get('gdsmtno', ''),
                    'GDECD': data.get('gdecd', ''),
                    'GDSNM': data.get('gdsNm', ''),
                    'ENDPRDGDSSPCFMODELDESC': data.get('endprdgdsspcfmodeldesc', ''),
                    'DCLUNITCD': data.get('dclunitcd', ''),
                    'LAWFUNITCD': data.get('lawfunitcd', ''),
                    'DCLUPRC': data.get('dcluprcamt', ''),
                    'DCLCURRCD': data.get('dclcurrcd', ''),
                    'DCLQTY': data.get('dclqty', ''),
                    'LVYRLFMODECD': data.get('lvyrlfmodecd', ''),
                    'ADJMTRMARKCD': data.get('adjmtrmarkcd', ''),
                    'ETPSEXEMARKCD': data.get('etpsexemarkcd', ''),
                    'MODFMARKCD': data.get('modfmarkcd', ''),
                    'VCLRPRIDINITQTY': data.get('vclrpridinitqty', ''),
                    'APPRMAXSURPQTY': data.get('apprmaxsurpqty', ''),
                }
                _d = copy.deepcopy(d)
                for k in _d:
                    if _d[k]:
                        pass
                    else:
                        d.pop(k)
                self.sql.insert('NemsImgList', **d)
                log.info('已更新料件序号：{}'.format(data['gdsseqno']))
                if 1 == int(data['gdsseqno']):
                    ret = True
        return ret

    @error_2_send_email
    def update_imglist_db(self, gdsSeqno, response_dict):
        ret = False
        for data in response_dict['rows']:
            if int(data['gdsseqno']) > gdsSeqno:
                d = {
                    'SEQNO': data.get('seqNo', ''),
                    'GDSSEQNO': data.get('gdsseqno'),
                    'GDSMTNO': data.get('gdsmtno', ''),
                    'GDECD': data.get('gdecd', ''),
                    'GDSNM': data.get('gdsNm', ''),
                    'ENDPRDGDSSPCFMODELDESC': data.get('endprdgdsspcfmodeldesc', ''),
                    'DCLUNITCD': data.get('dclunitcd', ''),
                    'LAWFUNITCD': data.get('lawfunitcd', ''),
                    'DCLUPRC': data.get('dcluprcamt', ''),
                    'DCLCURRCD': data.get('dclcurrcd', ''),
                    'DCLQTY': data.get('dclqty', ''),
                    'LVYRLFMODECD': data.get('lvyrlfmodecd', ''),
                    'ADJMTRMARKCD': data.get('adjmtrmarkcd', ''),
                    'ETPSEXEMARKCD': data.get('etpsexemarkcd', ''),
                    'MODFMARKCD': data.get('modfmarkcd', ''),
                    'VCLRPRIDINITQTY': data.get('vclrpridinitqty', ''),
                    'APPRMAXSURPQTY': data.get('apprmaxsurpqty', ''),
                }
                _d = copy.deepcopy(d)
                for k in _d:
                    if _d[k]:
                        pass
                    else:
                        d.pop(k)
                self.sql.insert('NemsImgList', **d)
                log.info('已更新料件序号：{}'.format(data['gdsseqno']))
                if 1 == int(data['gdsseqno']):
                    ret = True
            else:
                ret = True
        return ret

    @error_2_send_email
    def update_nems_img_list_info(self, nemsno, seqNo):
        """更新料件表"""
        gdsSeqno = self.get_local_db_max_gdsseqno('NemsImgList', seqNo)
        if gdsSeqno is None:
            gdsSeqno = 0
        page = 0
        while True:
            page += 1
            response_dict = self.get_nems_img_list_info(page, seqNo)
            if self.update_imglist_db(gdsSeqno, response_dict):
                _gdsSeqno = self.get_local_db_max_gdsseqno('NemsImgList', seqNo)
                if _gdsSeqno and _gdsSeqno > gdsSeqno:
                    log.info('账册号{}的料件序号已更新至 {}'.format(nemsno, _gdsSeqno))
                else:
                    log.info('海关今日暂未更新账册号为{}的料件..'.format(nemsno))
                return
            else:
                wait_time = random.randint(5, 10)
                log.info('海关今日更新账册号{}的料件序号超过50条，{}秒后将继续爬取第{}页数据..'.format(nemsno, wait_time, page + 1))
                time.sleep(wait_time)
                continue

    def get_nems_img_list_info(self, page, seqNo):
        """料件"""
        url = 'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/atb/emsGoodsQueryService'
        headers = {
            "Host": "sz.singlewindow.cn",
            "Connection": "keep-alive",
            "Content-Length": "132",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "http://sz.singlewindow.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
            "Content-Type": "application/json",
            "Referer": "http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/canadianTradeBooks?sysId=95&flag=view&seqNo={}&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/emspubserver/&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/emspubserver/".format(
                seqNo),
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        data = {
            "copGNo": "",
            "gdecd": "",
            "gdeNm": "",
            "page": {"curPage": page, "pageSize": 50},
            "operType": "0",
            "seqNO": seqNo,
            "queryType": "Img",
        }
        self.session.headers.update(headers)
        self.session.cookies.update(self.get_cookie())
        http_res = self.session.post(url, data=json.dumps(data), timeout=20)
        return json.loads(http_res.text)

    @error_2_send_email
    def re_update_ems_img_list_db(self, nemsno, seqNo):
        """中断后继续更新"""
        gdsSeqno = self.get_local_db_min_gdsseqno('NemsImgList', seqNo)
        if gdsSeqno is None:
            gdsSeqno = 0
        page = 324
        while True:
            page += 1
            response_dict = self.get_nems_img_list_info(page, seqNo)
            if self.re_update_imglist_db(gdsSeqno, response_dict):
                _gdsSeqno = self.get_local_db_min_gdsseqno('NemsImgList', seqNo)
                if _gdsSeqno and _gdsSeqno < gdsSeqno:
                    log.info('账册号{}的料件序号已更新至 {}'.format(nemsno, _gdsSeqno))
                else:
                    log.info('海关今日暂未更新账册号为{}的料件..'.format(nemsno))
                return
            else:
                wait_time = random.randint(5, 10)
                log.info('海关今日更新账册号{}的料件序号超过50条，{}秒后将继续爬取第{}页数据..'.format(nemsno, wait_time, page + 1))
                time.sleep(wait_time)
                continue

    @error_2_send_email
    def get_nems_exg_list_info(self, page, seqNo):
        """成品"""
        url = 'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/atb/emsGoodsQueryService'
        headers = {
            "Host": "sz.singlewindow.cn",
            "Connection": "keep-alive",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "http://sz.singlewindow.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
            "Content-Type": "application/json",
            "Referer": "http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/canadianTradeBooks?sysId=95&flag=view&seqNo={}&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/emspubserver/&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/emspubserver/".format(
                seqNo),
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        data = {"copGNo": "", "gdecd": "", "gdeNm": "", "page": {"curPage": page, "pageSize": 50}, "operType": "0",
                "seqNO": seqNo, "queryType": "Exg"}
        self.session.headers.update(headers)
        self.session.cookies.update(self.get_cookie())
        http_res = self.session.post(url, data=json.dumps(data), timeout=20)
        return json.loads(http_res.text)

    def get_info(self):
        for i, response_dict in self.get_company_seqno():
            for obj in response_dict.get('rows'):
                seqNo = obj.get('seqNo')
                self.get_nems_info(i, seqNo)

    def get_nems_info(self, nemsno, seqNo):
        self.update_nems_head_db(nemsno, seqNo)
        if "201800000000002605" == seqNo:
            self.re_update_ems_img_list_db(nemsno, seqNo)
        else:
            self.update_nems_img_list_info(nemsno, seqNo)
        self.update_nems_exg_list_info(nemsno, seqNo)
