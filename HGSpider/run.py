import os
import sys
import time

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path)

from multiprocessing import Process
from hgSpider.bwllistspider import BwlListSpider
from hgSpider.special_bwllistspider import SpecialBwlListSpider
from hgSpider.nptsspider import NptsSpider
from hgSpider.nemsspider import NemsSpider
from dgHgspider.dg_nemsspider import DgNemsSpider
from dgHgspider.dg_nptsspider import DgNptsSpider
from lib.sync_sql import SyncSqlGold


def runBwlSpider():
    bwl_obj = BwlListSpider()
    bwl_obj.get_info()


def runSpecialBwlSpider():
    bwl_obj = SpecialBwlListSpider()
    bwl_obj.get_info()


def runNptsSpider():
    npts_obj = NptsSpider()
    npts_obj.get_info()


def runNemsSpider():
    nems_obj = NemsSpider()
    nems_obj.get_info()


def sync_db():
    obj = SyncSqlGold()
    obj.run_sync()


def runDgNemsSpider():
    DgNemsSpider().get_info()


def runDgNptsSpider():
    DgNptsSpider().get_info()


def run_spider():
    t1 = Process(target=runBwlSpider)
    t2 = Process(target=runSpecialBwlSpider)
    t3 = Process(target=runNptsSpider)
    t4 = Process(target=runNemsSpider)
    threads = [t1, t2, t3, t4]
    for i in threads:
        i.start()
        time.sleep(10)

    for i in threads:
        i.join()

    sync_db()  # 同步数据库

    print('深圳程序执行完毕...')


def run_dg_spider():
    runDgNemsSpider()
    runDgNptsSpider()
    print('东莞程序执行完毕...')


def run():
    run_spider()
    run_dg_spider()
    print('程序执行完毕...')


if __name__ == "__main__":
    run_spider()  # 爬取深圳数据
    # run_dg_spider()  # 爬取东莞数据
    # run()  # 爬取所有
