#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-08-13 10:52:48
# @Author  : zaniu (Zzaniu@126.com)
# @Version : $Id$

import os
import re
import json
from lxml import etree
import time
import hashlib
import requests
from aip import AipOcr
from PIL import Image
from conf import settings
from lib.sql import Sql
from lib.mail import error_2_send_email
from lib.log import getSpiderLogger
import multiprocessing

log = getSpiderLogger()


class BaseCls(object):
    def __init__(self, *args, **kwargs):
        self.IndexUrl = settings.INDEX_URL
        self.ImageUrl = settings.IMAGE_URL
        self.CookieUrl = settings.BWLCOOKIE_URL
        self.ImageDir = settings.IMAGE_DIR
        self.ImageDir2 = settings.IMAGE_DIR2
        self.CookieDir = settings.COOKIE_DIR
        self.aipOcr = AipOcr(settings.APP_ID, settings.API_KEY, settings.SECRET_KEY)
        self.session = requests.session()
        self.sql = Sql(settings.DATABASES_SERVER)

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
    def get_login_info(self, headers=None):
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
                "Connection": "keep-alive",
            }
        res = self.session.get(self.IndexUrl, headers=headers, timeout=20)
        content = etree.HTML(res.text)
        lt = content.xpath(r'//*[@id="fm1"]/p[1]/input[1]/@value')[0]
        execution = content.xpath(r'//*[@id="fm1"]/p[1]/input[2]/@value')[0]
        return lt, execution

    @error_2_send_email
    def know_Image(self, headers=None, timeout=20):
        start_time = time.time()
        used_time = 0
        ret = {'value': None, 'error': None}
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
                "Connection": "keep-alive",
            }
        code_count = 0
        while used_time < timeout:
            code_count += 1
            res = self.session.get(self.ImageUrl, headers=headers, timeout=20)
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
            'swy': settings.USERNAME,
            'swm': hashlib.md5(settings.PASSWD.encode('utf8')).hexdigest(),
            'swm2': '',
            'verifyCode': self.know_Image().get('value'),
            'lt': lt,
            '_eventId': 'submit',
            'submit': '登录',
            'execution': execution,
        }
        header = {
            'Host': 'app.singlewindow.cn',
            'Origin': 'http://app.singlewindow.cn',
            'Referer': 'http://app.singlewindow.cn/cas/login?_local_login_flag=1&service=http://app.singlewindow.cn/cas/jump.jsp%3FtoUrl%3DaHR0cDovL2FwcC5zaW5nbGV3aW5kb3cuY24vY2FzL29hdXRoMi4wL2F1dGhvcml6ZT9jbGllbnRfaWQ9MTM2NyZyZXNwb25zZV90eXBlPWNvZGUmcmVkaXJlY3RfdXJpPWh0dHAlM0ElMkYlMkZzei5zaW5nbGV3aW5kb3cuY24lMkZkeWNrJTJGT0F1dGhMb2dpbkNvbnRyb2xsZXI=&localServerUrl=http://sz.singlewindow.cn/dyck&localDeliverParaUrl=/deliver_para.jsp&colorA1=d1e4fb&colorA2=66,%20124,%20193,%200.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Upgrade-Insecure-Requests': '1',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
        }
        self.session.headers.update(header)
        res = self.session.post(self.IndexUrl, data=data, timeout=20)
        if res.text.find("登录成功") > 0:
            log.info('模拟登陆成功！！！')
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
        self.session.get(self.CookieUrl, timeout=20)
        self.save_cookie()
        return self.session.cookies.get_dict()
