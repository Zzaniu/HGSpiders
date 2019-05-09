import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_FILE_PATH = r"d:/test/hgspider"
SZ_BASE_FILE_PATH = os.path.join(BASE_FILE_PATH, 'SZ')
DG_BASE_FILE_PATH = os.path.join(BASE_FILE_PATH, 'DG')
if not os.path.exists(SZ_BASE_FILE_PATH):
    os.makedirs(SZ_BASE_FILE_PATH)
if not os.path.exists(DG_BASE_FILE_PATH):
    os.makedirs(DG_BASE_FILE_PATH)
# log相关配置
IMAGE_DIR = os.path.join(SZ_BASE_FILE_PATH, 'HGCode1.png')
IMAGE_DIR2 = os.path.join(SZ_BASE_FILE_PATH, 'HGCode2.png')
COOKIE_DIR = os.path.join(SZ_BASE_FILE_PATH, 'cookie')
DG_IMAGE_DIR = os.path.join(DG_BASE_FILE_PATH, 'DG_HGCode1.png')
DG_IMAGE_DIR2 = os.path.join(DG_BASE_FILE_PATH, 'DG_HGCode2.png')
DG_COOKIE_DIR = os.path.join(DG_BASE_FILE_PATH, 'dg_cookie')
USERNAME = 'HULIXIA'
DG_USERNAME = 'DGBT010'
PASSWD = os.getenv('HGPASSWD')
DG_PASSWD = os.getenv('DG_HGPASSWD')
INDEX_URL = r'http://app.singlewindow.cn/cas/login'
IMAGE_URL = r'http://app.singlewindow.cn/cas/plat_cas_verifycode_gen?r=0.20726995129430703'
BWLCOOKIE_URL = r'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwlQueryList?sysId=Z8&ngBasePath=http%3A%2F%2Fsz.singlewindow.cn%3A80%2Fdyck%2FswProxy%2Femspubserver%2F'
BWL_QUERY_URL = r'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwl/Z8/bwlQueryList'
BWLREAL_LIST_URL = r'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwl/Z8/bwlGoodsQueryList'
BWLREAL_HEAD_URL = R'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwl/Z8/bwlDetailRequest'
SPECIAL_BWLCOOKIE_URL = r'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwlQueryList?sysId=Z7&ngBasePath=http%3A%2F%2Fsz.singlewindow.cn%3A80%2Fdyck%2FswProxy%2Femspubserver%2F'
SPECIAL_BWL_QUERY_URL = r'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwl/Z7/bwlQueryList'
SPECIAL_BWLREAL_LIST_URL = r'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwl/Z7/bwlGoodsQueryList'
SPECIAL_BWLREAL_HEAD_URL = R'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/bwl/Z7/bwlDetailRequest'
NPTSCOOKIE_URL = r'http://sz.singlewindow.cn:80/dyck/swProxy/nptsserver/sw/ems/npts/queryEml?sysId=B1&amp;ngBasePath=http%3A%2F%2Fsz.singlewindow.cn%3A80%2Fdyck%2FswProxy%2Fnptsserver%2F'
NEMSCOOKIE_URL = r'http://sz.singlewindow.cn/dyck/swProxy/emspubserver/sw/ems/pub/queryCanadianTradeBooks?sysId=95&ngBasePath=http%3A%2F%2Fsz.singlewindow.cn%3A80%2Fdyck%2FswProxy%2Femspubserver%2F'
APP_ID = '11637191'
API_KEY = 'EWGorLT3vvsXzqDaYDomFfgZ'
SECRET_KEY = 'zzAmHT8WAtutsoMfjYsL4jfFON9P0y3z'
OPTIONS = {
    'detect_direction': 'ture',
    'language_type': 'CHN_ENG',
}

pageSize = 50 * 10

SEND_EMAIL = os.environ.get('mailAddr')
EMAIL_PWD = os.environ.get('mailPwd')
RE_CONNECT_SQL_TIME = 10  # 数据库重连次数
RE_CONNECT_SQL_WAIT_TIME = 5  # 重连数据库等待时间，s

SERVER_FLAG = True
DG_SERVER_FLAG = True

