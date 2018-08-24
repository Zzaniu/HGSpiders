#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-08-13 11:53:12
# @Author  : zaniu (Zzaniu@126.com)
# @Version : $Id$
###这里我是采用的单例模式，可以考虑直接用import,因为import也是单例模式###
# 需要安装concurrent_log_handler  pip install concurrent_log_handler
import os
import logging
import logging.config
from conf import settings
import functools


def singleton(func):
    """单例装饰器函数"""
    data = {'obj': None}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if data.get('obj') is None:
            data['obj'] = func(*args, **kwargs)
        return data['obj']

    return wrapper


@singleton
def getSpiderLogger():
    log_conf_path = os.path.join(settings.BASE_DIR, 'conf', 'log.ini')
    logging.config.fileConfig(log_conf_path)
    return logging.getLogger('Spider')
