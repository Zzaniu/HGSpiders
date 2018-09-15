import os
import sys
import time

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path)

from multiprocessing import Process
from hgSpider.bwllistspider import BwlListSpider
from hgSpider.nptsspider import NptsSpider
from hgSpider.nemsspider import NemsSpider
from lib.sync_sql import SyncSqlGold


def runBwlSpider():
    bwl_obj = BwlListSpider()
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


if __name__ == "__main__":
    t1 = Process(target=runBwlSpider)
    t2 = Process(target=runNptsSpider)
    t3 = Process(target=runNemsSpider)
    threads = [t1, t2, t3]
    threads = [t1]
    for i in threads:
        i.start()
        time.sleep(10)

    for i in threads:
        i.join()

    sync_db()  # 同步数据库

    print('程序执行完毕...')