#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-08-7 11:54:13
# @Author  : Zzaniu (Zzaniu@126.com)
# @Link    : http://example.org
# @Version : $Id$
import copy
import json
import random
import time
from conf import settings
from hgSpider.basecls import BaseCls
from lib.mail import error_2_send_email, send_email
from lib.log import getSpiderLogger

log = getSpiderLogger()


class BwlListSpider(BaseCls):
    def __init__(self, *args, **kwargs):
        super(BwlListSpider, self).__init__(*args, **kwargs)
        self.CookieUrl = settings.BWLCOOKIE_URL
        self.RealListUrl = settings.BWLREAL_LIST_URL
        self.RealHeadUrl = settings.BWLREAL_HEAD_URL
        self.QueryUrl = settings.BWL_QUERY_URL
        self.CompanyList = settings.BWL_COMPANY_LIST
        self.pagesize = settings.pageSize

    def update_bwlist_db(self, gdsSeqno, response_dict, bwlno):
        """因为顺序是未知的，所以需要遍历完整个json"""
        assert response_dict['rows'], '海关暂无相关物流账册{}表体信息...'.format(bwlno)
        ret = False
        for data in response_dict['rows']:
            if int(data['gdsSeqNo']) > gdsSeqno:
                self.update_db_list(data, bwlno)
                if 1 == int(data['gdsSeqNo']):
                    ret = True
            else:
                ret = True
        return ret

    def re_update_bwlist_db(self, gdsSeqno, response_dict, nemsno):
        ret = False
        for data in response_dict['rows']:
            if int(data['gdsSeqNo']) < gdsSeqno:
                self.update_db_list(data, nemsno)
                if 1 == int(data['gdsSeqNo']):
                    ret = True
        return ret

    @error_2_send_email
    def update_db_list(self, data, bwlno):
        seqno = data.get('seqNo')
        print('data = ', data)
        BwlList2Head = self.sql.select('BwlHeadType', 'Id', where={'SeqNo': seqno})
        if BwlList2Head:
            BwlList2Head = BwlList2Head[0][0]
        else:
            raise Exception('SeqNo:{}發生錯誤，表頭數據不存在'.format(seqno))
        d = {
            'SeqNo': seqno,
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
            'SecdLawfUnitcd': data.get('secdLawfUnitCd'),
            'BwlList2Head': BwlList2Head,
        }
        _d = copy.deepcopy(d)
        for k in _d:
            if _d[k]:
                pass
            else:
                d.pop(k)
        self.sql.insert('BwlListType', **d)

        log.info('物流账册{}[SeqNo:{}]已更新標體序号：{}'.format(bwlno, seqno, data['gdsSeqNo']))

    def get_local_db_max_or_min_gseqno(self, seqno, max=True):
        if max:
            _sql = "SELECT max(GdsSeqno) as gdsSeqno FROM BwlListType WHERE SeqNo = %s"
        else:
            _sql = "SELECT min(GdsSeqno) as gdsSeqno FROM BwlListType WHERE SeqNo = %s"
        ret = self.sql.raw_sql(_sql, seqno)
        if ret.get('status'):
            gdsSeqno = ret['ret_tuples'][0][0]
            return gdsSeqno

    def update_bwl_list_info(self, bwlno, seqno):
        has_breakpoint = False
        max_gSeqno = self.get_local_db_max_or_min_gseqno(seqno)
        min_gSeqno = self.get_local_db_max_or_min_gseqno(seqno, max=False)
        if max_gSeqno is None:
            max_gSeqno = 0
        else:
            if min_gSeqno > 1:
                has_breakpoint = True
        page = 0
        while True:
            page += 1
            response_dict = self.get_bwl_list_info(page, seqno)
            if has_breakpoint:
                if self.re_update_bwlist_db(min_gSeqno, response_dict, bwlno):
                    _gSeqno = self.get_local_db_max_or_min_gseqno(seqno, max=False)
                    if 1 == _gSeqno:
                        log.info('物流账册{}的表体序号已更新至 {}'.format(bwlno, _gSeqno))
                        return
                else:
                    wait_time = random.randint(5, 10)
                    log.info(
                        '海关今日更新物流账册{}的表体序号超过{}条，{}秒后将继续爬取第{}页数据..'.format(bwlno, self.pagesize, wait_time, page + 1))
                    time.sleep(wait_time)
                    continue
            else:
                try:
                    if self.update_bwlist_db(max_gSeqno, response_dict, bwlno):
                        _gdsSeqno = self.get_local_db_max_or_min_gseqno(seqno)
                        if _gdsSeqno and _gdsSeqno > max_gSeqno:
                            log.info('企业{}备案序号已更新至 {}'.format(bwlno, _gdsSeqno))
                        else:
                            log.info('海关今日暂未更新企业{}备案序号..'.format(bwlno))
                        return
                    else:
                        log.info('海关今日更新企业{}备案序号超过{}条，5~10秒后将继续爬取第{}页数据..'.format(bwlno, self.pagesize, page + 1))
                        time.sleep(random.randint(5, 10))
                        continue
                except Exception as e:
                    log.info(str(e))
                    return

    @error_2_send_email
    def get_bwl_list_info(self, page, seqno):
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
            'Referer': 'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwl?sysId=Z8&flag=view&seqNo={}&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/emspubserver/&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/emspubserver/'.format(
                seqno)
        }
        postdata = {
            "page": {"curPage": page, "pageSize": settings.pageSize},
            "queryType": "B", "operType": "0", "seqNo": seqno, "operCusRegCode": '4403180896',
        }
        self.session.headers.update(headers)
        self.session.cookies.update(self.get_cookie())
        http_res = self.session.post(self.RealListUrl, data=json.dumps(postdata), timeout=30)
        response_dict = json.loads(http_res.text)
        return response_dict

    @error_2_send_email
    def update_bwl_head_db(self, bwlno, seqNo):
        """插入表头"""
        if self.sql.select('BwlHeadType', 'id', where={'SeqNo': seqNo}):
            log.info('物流账册号{},seq-{}已存在'.format(bwlno, seqNo))
            return True
        head_dict = self.get_bwl_head_info(seqNo).get('data')
        head_obj = head_dict.get('bwlHead')
        d = {
            'SeqNo': head_obj.get('seqNo', ''),
            'BwlNo': head_obj.get('bwlNo', ''),
            # 'ChgTmsCnt': head_obj.get('chgTmsCnt', ''),
            'DclTypecd': head_obj.get('dclTypeCd', ''),
            'BwlTypecd': head_obj.get('bwlTypeCd', ''),
            'MasterCuscd': head_obj.get('masterCuscd', ''),
            'BizopEtpsSccd': head_obj.get('bizopEtpsSccd', ''),
            'BizopEtpsno': head_obj.get('bizopEtpsno', ''),
            'BizopEtpsNm': head_obj.get('bizopEtpsNm', ''),
            'DclEtpsSccd': head_obj.get('dclEtpsSccd', ''),
            'DclEtpsno': head_obj.get('dclEtpsno', ''),
            'DclEtpsNm': head_obj.get('dclEtpsNm', ''),
            'DclEtpsTypecd': head_obj.get('dclEtpsTypeCd', ''),
            'ContactEr': head_obj.get('contactEr', ''),
            'ContactTele': head_obj.get('contactTele', ''),
            'HouseTypecd': head_obj.get('houseTypeCd', ''),
            'Houseno': head_obj.get('houseNo', ''),
            'HouseNm': head_obj.get('houseNm', ''),
            'HouseArea': head_obj.get('houseArea', ''),
            'HouseVolume': head_obj.get('houseVolume', ''),
            'HouseAdderss': head_obj.get('houseAddress', ''),
            # 'VALIDDATE': head_obj.get('dclTime', ''),
            # 'REDUNATRCD': head_obj.get('inputDate', ''),
            # 'PRODUCETYPECD': head_obj.get('putrecApprTime', ''),
            # 'IMPEXPPORTCD': head_obj.get('chgApprTime', ''),
            'FinishValidDate': head_obj.get('finishValidTime', ''),
            # 'EXPCURRCD': head_obj.get('pauseChgMarkCd', ''),
            # 'UCNSDCLSEGCD': head_obj.get('emapvStucd', ''),
            # 'STNDBKBANKCD': head_obj.get('dclMarkCd', ''),
            'AppendTypecd': head_obj.get('appendTypeCd', ''),
            'Rmk': head_obj.get('rmk', ''),
            'InputCode': head_obj.get('inputCode', ''),
            'InputSccd': head_obj.get('inputSccd', ''),
            'InputName': head_obj.get('inputName', ''),
            # 'PRODUCTRATIO': head_obj.get('addTime', ''),
        }
        _d = copy.deepcopy(d)
        for k in _d:
            if _d[k]:
                pass
            else:
                d.pop(k)
        try:
            ret = self.sql.insert('BwlHeadType', **d)
        except Exception as e:
            log.info('物流账册号{}[SeqNo:{}]估计是暂存的数据，数据不完整，跳过爬取'.format(bwlno, seqNo))
            return True
        if ret:
            log.info('手册号{}[SeqNo:{}]已插入表头信息'.format(bwlno, seqNo))
            return True
        else:
            log.error('手册号{}[SeqNo:{}]插入表头信息失败，请检查..'.format(bwlno, seqNo))
            # raise Exception('手册号{}插入表头信息失败，请检查..'.format(bwlno))

    def get_bwl_head_info(self, seqNo):
        """获取表头数据"""
        headers = {
            "Host": "sz.singlewindow.cn",
            "Connection": "keep-alive",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "http://sz.singlewindow.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
            "Content-Type": "application/json;charset=UTF-8",
            "Referer": "http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwl?sysId=Z8&flag=view&seqNo={}&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/emspubserver/&ngBasePath=http://sz.singlewindow.cn:80/dyck/swProxy/emspubserver/".format(
                seqNo),
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            'Cache-Control': None,
            'Content-Length': None,
        }
        postdata = {"seqNo": seqNo, "operCusRegCode": "4403180896"}
        self.session.headers.update(headers)
        self.session.cookies.update(self.get_cookie())
        http_res = self.session.post(self.RealHeadUrl, data=json.dumps(postdata), timeout=30)
        return json.loads(http_res.text)

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
            "Referer": "http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwlQueryList?sysId=Z8&ngBasePath=http%3A%2F%2Fsz.singlewindow.cn%3A80%2Fdyck%2FswProxy%2Femspubserver%2F",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        postdata = {"sysId": "Z8", "status": " ", "statusName": "全部", "selTradeCode": "", "bwlNo": "", "seqNo": "",
                    "bizopEtpsno": "", "bizopEtpsSccd": "", "inputDateStart": "", "inputDateEnd": "",
                    "inputCode": "4403180896"}
        self.session.headers.update(headers)
        self.session.cookies.update(self.get_cookie())
        for i in self.CompanyList:
            postdata['selTradeCode'] = i
            http_res = self.session.post(self.QueryUrl, data=json.dumps(postdata), timeout=30)
            try:
                response_dict = json.loads(http_res.text)
                yield i, response_dict
            except:
                self.session.cookies.update(self.get_cookie(LOCAL_COOKIE_FLG=False))
                http_res = self.session.post(self.QueryUrl, data=json.dumps(postdata), timeout=30)
                try:
                    response_dict = json.loads(http_res.text)
                    yield i, response_dict
                except:
                    raise Exception('获取公司seqNo失败，请检查程序...')

    def get_info(self):
        for i, response_dict in self.get_company_seqno():
            for obj in response_dict.get('data').get('resultList'):
                seqNo = obj.get('seqNo')
                self.get_bwl_info(i, seqNo)

    def get_bwl_info(self, bwlno, seqNo):
        """这里可以考虑做成多线程，主要是怕把海关搞挂了，对性能也没有要求，就先单线程跑着吧"""
        self.update_bwl_head_db(bwlno, seqNo)
        self.update_bwl_list_info(bwlno, seqNo)
        # self.update_by_field(bwlno, seqNo)

    def update_by_field(self, bwlno, seqno):
        page = 0
        while True:
            page += 1
            response_dict = self.get_bwl_list_info(page, seqno)
            if not response_dict['rows']:
                return
            try:
                self.update_db_list_by_field(response_dict, bwlno, seqno)
                if (page + 1) * settings.pageSize > int(response_dict.get('total')):
                    return
            except Exception as e:
                log.info(str(e))
                return

    def update_db_list_by_field(self, response_dict, bwlno, seqno):
        for data in response_dict['rows']:
            if data.get('secdLawfUnitCd'):
                d = {
                    'SecdLawfUnitcd': data.get('secdLawfUnitCd'),
                }
                _d = copy.deepcopy(d)
                for k in _d:
                    if _d[k]:
                        pass
                    else:
                        d.pop(k)
                self.sql.update('BwlListType', where={'SeqNo': seqno, 'GdsSeqno': data.get('gdsSeqNo')}, **d)
                log.info('物流账册{}已更新单损耗序号：{}'.format(bwlno, data['gdsSeqNo']))
            else:
                continue


