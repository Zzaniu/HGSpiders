import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_FILE_PATH = r"d:/test/hgspider"
# log相关配置
IMAGE_DIR = os.path.join(BASE_FILE_PATH, 'HGCode1.png')
IMAGE_DIR2 = os.path.join(BASE_FILE_PATH, 'HGCode2.png')
COOKIE_DIR = os.path.join(BASE_FILE_PATH, 'cookie')
USERNAME = 'HULIXIA'
PASSWD = os.getenv('HGPASSWD')
INDEX_URL = r'http://app.singlewindow.cn/cas/login'
IMAGE_URL = r'http://app.singlewindow.cn/cas/plat_cas_verifycode_gen?r=0.20726995129430703'
BWLCOOKIE_URL = r'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwlQueryList?sysId=Z8&ngBasePath=http%3A%2F%2Fsz.singlewindow.cn%3A80%2Fdyck%2FswProxy%2Femspubserver%2F'
BWLREAL_URL = r'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwl/Z8/bwlGoodsQueryList'
NPTSCOOKIE_URL = r'http://sz.singlewindow.cn:80/dyck/swProxy/nptsserver/sw/ems/npts/queryEml?sysId=B1&amp;ngBasePath=http%3A%2F%2Fsz.singlewindow.cn%3A80%2Fdyck%2FswProxy%2Fnptsserver%2F'
NEMSCOOKIE_URL = r'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/queryCanadianTradeBooks?sysId=95&ngBasePath=http%3A%2F%2Fsz.singlewindow.cn%3A80%2Fdyck%2FswProxy%2Femspubserver%2F'
APP_ID = '11637191'
API_KEY = 'EWGorLT3vvsXzqDaYDomFfgZ'
SECRET_KEY = 'zzAmHT8WAtutsoMfjYsL4jfFON9P0y3z'
OPTIONS = {
    'detect_direction': 'ture',
    'language_type': 'CHN_ENG',
}

RE_CONNECT_SQL_TIME = 10  # 数据库重连次数
RE_CONNECT_SQL_WAIT_TIME = 5  # 重连数据库等待时间，s
SERVER = 0
GOLD_8_1 = 1
if SERVER:
    DATABASES = {
        'host': 'gz-cdb-ld4ka6l5.sql.tencentcdb.com',
        'port': 63482,
        'user': 'gmb_bt',
        'password': 'gmbglod!@456',
        'db': 'GMBGTEO',
        'charset': 'utf8',
    }
elif GOLD_8_1:
    DATABASES = {
        'host': '111.230.242.51',
        'port': 3306,
        'user': 'btrProject',
        'password': 'welcome2btr',
        'db': 'goldtwo8.1',
        'charset': 'utf8',
    }
else:
    DATABASES = {
        'host': '111.230.242.51',
        'port': 3306,
        'user': 'btrProject',
        'password': 'welcome2btr',
        'db': 'gmb3',
        'charset': 'utf8',
    }

# 需要爬取手册信息的公司列表
NPTS_COMPANY_LIST = ['4403947730', '4403161G44', '440314634A', '4403180896', '4403940185', '4403948655', '4403937851',
                     '4403946532', '4403941779', '440314339B', '4413361208',]

# 需要爬取帐册信息的公司列表
NEMS_COMPANY_LIST = ['4403945502', '4403145859', '4403937384', '4403948176', '4403949633', '4403942926', '4413342005',
                     '4403137880', '4403046901', '4403949040', '440314709B', '440314709B']
