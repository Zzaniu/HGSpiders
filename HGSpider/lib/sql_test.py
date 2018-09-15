import pymysql
from conf import settings

# 连接数据库
conn = pymysql.connect(**settings.DATABASES_GOLD_8_1)  # db：库名
# 创建游标
cur = conn.cursor()
# 查询lcj表中存在的数据
cur.execute("select * from NemsHead")
# fetchall:获取lcj表中所有的数据
ret1 = cur.fetchall()
if cur.description:
    names = [x[0] for x in cur.description]
    print('names = ', names)
print(ret1)
print("----------------------")
# 获取lcj表中前三行数据
ret2 = cur.fetchmany(3)
print(ret2)
print("------------------------------")
# 获取lcj表中第一行数据
ret3 = cur.fetchone()
print(ret3)
# 同时向数据库lcj表中插入多条数据
# ret = cur.executemany("insert into lcj values(%s,%s,%s,%s,%s)", [(41,"xiaoluo41",'man',24,13212344332),
#                                                             (42,"xiaoluo42",'gril',21,13245678948),
#                                                             (43,"xiaoluo43",'gril',22,13245678949),
#                                                                (44,"xiaoluo44",'main',24,13543245648)])
# 提交
conn.commit()
# 关闭指针对象
cur.close()
# 关闭连接对象
conn.close()