if SERVER_FLAG:
    DATABASES = {
        'host': 'gz-cdb-ld4ka6l5.sql.tencentcdb.com',
        'port': 63482,
        'user': 'gmb_bt',
        'password': 'glodtwo!@456',
        'db': 'GMBGTEO',
        'charset': 'utf8',
    }
else:
    DATABASES = {
        'host': '111.230.242.51',
        'port': 3306,
        'user': 'btrProject',
        'password': 'welcome2btr',
        'db': 'goldtwo8.1',
        'charset': 'utf8',
    }

if DG_SERVER_FLAG:
    DG_DATABASES = {
        'host': 'gz-cdb-ld4ka6l5.sql.tencentcdb.com',
        'port': 63482,
        'user': 'gmb_bt',
        'password': 'glodtwo!@456',
        'db': 'GMBGTEODW',
        'charset': 'utf8',
    }
else:
    DG_DATABASES = {
        'host': '111.230.242.51',
        'port': 3306,
        'user': 'btrProject',
        'password': 'welcome2btr',
        'db': 'goldtwo8',
        'charset': 'utf8',
    }

DATABASES_GOLD_8_1 = {
    'host': '111.230.242.51',
    'port': 3306,
    'user': 'btrProject',
    'password': 'welcome2btr',
    'db': 'goldtwo8.1',
    'charset': 'utf8',
}
DG_DATABASES_GOLD_8 = {
    'host': '111.230.242.51',
    'port': 3306,
    'user': 'btrProject',
    'password': 'welcome2btr',
    'db': 'goldtwo8',
    'charset': 'utf8',
}

# 需要爬取手册信息的公司列表
NPTS_COMPANY_LIST = ['4505941398', '4413942257', '4403948573', '4404144768', '4403941347', '440314047B', '4403942742', '4403161Y2E', '440314754B', '4403944047', '4403167958', '4403949175', '4401340041', '440314311B', '4403948450', '4403949023', '4403948617', '44031419GS', '4403962924', '4413947311',
                     '4403947434', '4413947218', '4413947120', '4403046188', '4403941821', '4403046383', '4403941570',
                     '4403163417', '3201943060', '3201943060', '4403931053', '4403046678', '4413946227',
                     '4403046959', '4403046242', '4403946615', '4403046832', '440316647Y', '44031419L0', '4413947161',
                     '440313813Q', '4413331040', '4403046378', '4403944047', '4403945299', '4403941220', '4403046988',
                     '4403942711', '4403947730', '4403161G44', '440314634A', '4403180896', '4403940185', '4403948655',
                     '4403937851', '4403949158', '4403946532', '4403941779', '440314339B', '4413361208', '4403946578',
                     '4403937478', '440314670B', '4453964065', '440314867B', '440304637U', '440304638E']
# 需要爬取帐册信息的公司列表
NEMS_COMPANY_LIST = ['4403046004', '4403942586', '4403046212', '4403940322', '4403140Q0P', '440394199A', '4403140Q7N', '44031499FL', '4403941169', '44031419EE', '4403042210', '440304630E', '4403937764', '4413342015', '4403940084', '44031419DR',
                     '4403945530', '4403968573', '4403943252',
                     '4403948297', '4413940964', '4413341227', '4413341215', '4413341228', '4403046703', '440304604L',
                     '4403949040', "4403949626", '440304631D', '440314726B', '4419946961', '4403945502', '4403145859',
                     '4403937384', '4403948176', '4403949633', '4403942926', '4413342005', '4403137880', '4403046901',
                     '440314709B', '4413948187', '4403946615', '4403949593', '4403046798', '4403140658', '4403046685',
                     '4403046418']
# 物流账册公司列表
BWL_COMPANY_LIST = ['4403W60001', ]

# 特殊监管区域公司列表
SPECIAL_BWL_COMPANY_LIST = ['4403660096', ]


# 账册
DG_NEMS_COMPANY_LIST = ['4413948610', '4120960242', '440304631D', '4403949040', '4403949626', ]
# 手册
DG_NPTS_COMPANY_LIST = ['4403945671', '44031419BX', '4403167958', '4413942814', '4413948427', ]

