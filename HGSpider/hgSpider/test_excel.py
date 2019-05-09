import collections

from lib.aniusql import Sql
from conf import settings
import pandas as pd



def to_excel():
    sql = Sql(settings.DATABASES_SERVER)
    dic = collections.OrderedDict()
    a = sql.select('DecList', '*', where={'id': 999}, first=True)
    ret = sql.raw_sql("SELECT * from DecList where GName LIKE '%%集成电路%%'")
    d = pd.DataFrame([pd.Series(i) for i in ret.get('ret_tuples')])
    d.columns = a.keys()
    d.to_excel(r'C:\Financesystem\data\declist.xlsx', index_label='序号')
    print(d)


if __name__ == "__main__":
    to_excel()


