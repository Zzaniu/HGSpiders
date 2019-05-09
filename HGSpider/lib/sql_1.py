import time
import traceback

import pymysql
import re
from conf import settings
from lib.log import getSpiderLogger

log = getSpiderLogger()


class Sql(object):
    def __init__(self):
        self.conn, self.cursor = self.connect_mysql()

    def __del__(self):
        """退出时关闭与数据库的连接"""
        self.cursor.close()
        self.conn.close()

    @staticmethod
    def connect_mysql():
        while True:
            try:
                conn = pymysql.connect(**settings.DATABASES)
                cursor = conn.cursor()
                break
            except:
                settings.RE_CONNECT_SQL_TIME -= 1
                time.sleep(settings.RE_CONNECT_SQL_WAIT_TIME)
                if settings.RE_CONNECT_SQL_TIME < 0:
                    log.error('数据库连接失败...')
                    raise Exception('数据库连接失败...')
                continue
        return conn, cursor

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

    def update(self,table_name,where=None, **kwargs):
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
        vals=tuple()
        if where:
            vals=tuple(where.values())
            for i,k in enumerate(where):

                if len(vals)==1:
                    filter_condition += '{}=%s'.format(k)
                else:
                    if i==0:
                        filter_condition+='{}=%s'.format(k)
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
        self.conn.commit()
        ret = self.cursor.fetchall()
        return ret

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


def functest2(tabsname, where, **kwargs):
    sql = Sql()
    return sql.update(tabsname, where, **kwargs)


if __name__ == "__main__":
    # update_hs_gmodels_other()
    print('大爷')
    if functest2('DecMsg', where={'DecId': 50,}, QpNotes='大爷'):
        print('大爷好')
    else:
        print('大爷慢走')