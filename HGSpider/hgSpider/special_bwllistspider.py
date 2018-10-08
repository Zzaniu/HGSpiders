#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-10-8 11:11:11
# @Author  : Zzaniu (Zzaniu@126.com)
# @Link    : http://example.org
# @Version : $Id$
from conf import settings
from hgSpider.bwllistspider import BwlListSpider
from lib.log import getSpiderLogger

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


if __name__ == "__main__":
    a = SpecialBwlListSpider()
    a.get_info()
    # for i, response_dict in a.get_company_seqno():
    #     print('i = ', i, 'response_dict = ', response_dict)
