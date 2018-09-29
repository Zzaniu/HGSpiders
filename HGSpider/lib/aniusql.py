import time
import traceback

import pymysql
import re

from DBUtils.PooledDB import PooledDB

from conf import settings
from lib.log import getSpiderLogger, singleton

log = getSpiderLogger()


# @singleton
class SingletonPoolDB(PooledDB):
    """单例数据库连接池"""
    pass


class Sql(object):
    def __init__(self, databases):
        self.__pool = self.connect_mysql(databases)
        self.conn = self.__pool.connection()
        self.cursor = self.conn.cursor()

    def __del__(self):
        """退出时释放资源"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    @staticmethod
    def connect_mysql(databases):
        """单例模式，会防止创建多个连接池"""
        times = settings.RE_CONNECT_SQL_TIME
        while times > 0:
            d = {
                'mincached': 5,  # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
                'maxcached': 5,  # 链接池中最多闲置的链接，0和None不限制
                'maxshared': 0,
            # 链接池中最多共享的链接数量，0和None表示全部共享。PS: 无用，因为pymysql和MySQLdb等模块的 threadsafety都为1，所有值无论设置为多少，_maxshared永远为0，所以永远是所有链接都共享。
                'maxconnections': 20,  # 连接池允许的最大连接数，0和None表示不限制连接数
                'blocking': True,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
                'maxusage': None,  # 一个链接最多被重复使用的次数，None表示无限制
                'ping': 0,
            }
            try:
                _pool = SingletonPoolDB(pymysql, **d, **databases)
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
            if self.cursor.description:
                names = [x[0] for x in self.cursor.description]
                print('name = ', names)
            self.conn.commit()
            return True
        except:
            log.error('数据库发生错误，错误信息{}'.format(str(traceback.format_exc())))
            self.conn.rollback()
            return False

    def update(self,table_name,where=None,no_where=False, **kwargs):
        """
        :param table_name:
        :param cols:
        :param where:
        :return:
        """
        if not no_where:
            assert where is not None, 'update 操作必须带where条件'
        filter_condition = ""  # 筛选条件
        vals_condition = tuple()
        if where:
            vals_condition = tuple(where.values())
            lens = len(where.items())
            for i, k in enumerate(where):
                if lens == 1:
                    filter_condition += "where {}=%s".format(k)
                else:
                    if i == 0:
                        filter_condition += "where {}=%s".format(k)
                    else:
                        filter_condition += " AND {}=%s".format(k)

        keys, vals = tuple(kwargs.keys()), tuple(kwargs.values())
        cols = ",".join(keys)
        wildcards = ",".join(["{}=%s".format(keys[i]) for i in range(len(vals))])

        sql = 'UPDATE {} SET {} {};'.format(table_name, wildcards, filter_condition)

        #将筛选条件的val加到tuple
        vals=vals+vals_condition
        try:
            ret = self.cursor.execute(sql, args=vals)   # 受影响的行
            self.conn.commit()
            if ret:
                return True
            else:
                return False
        except Exception as e:
            self.conn.rollback()
            log.error("error = {}".format(e))
            return False

    def _select(self):
        pass

    def select(self, table_name, *cols, where=None, limit=None, first=False):
        """
        :param table_name: 表名,str
        :param cols: 列名
        :param where: 筛选条件,暂时只添加一个
        :param limit: 查询行数,int型,None表示查询苏所有
        SELECT * FROM DecMsg where ClientSeqNo="201801100950223990" and DeleteFlag="0"
        :return:
        """
        filter_condition = ""  # 筛选条件,暂时只支持一个查询条件
        vals=tuple()
        if where:
            vals=tuple(where.values())
            for i,k in enumerate(where):
                if len(vals)==1:
                    if k.endswith('__gt'):
                        filter_condition += 'where {}>%s'.format(k[:-4])
                    elif k.endswith('__lt'):
                        filter_condition += 'where {}<%s'.format(k[:-4])
                    else:
                        filter_condition += 'where {}=%s'.format(k)
                else:
                    if i==0:
                        if k.endswith('__gt'):
                            filter_condition += 'where {}>%s'.format(k[:-4])
                        elif k.endswith('__lt'):
                            filter_condition += 'where {}<%s'.format(k[:-4])
                        else:
                            filter_condition += 'where {}=%s'.format(k)
                    else:
                        if k.endswith('__gt'):
                            filter_condition += ' and {}>%s'.format(k[:-4])
                        elif k.endswith('__lt'):
                            filter_condition += ' and {}<%s'.format(k[:-4])
                        else:
                            filter_condition += ' and {}=%s'.format(k)

        if not cols and not limit:  # select * ,无limit
            sql = 'select * from {} {};'.format(table_name,filter_condition)
        elif limit:
            if not cols:  # select * 有limit
                sql = 'select * from {} {} limit {};'.format(table_name,filter_condition, limit)
            else:  # select x1,x2 有limit
                col_names = ",".join(cols)
                sql = 'select {} from {} {} limit {};'.format(col_names, table_name,filter_condition, limit)
        else:
            # no limit,有col值
            col_names = ",".join(cols)
            sql = 'select {} from {} {};'.format(col_names, table_name,filter_condition)

        self.cursor.execute(sql, vals)
        if self.cursor.description:
            names = [x[0] for x in self.cursor.description]

        self.conn.commit()
        if first:
            ret = self.cursor.fetchone()
            if ret:
                return dict(zip(names, ret))
            else:
                return None
        result = self.cursor.fetchall()
        rets = [x for x in result]
        ret_dict = []
        for ret in rets:
            ret_dict.append(dict(zip(names, ret)))
        return ret_dict

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

    def raw_sql(self, _sql, *args):
        """支持原生SQL"""
        ret = {'status': False, 'ret_tuples': ()}
        try:
            lines = self.cursor.execute(_sql, args)
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


if __name__ == "__main__":
    sql = Sql(settings.DATABASES_GOLD_8_1)
    ret = sql.select('Msg', where={'id__gt': 85}, first=True)
    # ret.pop('id')
    # ret = sql.insert('Msg', **ret)
    print("ret = ", ret)
