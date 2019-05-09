#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-10-8 11:11:11
# @Author  : Zzaniu (Zzaniu@126.com)
# @Link    : http://example.org
# @Version : $Id$
import copy

from conf import settings
from hgSpider.bwllistspider import BwlListSpider
from lib.log import getSpiderLogger
from lib.mail import error_2_send_email

log = getSpiderLogger()


class SpecialBwlListSpider(BwlListSpider):
    def __init__(self, *args, **kwargs):
        super(SpecialBwlListSpider, self).__init__(*args, **kwargs)
        self.CookieUrl = settings.SPECIAL_BWLCOOKIE_URL
        self.RealListUrl = settings.SPECIAL_BWLREAL_LIST_URL
        self.RealHeadUrl = settings.SPECIAL_BWLREAL_HEAD_URL
        self.QueryUrl = settings.SPECIAL_BWL_QUERY_URL
        self.CompanyList = settings.SPECIAL_BWL_COMPANY_LIST
        self.pagesize = settings.pageSize

    @error_2_send_email
    def update_db_list(self, data, bwlno):
        seqno = data.get('seqNo')
        BwlList2Head = self.sql.select('SpecialBwlHeadType', 'Id', where={'SeqNo': seqno})
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
        self.sql.insert('SpecialBwlListType', **d)
        log.info('物流账册{}[SeqNo:{}]已更新標體序号：{}'.format(bwlno, seqno, data['gdsSeqNo']))

    @error_2_send_email
    def update_bwl_head_db(self, bwlno, seqNo):
        """插入表头"""
        if self.sql.select('SpecialBwlHeadType', 'id', where={'SeqNo': seqNo}):
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
            ret = self.sql.insert('SpecialBwlHeadType', **d)
        except Exception as e:
            log.info('物流账册号{}[SeqNo:{}]估计是暂存的数据，数据不完整，跳过爬取'.format(bwlno, seqNo))
            return True
        if ret:
            log.info('物流账册号{}[SeqNo:{}]已插入表头信息'.format(bwlno, seqNo))
            return True
        else:
            log.error('物流账册号{}[SeqNo:{}]插入表头信息失败，请检查..'.format(bwlno, seqNo))
            # raise Exception('手册号{}插入表头信息失败，请检查..'.format(bwlno))

    def get_local_db_max_or_min_gseqno(self, seqno, max=True):
        if max:
            _sql = "SELECT max(GdsSeqno) as gdsSeqno FROM SpecialBwlListType WHERE SeqNo = %s"
        else:
            _sql = "SELECT min(GdsSeqno) as gdsSeqno FROM SpecialBwlListType WHERE SeqNo = %s"
        ret = self.sql.raw_sql(_sql, seqno)
        if ret.get('status'):
            gdsSeqno = ret['ret_tuples'][0][0]
            return gdsSeqno

if __name__ == "__main__":
    a = SpecialBwlListSpider()
    a.get_info()
    # for i, response_dict in a.get_company_seqno():
    #     print('i = ', i, 'response_dict = ', response_dict)
