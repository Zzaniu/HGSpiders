#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-08-13 09:50:44
# @Author  : zaniu (Zzaniu@126.com)
# @Version : $Id$
import copy
import json
import random
import time

from conf import settings
from hgSpider.basecls import BaseCls
from lib.mail import error_2_send_email
from lib.log import getSpiderLogger

log = getSpiderLogger()


class NptsSpider(BaseCls):
    """金二加工贸易电子帐册"""

    def __init__(self, *args, **kwargs):
        super(NptsSpider, self).__init__(*args, **kwargs)
        self.CookieUrl = settings.NPTSCOOKIE_URL
        self.RealUrl = r'http://sz.singlewindow.cn/dyck/swProxy/nptsserver/sw/ems/npts/eml/emlQueryListService'
        self.RealUrl2 = r'http://sz.singlewindow.cn/dyck/swProxy/nptsserver/sw/ems/npts/eml/emsDetailService'
        self.RealUrl3 = r'http://sz.singlewindow.cn/dyck/swProxy/nptsserver/sw/ems/npts/eml/emlGoodsQueryService'
        self.CompanyList = settings.NPTS_COMPANY_LIST

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
        self.session.cookies.update({"loginSignal": '0'})
        self.save_cookie()
        return self.session.cookies.get_dict()

    def update_npts_cm_list_info(self, nptsno, seqNo):
        has_breakpoint = False
        max_gSeqno = self.get_local_db_max_or_min_gseqno('NptsEmlConsumeType', seqNo)
        min_gSeqno = self.get_local_db_max_or_min_gseqno('NptsEmlConsumeType', seqNo, max=False)
        # 只要有最大值，且最小值不是1，说明上次爬的过程中中断了，要往后面找，一直更新到1.第二天再更新海关新增的
        if max_gSeqno is None:
            max_gSeqno = 0
        else:
            if min_gSeqno > 1:
                has_breakpoint = True
        page = 0
        while True:
            page += 1
            response_dict = self.get_npts_cm_list_info(page, seqNo)
            if has_breakpoint:
                if self.re_update_cmlist_db(min_gSeqno, response_dict, nptsno):
                    _gSeqno = self.get_local_db_max_or_min_gseqno('NptsEmlConsumeType', seqNo, max=False)
                    if 1 == _gSeqno:
                        log.info('手册号{}的单损耗序号已更新至 {}'.format(nptsno, _gSeqno))
                        return
                else:
                    wait_time = random.randint(5, 10)
                    log.info('海关今日更新手册号{}的单损耗序号超过50条，{}秒后将继续爬取第{}页数据..'.format(nptsno, wait_time, page + 1))
                    time.sleep(wait_time)
                    continue
            else:
                if self.update_cmlist_db(max_gSeqno, response_dict, nptsno):
                    _gSeqno = self.get_local_db_max_or_min_gseqno('NptsEmlConsumeType', seqNo)
                    if _gSeqno and _gSeqno > max_gSeqno:
                        log.info('手册号{}的单损耗序号已更新至 {}'.format(nptsno, _gSeqno))
                    else:
                        log.info('海关今日暂未更新手册号为{}的单损耗..'.format(nptsno))
                    return
                else:
                    wait_time = random.randint(5, 10)
                    log.info('海关今日更新手册号{}的单损耗序号超过50条，{}秒后将继续爬取第{}页数据..'.format(nptsno, wait_time, page + 1))
                    time.sleep(wait_time)
                    continue

    @error_2_send_email
    def get_local_db_max_or_min_gseqno(self, tabname, seqNo, max=True):
        if max:
            _sql = 'SELECT max(GSEQNO) as gSeqno FROM {} WHERE SEQNO = {}'.format(tabname, seqNo)
        else:
            _sql = 'SELECT min(GSEQNO) as gSeqno FROM {} WHERE SEQNO = {}'.format(tabname, seqNo)
        ret = self.sql.raw_sql(_sql)
        if ret.get('status'):
            gSeqno = ret['ret_tuples'][0][0]
            return gSeqno

    @error_2_send_email
    def update_npts_exg_list_info(self, nptsno, seqNo):
        has_breakpoint = False
        max_gdsSeqno = self.get_local_db_max_or_min_gdsseqno('NptsEmlExgType', seqNo)
        min_gdsSeqno = self.get_local_db_max_or_min_gdsseqno('NptsEmlExgType', seqNo, max=False)
        if max_gdsSeqno is None:
            max_gdsSeqno = 0
        else:
            if min_gdsSeqno > 1:
                has_breakpoint = True
        page = 0
        while True:
            page += 1
            response_dict = self.get_npts_exg_list_info(page, seqNo)
            if has_breakpoint:
                if self.re_update_exglist_db(min_gdsSeqno, response_dict, nptsno):
                    _gdsSeqno = self.get_local_db_max_or_min_gdsseqno('NptsEmlExgType', seqNo, max=False)
                    if 1 == _gdsSeqno:
                        log.info('手册号{}的成品序号已更新至 {}'.format(nptsno, _gdsSeqno))
                        return
                else:
                    wait_time = random.randint(5, 10)
                    log.info('海关今日更新手册号{}的成品序号超过50条，{}秒后将继续爬取第{}页数据..'.format(nptsno, wait_time, page + 1))
                    time.sleep(wait_time)
                    continue
            else:
                if self.update_exglist_db(max_gdsSeqno, response_dict, nptsno):
                    _gdsSeqno = self.get_local_db_max_or_min_gdsseqno('NptsEmlExgType', seqNo)
                    if _gdsSeqno and _gdsSeqno > max_gdsSeqno:
                        log.info('手册号{}的成品序号已更新至 {}'.format(nptsno, _gdsSeqno))
                    else:
                        log.info('海关今日暂未更新手册号为{}的成品..'.format(nptsno))
                    return
                else:
                    wait_time = random.randint(5, 10)
                    log.info('海关今日更新手册号{}的成品序号超过50条，{}秒后将继续爬取第{}页数据..'.format(nptsno, wait_time, page + 1))
                    time.sleep(wait_time)
                    continue

    @error_2_send_email
    def updata_db_exg(self, data, nptsno):
        d = {
            'SEQNO': data.get('seqNo'),
            'GDSSEQNO': data.get('gdsSeqno'),
            'GDSMTNO': data.get('gdsMtno', ''),
            'GDECD': data.get('gdecd', ''),
            'GDSNM': data.get('gdsNm', ''),
            'ENDPRDGDSSPCFMODELDESC': data.get('endprdGdsSpcfModelDesc', ''),
            'DCLUNITCD': data.get('dclUnitcd', ''),
            'LAWFUNITCD': data.get('lawfUnitcd', ''),
            'DCLUPRC': data.get('dclUprcAmt', ''),
            'DCLCURRCD': data.get('dclCurrcd', ''),
            'DCLQTY': data.get('dclQty', ''),
            'DCLTOTALPRC': data.get('dclTotalAmt', ''),
            'PRMKTNATCD': data.get('natcd', ''),
            'LVYRLFMODECD': data.get('lvyrlfModecd', ''),
            'MODFMARKCD': data.get('modfMarkcd', ''),
            'CUSMEXEMARKCD': data.get('cusmExeMarkcd', ''),
            'UCNSTQSNFLAG': data.get('ucnsTqsnFlag', ''),
            'CSTTNFLAG': data.get('csttnFlag', ''),
        }
        _d = copy.deepcopy(d)
        for k in _d:
            if _d[k]:
                pass
            else:
                d.pop(k)
        self.sql.insert('NptsEmlExgType', **d)
        log.info('手册号{}已更新成品序号：{}'.format(nptsno, data['gdsSeqno']))

    def update_exglist_db(self, gdsSeqno, response_dict, nptsno):
        ret = False
        for data in response_dict['rows']:
            if int(data['gdsSeqno']) > gdsSeqno:
                self.updata_db_exg(data, nptsno)
                if 1 == int(data['gdsSeqno']):
                    ret = True
            else:
                ret = True
        return ret

    def re_update_exglist_db(self, gdsSeqno, response_dict, nptsno):
        ret = False
        for data in response_dict['rows']:
            if int(data['gdsSeqno']) < gdsSeqno:
                self.updata_db_exg(data, nptsno)
                if 1 == int(data['gdsSeqno']):
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
        postdata = {"sysId": "B1", "status": " ", "statusName": "全部", "selTradeCode": "", "emlNo": "",
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
    def get_npts_head_info(self, seqNo):
        """获取表头数据"""
        headers = {
            "Host": "sz.singlewindow.cn",
            "Connection": "keep-alive",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "http://sz.singlewindow.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
            "Content-Type": "application/json;charset=UTF-8",
            "Referer": "http://sz.singlewindow.cn/dyck/swProxy/nptsserver/sw/ems/npts/eml?flag=view&seqNo={}&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/nptsserver/&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/nptsserver/".format(
                seqNo),
            "Accept-Language": "zh-CN,zh;q=0.9",
            'Cache-Control': None,
            'Content-Length': None,
        }
        postdata = {"seqNo": seqNo}
        self.session.headers.update(headers)
        self.session.cookies.update(self.get_cookie())
        http_res = self.session.post(self.RealUrl2, data=json.dumps(postdata), timeout=20)
        print('http_res.text = ', http_res.text)
        return json.loads(http_res.text)

    @error_2_send_email
    def update_npts_head_db(self, nptsno, seqNo):
        """插入表头"""
        if self.sql.select('NptsEmlHead', 'id', where={'SEQNO': seqNo}):
            log.info('手册号{}已存在'.format(nptsno))
            return True
        head_obj = self.get_npts_head_info(seqNo).get('data').get('nptsEmlHead')
        d = {
            'SEQNO': head_obj.get('seqNo', ''),
            'EMLNO': head_obj.get('emlNo', ''),
            'ETPSPREENTNO': head_obj.get('etpsPreentNo', ''),
            'MSTERCUSCD': head_obj.get('masterCuscd', ''),
            'EMLTYPE': head_obj.get('emlType', ''),
            'DCLTYPECD': head_obj.get('dclTypecd', ''),
            'BIZOPETPSNO': head_obj.get('bizopEtpsno', ''),
            'BIZOPETPSSCCD': head_obj.get('bizopEtpsSccd', ''),
            'BIZOPETPSNM': head_obj.get('bizopEtpsNm', ''),
            'RCVGDETPSNO': head_obj.get('rcvgdEtpsno', ''),
            'RVSNGDETPSSCCD': head_obj.get('rvsngdEtpsSccd', ''),
            'RCVGDETPSNM': head_obj.get('rcvgdEtpsNm', ''),
            'DCLETPSNO': head_obj.get('dclEtpsno', ''),
            'DCLETPSSCCD': head_obj.get('dclEtpsSccd', ''),
            'DCLETPSNM': head_obj.get('dclEtpsNm', ''),
            'RCVGDETPSDTCD': head_obj.get('rcvgdEtpsDtcd', ''),
            'DCLETPSTYPECD': head_obj.get('dclEtpsTypecd', ''),
            'DCLTIME': head_obj.get('dclTime', ''),
            'SUPVMODECD': head_obj.get('supvModecd', ''),
            'IMPCTRTNO': head_obj.get('impCtrtNo', ''),
            'EXPCTRTNO': head_obj.get('expCtrtNo', ''),
            'VALIDDATE': head_obj.get('validDate', ''),
            'REDUNATRCD': head_obj.get('reduNatrcd', ''),
            'PRODUCETYPECD': head_obj.get('produceTypecd', ''),
            'IMPEXPPORTCD': head_obj.get('impexpPortcd', ''),
            'IMPCURRCD': head_obj.get('impCurrcd', ''),
            'EXPCURRCD': head_obj.get('expCurrcd', ''),
            'UCNSDCLSEGCD': head_obj.get('ucnsDclSegcd', ''),
            'STNDBKBANKCD': head_obj.get('stndbkBankcd', ''),
            'PAUSEIMPEXPMARKCD': head_obj.get('pauseImpexpMarkcd', ''),
            'INPUTETPSTYPECD': head_obj.get('inputEtpsTypecd', ''),
            'INPUTETPSSCCD': head_obj.get('inputEtpsSccd', ''),
            'INPUTETPSNM': head_obj.get('inputEtpsNm', ''),
            'INPUTTIME': head_obj.get('inputTime', ''),
            'PRODUCTRATIO': head_obj.get('productRatio', ''),
            'PAUSECHGMARKCD': head_obj.get('pauseChgMarkcd', ''),
            'LINKMAN': head_obj.get('linkMan', ''),
            'LINKMANTEL': head_obj.get('linkManTel', ''),
            'ETPSPOSESSADJAQUAFLAG': head_obj.get('etpsPosesSadjaQuaFlag', ''),
            'CHGTMSCNT': head_obj.get('chgTmsCnt', ''),
            'FTIMEEXP': head_obj.get('ftimeExp', ''),
            'RMK': head_obj.get('rmk', ''),
            'OWNERETPSSCCD': head_obj.get('rmk', ''),
            'OWNERETPSNO': head_obj.get('rmk', ''),
            'OWNERETPSNM': head_obj.get('rmk', ''),
        }
        _d = copy.deepcopy(d)
        for k in _d:
            if _d[k]:
                pass
            else:
                d.pop(k)
        if self.sql.insert('NptsEmlHead', **d):
            log.info('手册号{}已插入表头信息'.format(nptsno))
            return True
        else:
            log.error('手册号{}插入表头信息失败，请检查..'.format(nptsno))
            raise Exception('手册号{}插入表头信息失败，请检查..'.format(nptsno))

    @error_2_send_email
    def get_local_db_max_or_min_gdsseqno(self, tabname, seqNo, max=True):
        if max:
            _sql = 'SELECT max(GDSSEQNO) as gdsSeqno FROM {} WHERE SEQNO = {}'.format(tabname, seqNo)
        else:
            _sql = 'SELECT min(GDSSEQNO) as gdsSeqno FROM {} WHERE SEQNO = {}'.format(tabname, seqNo)
        ret = self.sql.raw_sql(_sql)
        if ret.get('status'):
            gdsSeqno = ret['ret_tuples'][0][0]
            return gdsSeqno

    @error_2_send_email
    def update_db_cm(self, data, nptsno):
        d = {
            'SEQNO': data.get('seqNo'),
            'GSEQNO': data.get('gseqNo'),
            'ENDPRDSEQNO': data.get('endprdSeqno'),
            'ENDPRDGDSMTNO': data.get('endprdGdsMtno', ''),
            'ENDPRDGDECD': data.get('endprdGdecd', ''),
            'ENDPRDGDENM': data.get('endprdGdsNm', ''),
            'MTPCKSEQNO': data.get('mtpckSeqno'),
            'GDSMTNO': data.get('mtpckGdsMtno', ''),
            'MTPCKGDECD': data.get('mtpckGdecd', ''),
            'MTPCKGDSNM': data.get('mtpckGdsNm', ''),
            'UCNSVERNO': data.get('ucnsVerno', ''),
            'UCNSQTY': data.get('ucnsQty', ''),
            'NETUSEUPQTY': data.get('netUseupQty', ''),
            'TGBLLOSSRATE': data.get('tgblLossRate', ''),
            'INTGBLOSSRATE': data.get('intgbLossRate', ''),
            'UCNSDCLSTUCD': data.get('ucnsDclStucd', ''),
            'BONDMTPCKPRPR': data.get('bondMtpckPrpr', ''),
            'MODFMARKCD': data.get('modfMarkcd', ''),
            'ETPSEXEMARKCD': data.get('etpsExeMarkcd', ''),
        }
        _d = copy.deepcopy(d)
        for k in _d:
            if _d[k]:
                pass
            else:
                d.pop(k)
        self.sql.insert('NptsEmlConsumeType', **d)
        log.info('手册号{}已更新单损耗序号：{}'.format(nptsno, data['gseqNo']))

    def re_update_cmlist_db(self, gSeqno, response_dict, nptsno):
        ret = False
        for data in response_dict['rows']:
            if int(data['gseqNo']) < gSeqno:
                self.update_db_cm(data, nptsno)
                if 1 == int(data['gseqNo']):
                    ret = True
        return ret

    def update_cmlist_db(self, gSeqno, response_dict, nptsno):
        ret = False
        for data in response_dict['rows']:
            if int(data['gseqNo']) > gSeqno:
                self.update_db_cm(data, nptsno)
                if 1 == int(data['gseqNo']):
                    ret = True
            else:
                ret = True
        return ret

    @error_2_send_email
    def update_db_img(self, data, nptsno):
        d = {
            'SEQNO': data.get('seqNo', ''),
            'GDSSEQNO': data.get('gdsSeqno'),
            'GDSMTNO': data.get('gdsMtno', ''),
            'GDECD': data.get('gdecd', ''),
            'GDSNM': data.get('gdsNm', ''),
            'ENDPRDGDSSPCFMODELDESC': data.get('endprdGdsSpcfModelDesc', ''),
            'DCLUNITCD': data.get('dclUnitcd', ''),
            'LAWFUNITCD': data.get('lawfUnitcd', ''),
            'DCLUPRC': data.get('dclUprcAmt', ''),
            'DCLCURRCD': data.get('dclCurrcd', ''),
            'DCLQTY': data.get('dclQty', ''),
            'DCLTOTALPRC': data.get('dclTotalAmt', ''),
            'PRMKTNATCD': data.get('natcd', ''),
            'LVYRLFMODECD': data.get('lvyrlfModecd', ''),
            'ADTMTRMARKCD': data.get('adjmtrMarkcd', ''),
            'MODFMARKCD': data.get('modfMarkcd', ''),
            'CUSMEXEMARKCD': data.get('cusmExeMarkcd', ''),
        }
        _d = copy.deepcopy(d)
        for k in _d:
            if _d[k]:
                pass
            else:
                d.pop(k)
        self.sql.insert('NptsEmlImgType', **d)
        log.info('手册号{}已更新料件序号：{}'.format(nptsno, data['gdsSeqno']))

    def update_imglist_db(self, gdsSeqno, response_dict, nptsno):
        ret = False
        for data in response_dict['rows']:
            if int(data['gdsSeqno']) > gdsSeqno:
                self.update_db_img(data, nptsno)
                if 1 == int(data['gdsSeqno']):
                    ret = True
            else:
                ret = True
        return ret

    def re_update_imglist_db(self, gdsSeqno, response_dict, nptsno):
        ret = False
        for data in response_dict['rows']:
            if int(data['gdsSeqno']) < gdsSeqno:
                self.update_db_img(data, nptsno)
                if 1 == int(data['gdsSeqno']):
                    ret = True
        return ret

    @error_2_send_email
    def update_npts_img_list_info(self, nptsno, seqNo):
        """更新料件表"""
        has_breakpoint = False
        max_gdsSeqno = self.get_local_db_max_or_min_gdsseqno('NptsEmlImgType', seqNo)
        min_gdsSeqno = self.get_local_db_max_or_min_gdsseqno('NptsEmlImgType', seqNo, max=False)
        if max_gdsSeqno is None:
            max_gdsSeqno = 0
        else:
            if min_gdsSeqno > 1:
                has_breakpoint = True
        page = 0
        while True:
            page += 1
            response_dict = self.get_npts_img_list_info(page, seqNo)
            if has_breakpoint:
                if self.update_imglist_db(min_gdsSeqno, response_dict, nptsno):
                    _gdsSeqno = self.get_local_db_max_or_min_gdsseqno('NptsEmlImgType', seqNo, max=False)
                    if 1 == _gdsSeqno:
                        log.info('手册号{}的料件序号已更新至 {}'.format(nptsno, _gdsSeqno))
                        return
                else:
                    wait_time = random.randint(5, 10)
                    log.info('海关今日更新手册号{}的料件序号超过50条，{}秒后将继续爬取第{}页数据..'.format(nptsno, wait_time, page + 1))
                    time.sleep(wait_time)
                    continue
            else:
                if self.update_imglist_db(max_gdsSeqno, response_dict, nptsno):
                    _gdsSeqno = self.get_local_db_max_or_min_gdsseqno('NptsEmlImgType', seqNo)
                    if _gdsSeqno and _gdsSeqno > max_gdsSeqno:
                        log.info('手册号{}的料件序号已更新至 {}'.format(nptsno, _gdsSeqno))
                    else:
                        log.info('海关今日暂未更新手册号为{}的料件..'.format(nptsno))
                    return
                else:
                    wait_time = random.randint(5, 10)
                    log.info('海关今日更新手册号{}的料件序号超过50条，{}秒后将继续爬取第{}页数据..'.format(nptsno, wait_time, page + 1))
                    time.sleep(wait_time)
                    continue

    def get_npts_cm_list_info(self, page, seqNo):
        """料件"""
        headers = {
            "Host": "sz.singlewindow.cn",
            "Connection": "keep-alive",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "http://sz.singlewindow.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
            "Content-Type": "application/json",
            "Referer": "http://sz.singlewindow.cn/dyck/swProxy/nptsserver/sw/ems/npts/eml?flag=view&seqNo={}&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/nptsserver/&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/nptsserver/".format(
                seqNo),
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        data = {"endprdSeqno": "", "mtpckSeqno": "", "ucnsVerno": "", "page": {"curPage": page, "pageSize": 50},
                "operType": "0", "seqNo": seqNo, "queryType": "Con"}
        self.session.headers.update(headers)
        self.session.cookies.update(self.get_cookie())
        http_res = self.session.post(self.RealUrl3, data=json.dumps(data), timeout=20)
        print("http_res.text = ", http_res.text)
        return json.loads(http_res.text)

    def get_npts_img_list_info(self, page, seqNo):
        """料件"""
        headers = {
            "Host": "sz.singlewindow.cn",
            "Connection": "keep-alive",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "http://sz.singlewindow.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
            "Content-Type": "application/json",
            "Referer": "http://sz.singlewindow.cn/dyck/swProxy/nptsserver/sw/ems/npts/eml?flag=view&seqNo={}&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/nptsserver/&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/nptsserver/".format(
                seqNo),
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        data = {"gdsMtno": "", "gdecd": "", "gdsNm": "", "page": {"curPage": page, "pageSize": 50}, "operType": "0",
                "seqNo": seqNo, "queryType": "Img"}
        self.session.headers.update(headers)
        self.session.cookies.update(self.get_cookie())
        http_res = self.session.post(self.RealUrl3, data=json.dumps(data), timeout=20)
        print("http_res.text = ", http_res.text)
        return json.loads(http_res.text)

    @error_2_send_email
    def get_npts_exg_list_info(self, page, seqNo):
        """成品"""
        headers = {
            "Host": "sz.singlewindow.cn",
            "Connection": "keep-alive",
            "Content-Length": "133",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "http://sz.singlewindow.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
            "Content-Type": "application/json",
            "Referer": "http://sz.singlewindow.cn/dyck/swProxy/nptsserver/sw/ems/npts/eml?flag=view&seqNo={}&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/nptsserver/&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/nptsserver/".format(
                seqNo),
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        data = {"gdsMtno": "", "gdecd": "", "gdsNm": "", "page": {"curPage": page, "pageSize": 50}, "operType": "0",
                "seqNo": seqNo, "queryType": "Exg"}
        self.session.headers.update(headers)
        self.session.cookies.update(self.get_cookie())
        http_res = self.session.post(self.RealUrl3, headers=headers, data=json.dumps(data), timeout=20)
        print('http_res.text = ', http_res.text)
        return json.loads(http_res.text)

    def get_info(self):
        for ntpsno, response_dict in self.get_company_seqno():
            print('response_dict = ', response_dict)
            for obj in response_dict.get('rows'):
                if obj.get('emlNo'):
                    seqNo = obj.get('seqNo')
                    self.get_npts_info(ntpsno, seqNo)
                else:
                    log.warning('手册号{}的预录入统一编号{}查询页面没有加工贸易手册编号，跳过爬取'.format(ntpsno, seqNo))

    def get_npts_info(self, nptsno, seqNo):
        self.update_npts_head_db(nptsno, seqNo)
        self.update_npts_img_list_info(nptsno, seqNo)
        self.update_npts_exg_list_info(nptsno, seqNo)
        # self.update_npts_cm_list_info(nptsno, seqNo)