class BwlList2Nems(BwlListSpider):
    """返填核注清单"""

    def return_nems(self, data):
        invtNo = data['invtNo']  # 海关编号
        invtGNo = data['invtGNo']  # 商品序号
        nid = self.sql.select('NRelation', 'Id', where={'QpEntryId': invtNo, 'DeleteFlag': 0})
        if not nid: return
        nid = nid[0][0]
        nems_head_id = self.sql.select('NemsInvtHeadType', 'Id', where={'NId': nid})
        if not nems_head_id: return
        nems_head_id = nems_head_id[0][0]
        self.sql.update('NemsInvtListType', where={'FKey': nems_head_id, 'GdsSeqno': invtGNo}, PutrecSeqno=data.get('gdsSeqNo'))

    @error_2_send_email
    def update_db_list(self, data, bwlno):
        seqno = data.get('seqNo')
        print('data = ', data)
        BwlList2Head = self.sql.select('BwlHeadType', 'Id', where={'SeqNo': seqno})
        if BwlList2Head:
            BwlList2Head = BwlList2Head[0][0]
        else:
            raise Exception('SeqNo:{}發生錯誤，表頭數據不存在'.format(seqno))
        d = {
            'SeqNo': seqno,
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
            'SecdLawfUnitcd': data.get('secdLawfUnitCd'),
            'BwlList2Head': BwlList2Head,
        }
        _d = copy.deepcopy(d)
        for k in _d:
            if _d[k]:
                pass
            else:
                d.pop(k)
        self.sql.insert('BwlListType', **d)
        self.return_nems(data)
        log.info('物流账册{}[SeqNo:{}]已更新標體序号：{}'.format(bwlno, seqno, data['gdsSeqNo']))


if __name__ == "__main__":
    # a = BwlListSpider()
    a = BwlList2Nems()
    a.get_info()
    # for i, response_dict in a.get_company_seqno():
    #     print('i = ', i, 'response_dict = ', response_dict)
