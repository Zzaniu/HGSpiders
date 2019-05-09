import time
import traceback

from multiprocessing import Process
import pymysql
import re
from conf import settings
from DBUtils.PooledDB import PooledDB
from lib.log import getSpiderLogger, singleton

log = getSpiderLogger()


class Sql(object):
    """每实例化一次，就获得一次链接，Process 实现了__del__方法，会自动释放连接池"""
    def __init__(self):
        self._pool = self.connect_mysql()
        self.conn = self._pool.connection()
        self.cursor = self.conn.cursor()
        print('id(self._pool) = ', id(self._pool))

    def __del__(self):
        """退出时释放资源"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    @staticmethod
    @singleton
    def connect_mysql():
        """单例模式，防止创建多个连接池"""
        times = settings.RE_CONNECT_SQL_TIME
        while times > 0:
            d = {
                'mincached': 2,  # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
                'maxcached': 5,  # 链接池中最多闲置的链接，0和None不限制
                'maxshared': 0,  # 链接池中最多共享的链接数量，0和None表示全部共享。PS: 无用，因为pymysql和MySQLdb等模块的 threadsafety都为1，所有值无论设置为多少，_maxshared永远为0，所以永远是所有链接都共享。
                'maxconnections': 20,  # 连接池允许的最大连接数，0和None表示不限制连接数
                'blocking': True,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
                'maxusage': None,  # 一个链接最多被重复使用的次数，None表示无限制
                'ping': 0,
            }
            try:
                _pool = PooledDB(pymysql, **d, **settings.DATABASES)
                return _pool
            except:
                log.debug('创建连接池失败，暂停{}S后继续创建'.format(settings.RE_CONNECT_SQL_WAIT_TIME))
                print('创建连接池失败，暂停{}S后继续创建'.format(settings.RE_CONNECT_SQL_WAIT_TIME))
                times -= 1
                time.sleep(settings.RE_CONNECT_SQL_WAIT_TIME)

        log.error('数据库连接失败...')
        raise Exception('数据库连接失败...')

    def insert(self, table_name, **kwargs):
        keys, vals = tuple(kwargs.keys()), tuple(kwargs.values())
        cols = ",".join(keys)
        wildcards = ",".join(["%s" for i in range(len(vals))])
        sql = 'insert into {}({}) VALUES ({});'.format(table_name, cols, wildcards)
        try:
            self.cursor.execute(sql, args=vals)
            self.conn.commit()
            return True
        except:
            log.error('数据库发生错误，错误信息{}'.format(str(traceback.format_exc())))
            self.conn.rollback()
            return False

    def update(self, table_name, where=None, **kwargs):
        """
        :param table_name:
        :param cols:
        :param where:
        :return:
        """
        filter_condition = ""  # 筛选条件
        vals_condition = tuple()
        if where:
            vals_condition = tuple(where.values())
            for k, v in where.items():
                filter_condition += "where {}=%s".format(k)

        keys, vals = tuple(kwargs.keys()), tuple(kwargs.values())
        cols = ",".join(keys)
        wildcards = ",".join(["{}=%s".format(keys[i]) for i in range(len(vals))])

        sql = 'UPDATE {} SET {} {};'.format(table_name, wildcards, filter_condition)
        # 将筛选条件的val加到tuple
        vals = vals + vals_condition
        try:
            ret = self.cursor.execute(sql, args=vals)  # 受影响的行
            self.conn.commit()
            time.sleep(1)
            if ret:
                return True
            else:
                return False
        except Exception as e:
            self.conn.rollback()
            log.error("error = {}".format(e))
            return False

    def select(self, table_name, *cols, where=None, limit=None):
        """
        :param table_name: 表名,str
        :param cols: 列名
        :param where: 筛选条件,暂时只添加一个
        :param limit: 查询行数,int型,None表示查询苏所有
        SELECT * FROM DecMsg where ClientSeqNo="201801100950223990" and DeleteFlag="0"
        :return:
        """
        filter_condition = "where "  # 筛选条件,暂时只支持一个查询条件
        vals = tuple()
        if where:
            vals = tuple(where.values())
            for i, k in enumerate(where):

                if len(vals) == 1:
                    filter_condition += '{}=%s'.format(k)
                else:
                    if i == 0:
                        filter_condition += '{}=%s'.format(k)
                    else:
                        filter_condition += ' and {}=%s'.format(k)

        if not cols and not limit:  # select * ,无limit
            sql = 'select * from {} {};'.format(table_name, filter_condition)
        elif limit:
            if not cols:  # select * 有limit
                sql = 'select * from {} {} limit {};'.format(table_name, filter_condition, limit)
            else:  # select x1,x2 有limit
                col_names = ",".join(cols)
                sql = 'select {} from {} {} limit {};'.format(col_names, table_name, filter_condition, limit)
        else:
            # no limit,有col值
            col_names = ",".join(cols)
            sql = 'select {} from {} {};'.format(col_names, table_name, filter_condition)

        try:
            self.cursor.execute(sql, vals)
            self.conn.commit()
            ret = self.cursor.fetchall()
            return ret
        except:
            self.conn.rollback()

    def all(self, table_name, *cols):
        col_names = ",".join(cols)
        sql = 'select {} from {};'.format(col_names, table_name)
        self.cursor.execute(sql)
        self.conn.commit()
        return self.cursor.fetchall()

    def delete(self, table_name, where=None):
        filter_condition = "where "  # 筛选条件
        vals_condition = tuple()
        if where:
            vals_condition = tuple(where.values())
            for i, k in enumerate(where):
                results = re.match('^(.+?)__(.+?)$', k)
                if 1 == len(vals_condition):
                    if results:
                        if 'gt' == results.group(2):
                            filter_condition += "{}>%s".format(results.group(1))
                        elif 'lt' == results.group(2):
                            filter_condition += "{}<%s".format(results.group(1))
                    else:
                        filter_condition += "{}=%s".format(k)
                else:
                    if 0 == i:
                        if results:
                            if 'gt' == results.group(2):
                                filter_condition += "{}>%s".format(results.group(1))
                            elif 'lt' == results.group(2):
                                filter_condition += "{}<%s".format(results.group(1))
                        else:
                            filter_condition += "{}=%s".format(k)
                    else:
                        if results:
                            if 'gt' == results.group(2):
                                filter_condition += " and {}>%s".format(results.group(1))
                            elif 'lt' == results.group(2):
                                filter_condition += " and {}<%s".format(results.group(1))
                        else:
                            filter_condition += " and {}=%s".format(k)

        sql = 'DELETE FROM {} {};'.format(table_name, filter_condition)

        try:
            self.cursor.execute(sql, args=vals_condition)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            log.error("error = {}".format(e))
            return False

    def raw_sql(self, _sql):
        """支持原生SQL"""
        ret = {'status': False, 'ret_tuples': ()}
        try:
            lines = self.cursor.execute(_sql)
            self.conn.commit()
            if lines:
                ret['status'] = True
                if _sql.lower().startswith('select'):
                    ret['ret_tuples'] = self.cursor.fetchall()
                    log.debug("ret['ret_tuples'] = {}".format(ret['ret_tuples']))
        except Exception as e:
            self.conn.rollback()
            log.error('error = {}'.format(e))

        return ret


def update_hs_gmodels_other():
    """更新商品编码表gmodel其它信息"""
    sql = Sql()
    _sql = 'select id, gmodel from Commodity'
    gmodel_obj = sql.raw_sql(_sql)
    index = 0
    if gmodel_obj.get('status'):
        for obj_list in gmodel_obj.get('ret_tuples'):
            sql.update('Commodity', where={'id': obj_list[0]}, gmodel=obj_list[1] + '其它')
            index += 1
            print('已更新第{}条'.format(index))
    print('更新完成，共更新数据{}条'.format(index))


def functest1():
    sql = Sql()
    ret = sql.select('DecMsg', 'ClientSeqNo', where={'DecId': 50})
    print('in functest1, ret1 = ', ret)
    ret = sql.select('DecMsg', 'ClientSeqNo', where={'DecId': 50})
    print('in functest1, ret2 = ', ret)
    sql.cursor.close()
    time.sleep(10)


def functest2():
    sql = Sql()
    sql.update('DecMsg', where={'DecId': 51}, QpNotes='大爷好')
    ret = sql.select('DecMsg', 'QpNotes', where={'DecId': 51})
    print('in functest2, ret1 = ', ret)
    sql.update('DecMsg', where={'DecId': 51}, QpNotes='大爷常来')
    ret = sql.select('DecMsg', 'QpNotes', where={'DecId': 51})
    print('in functest2, ret2 = ', ret)
    sql.cursor.close()
    time.sleep(10)


if __name__ == "__main__":
    print('大爷')
    #
    # sql = Sql()
    # ret = sql.select('DecMsg', 'ClientSeqNo', where={'DecId': 50})
    # print('in functest1, ret1 = ', ret)
    # ret = sql.select('DecMsg', 'ClientSeqNo', where={'DecId': 50})
    # print('in functest1, ret2 = ', ret)


    # t1 = Process(target=functest1)
    t2 = Process(target=functest2)
    t3 = Process(target=functest2)
    t4 = Process(target=functest2)
    t5 = Process(target=functest2)

    # t_list = [t1, t2, t3, t4, t5]
    t_list = [t2, t3, t4, t5]
    for t in t_list:
        t.start()
    for t in t_list:
        t.join()
    print('程序执行完毕...')


