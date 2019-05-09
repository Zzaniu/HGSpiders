import json
import os

import requests

from conf import settings
from hgSpider.nemsspider import NemsSpider

if __name__ == "__main__":
    a = NemsSpider()
    n = a.get_local_db_max_or_min_gdsseqno('NemsImgList', '201800000000002529', max=False)
    print('n = ', n)
