import os
import sys
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path)

from multiprocessing import Process
from hgSpider.bwllistspider import BwlListSpider
from hgSpider.nptsspider import NptsSpider
from hgSpider.nemsspider import NemsSpider


def runBwlSpider():
    bwl_obj = BwlListSpider()
    bwl_obj.update_local_db_info()


def runNptsSpider():
    npts_obj = NptsSpider()
    npts_obj.get_info()


def runNemsSpider():
    nems_obj = NemsSpider()
    nems_obj.get_info()


if __name__ == "__main__":
    t1 = Process(target=runBwlSpider)
    t2 = Process(target=runNptsSpider)
    # t3 = Process(target=runNemsSpider)
    
    threads = [t2]
    
    for i in threads:
        i.start()
    
    for i in threads:
        i.join()
