#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2019-01-03 16:52:48
# @Author  : zaniu (Zzaniu@126.com)
# @Version : $Id$

import functools
import os
import random
import re
import json
from time import sleep
from urllib.parse import quote

from lxml import etree
import time
import hashlib
import requests
from aip import AipOcr
from PIL import Image
from conf import settings
from hgSpider.basecls import MySession
from lib.sql import Sql
from lib.mail import error_2_send_email
from lib.log import getSpiderLogger
import multiprocessing

log = getSpiderLogger()


class DgBaseCls(object):
    def __init__(self, *args, **kwargs):
        self.IndexUrl = 'http://app.singlewindow.cn/cas/login?ticket=ST-19837-dDTAKiShmYdjLaz5nQjX-app.singlewindow.cn'
        self.ImageUrl = 'http://app.singlewindow.cn/cas/plat_cas_verifycode_gen?r={}'.format(random.random())
        self.CookieUrl = 'http://www.singlewindow.gd.cn/index.action'
        self.ImageDir = settings.DG_IMAGE_DIR
        self.ImageDir2 = settings.DG_IMAGE_DIR2
        self.CookieDir = settings.DG_COOKIE_DIR
        self.aipOcr = AipOcr(settings.APP_ID, settings.API_KEY, settings.SECRET_KEY)
        self.session = MySession()
        self.sql = Sql(settings.DG_DATABASES)
        self.pagesize = settings.pageSize
        self.header = {
            'Host': 'app.singlewindow.cn',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

    def get_file_content(self):
        image = Image.open(self.ImageDir)
        im = image
        img_grey = im.convert('L')
        threshold = 55
        table = []
        for i in range(256):
            if i < threshold:
                table.append(0)
            else:
                table.append(1)
        img_out = img_grey.point(table, '1')
        img_out.save(self.ImageDir2)
        with open(self.ImageDir2, 'rb') as f:
            return f.read()

    @error_2_send_email
    def get_login_info(self):
        res = self.session.get(self.IndexUrl, headers=self.header, timeout=30)
        content = etree.HTML(res.text)
        lt = content.xpath(r'//*[@id="lt"]/@value')[0]
        execution = content.xpath(r'//*[@id="execution"]/@value')[0]
        return lt, execution

    @error_2_send_email
    def know_Image(self, headers=None, timeout=30):
        start_time = time.time()
        used_time = 0
        ret = {'value': None, 'error': None}
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
                "Connection": "keep-alive",
                "Referer": "http://app.singlewindow.cn/cas/login?ticket=ST-19837-dDTAKiShmYdjLaz5nQjX-app.singlewindow.cn",
            }
        code_count = 0
        while used_time < timeout:
            code_count += 1
            res = self.session.get(self.ImageUrl, headers=headers, timeout=30)
            with open(self.ImageDir, "wb") as f:
                f.write(res.content)
            value = self.aipOcr.basicGeneral(self.get_file_content(), settings.OPTIONS)
            try:
                value = value['words_result'][0]['words'].replace(' ', '')
            except:
                continue
            if 4 == len(value) and re.match('^[0-9a-zA-Z]{4}$', value):
                log.info("已识别验证码%d张，验证码识别成功..." % code_count)
                log.info("验证码是:%r" % value)
                ret['value'] = value
                return ret
            used_time = int(time.time() - start_time)
        ret['error'] = '图片识别程序超时退出...'
        log.warning('图片识别程序超时退出...')
        return ret

    @error_2_send_email
    def get_login_cookie(self):
        lt, execution = self.get_login_info()
        data = {
            'swy': settings.DG_USERNAME,
            'swm': hashlib.md5(settings.DG_PASSWD.encode('utf8')).hexdigest(),
            'swm2': '',
            'verifyCode': self.know_Image().get('value'),
            'lt': lt,
            '_eventId': 'submit',
            'swLoginFlag': 'swUp',
            'lpid': 'P1',
            'execution': execution,
        }
        header = {
            'Origin': 'http://app.singlewindow.cn',
            'Referer': 'http://app.singlewindow.cn/cas/login?ticket=ST-19837-dDTAKiShmYdjLaz5nQjX-app.singlewindow.cn',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        header.update(self.header)
        self.session.headers.update(header)
        res = self.session.post(self.IndexUrl, data=data, timeout=30)
        if res.text.find("登录成功") > 0:
            log.info('模拟登陆成功！！！')
            self.save_cookie()
            return True
        return False

    def save_cookie(self):
        with open(self.CookieDir, "w") as output:
            cookies = self.session.cookies.get_dict()
            json.dump(cookies, output)
        log.info("已在目录下生成cookie文件")

    def get_cookie(self, LOCAL_COOKIE_FLG=True):
        """加长锁，为了防止重复登录"""
        with multiprocessing.Lock():
            if LOCAL_COOKIE_FLG and os.path.exists(self.CookieDir):
                with open(self.CookieDir, "r") as f:
                    cookie = json.load(f)
                    return cookie
            else:
                if os.path.exists(self.CookieDir):
                    os.remove(self.CookieDir)
                return self.get_web_cookie()

    def get_js_cookie(self):
        def get_web_accessId(url):
            header = {
                'Host': 'www.singlewindow.gd.cn',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            }
            _session = requests.session()
            res = _session.get(url, headers=header)
            s = re.search('accessId=([\s\S]+?)&', res.text)
            if s:
                return s.group(1), _session.cookies.get_dict()

        def url_code(_str):
            return quote(_str)
        accessid, cookie_dict = get_web_accessId('http://www.singlewindow.gd.cn/')
        _str = 'http://user-analysis.tycc100.com/service?action=page.load&data='
        _str1 = '&callback=ubaGetCallback'
        _str2 = """{"userId":null,"sessionId":null,"account":"N00000000714","accessId":"%s","platform":{"browserName":"Chrome","browserVersion":"71.0.3578.98","osInfo":"Windows 7 / Server 2008 R2 64-bit","platformDescription":"Chrome 71.0.3578.98 on Windows 7 / Server 2008 R2 64-bit"},"page":{"title":"中国(广东)国际贸易单一窗口","prevUrl":"","currentUrl":"http://www.singlewindow.gd.cn/"},"type":"load","isOpenChat":false,"rootDomain":"singlewindow.gd.cn"}"""%accessid
        _str3 = url_code(_str2)
        url = _str + _str3 + _str1  # 获取那两个baid_id的正确URL
        header = {
            'Host': 'user-analysis.tycc100.com',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'http://www.singlewindow.gd.cn/',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        res = requests.get(url=url, headers=header)
        s = re.search('(\{[\s\S]+?\})', res.text)
        if s:
            _cookie = json.loads(s.group(1))
            _cookie.update(cookie_dict)
            return _cookie, accessid

    def set_js_cookie(self):
        local_cookie = self.get_cookie()
        cookie_dict, accessid = self.get_js_cookie()
        _cookie_dict = {}
        if cookie_dict and cookie_dict.get('success'):
            _cookie_dict['bad_id{}'.format(accessid)] = cookie_dict.get('userId')
            _cookie_dict['nice_id{}'.format(accessid)] = cookie_dict.get('sessionId')
            _cookie_dict['href'] = 'http%3A%2F%2Fwww.singlewindow.gd.cn%2F'
            _cookie_dict['pageViewNum'] = '1'
            _cookie_dict['accessId'] = accessid
            _cookie_dict['JSESSIONID'] = cookie_dict.get('JSESSIONID')
        local_cookie.update(_cookie_dict)
        with open(self.CookieDir, "w") as output:
            json.dump(local_cookie, output)
        log.info('已设置JS cookies')

    @error_2_send_email
    def get_web_cookie(self):
        while not self.get_login_cookie():
            log.info('登陆失败，1S后重新登陆..')
            time.sleep(1)
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'Referer': None,
        }
        self.session.headers.update(headers)
        self.session.get(self.CookieUrl, timeout=30)
        self.save_cookie()
        return self.session.cookies.get_dict()


if __name__ == "__main__":
    s = DgBaseCls()
    while True:
        if s.get_login_cookie():
            break
        print('登录失败，1S后重新登录')
        sleep(1)

