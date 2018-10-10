# version: 1.0
# auth: Zzaniu

from lib.aniusql import Sql
from conf import settings
from lib.mail import error_2_send_email


class SyncSqlGold(object):
    """从线上数据库同步gold_8.1数据库"""

    def __init__(self):
        self.sql_gold = Sql(settings.DATABASES_GOLD_8_1)
        self.__sql_online = Sql(settings.DATABASES_SERVER)  # 双下划綫开头，表示为私有对象，只可被类内访问，不可继承

    def query_online(self, sql, *args):
        return self.__sql_online.raw_sql(sql, *args)

    def run_sync(self):
        self.sync_npts_db()
        self.sync_nems_db()
        self.sync_bwl_db()
        self.sync_special_bwl_db()

    def sync_npts_db(self):
        self.sync_npts_head()
        self.sync_npts_img()
        self.sync_npts_exg()
        self.sync_npts_cm()

    def sync_nems_db(self):
        self.sync_nems_head()
        self.sync_nems_img()
        self.sync_nems_exg()
        self.sync_nems_cm()

    def sync_bwl_db(self):
        self.sync_bwl_head()
        self.sync_bwl_list()

    def sync_special_bwl_db(self):
        self.sync_special_bwl_head()
        self.sync_special_bwl_list()

    def get_distinct_seqno(self, sql, table_name):
        """获取表中所有不重复的SEQNO"""
        ret = []
        sql_str = "SELECT DISTINCT SEQNO from {}".format(table_name)
        results = sql(sql_str)
        if results.get('status'):
            for seqno in results.get('ret_tuples'):
                ret.append(seqno[0])  # 列表的方式就是数据大了这个方式就行不通了，会太耗内存
        return ret

    def take_the_difference_set(self, list_online, list_gold):
        """取线上与GOLD的差集"""
        return list(set(list_online)-set(list_gold))

    def sync_tatm_seq(self, miss_seqno_list, table_name):
        for seqno in miss_seqno_list:
            rets = self.__sql_online.select(table_name, where={'SEQNO': seqno})
            for ret in rets:
                ret.pop('id')
                self.sql_gold.insert(table_name, **ret)

    def get_miss_seqno_list(self, table_name):
        seq_online_list = self.get_distinct_seqno(self.query_online, table_name)
        seq_gold_list = self.get_distinct_seqno(self.sql_gold.raw_sql, table_name)
        return self.take_the_difference_set(seq_online_list, seq_gold_list)

    def sync_npts_head(self):
        miss_seqno_list = self.get_miss_seqno_list('NptsEmlHead')
        self.sync_tatm_seq(miss_seqno_list, 'NptsEmlHead')

    def sync_npts_img(self):
        miss_seqno_list = self.get_miss_seqno_list('NptsEmlImgType')
        self.sync_tatm_seq(miss_seqno_list, 'NptsEmlImgType')
        self.sync_update_tatm_list('NptsEmlImgType', 'GDSSEQNO')

    def sync_npts_exg(self):
        miss_seqno_list = self.get_miss_seqno_list('NptsEmlExgType')
        self.sync_tatm_seq(miss_seqno_list, 'NptsEmlExgType')
        self.sync_update_tatm_list('NptsEmlExgType', 'GDSSEQNO')

    def sync_npts_cm(self):
        miss_seqno_list = self.get_miss_seqno_list('NptsEmlConsumeType')
        self.sync_tatm_seq(miss_seqno_list, 'NptsEmlConsumeType')
        self.sync_update_tatm_list('NptsEmlConsumeType', 'GSEQNO')

    def sync_nems_head(self):
        miss_seqno_list = self.get_miss_seqno_list('NemsHead')
        self.sync_tatm_seq(miss_seqno_list, 'NemsHead')

    def sync_nems_img(self):
        miss_seqno_list = self.get_miss_seqno_list('NemsImgList')
        self.sync_tatm_seq(miss_seqno_list, 'NemsImgList')
        self.sync_update_tatm_list('NemsImgList', 'GDSSEQNO')

    def sync_nems_exg(self):
        miss_seqno_list = self.get_miss_seqno_list('NemsExgList')
        self.sync_tatm_seq(miss_seqno_list, 'NemsExgList')
        self.sync_update_tatm_list('NemsExgList', 'GDSSEQNO')

    def sync_nems_cm(self):
        miss_seqno_list = self.get_miss_seqno_list('NemsCmList')
        self.sync_tatm_seq(miss_seqno_list, 'NemsCmList')
        self.sync_update_tatm_list('NemsCmList', 'GSEQNO')

    def sync_bwl_seqno(self, miss_seqno_list, table_name):
        for seqno in miss_seqno_list:
            rets = self.__sql_online.select(table_name, where={'SeqNo': seqno})
            for ret in rets:
                ret.pop('Id')
                self.sql_gold.insert(table_name, **ret)

    def get_bwl_miss_seqno_list(self, table_name):
        seq_online_list = self.get_distinct_seqno(self.query_online, table_name)
        seq_gold_list = self.get_distinct_seqno(self.sql_gold.raw_sql, table_name)
        return self.take_the_difference_set(seq_online_list, seq_gold_list)

    def sync_bwl_head(self):
        miss_seqno_list = self.get_bwl_miss_seqno_list('BwlHeadType')
        self.sync_bwl_seqno(miss_seqno_list, 'SpecialBwlHeadType')

    def sync_special_bwl_head(self):
        miss_seqno_list = self.get_bwl_miss_seqno_list('SpecialBwlHeadType')
        self.sync_bwl_seqno(miss_seqno_list, 'BwlHeadType')

    def sync_update_2_max(self, table_name, field, seqno):
        local_max_gdsseqno = self.get_local_db_max_or_min_gdsseqno(self.sql_gold, table_name, field, seqno)
        online_max_gdsseqno = self.get_local_db_max_or_min_gdsseqno(self.__sql_online, table_name, field, seqno)
        if local_max_gdsseqno < online_max_gdsseqno:
            rets = self.__sql_online.select(table_name, where={'SeqNo': seqno, '{}__gt'.format(field): local_max_gdsseqno})
            for ret in rets:
                if ret.__contains__('Id'):
                    ret.pop('Id')
                elif ret.__contains__('id'):
                    ret.pop('id')
                else:
                    pass
                self.sql_gold.insert(table_name, **ret)

    def sync_update_2_min(self, table_name, field, seqno):
        local_min_gdsseqno = self.get_local_db_max_or_min_gdsseqno(self.sql_gold, table_name, field, seqno, max=False)
        online_min_gdsseqno = self.get_local_db_max_or_min_gdsseqno(self.__sql_online, table_name, field, seqno, max=False)
        if local_min_gdsseqno > online_min_gdsseqno:
            rets = self.__sql_online.select(table_name, where={'SeqNo': seqno, '{}__lt'.format(field): local_min_gdsseqno})
            for ret in rets:
                if ret.__contains__('Id'):
                    ret.pop('Id')
                elif ret.__contains__('id'):
                    ret.pop('id')
                else:
                    pass
                self.sql_gold.insert(table_name, **ret)\

    @error_2_send_email
    def sync_update_tatm_list(self, table_name, field):
        assert not self.get_miss_seqno_list(table_name), '数据库{}的SeqNo同步未完成'.format(table_name)
        for seqno in self.get_distinct_seqno(self.query_online, table_name):
            self.sync_update_2_max(table_name, field, seqno)
            self.sync_update_2_min(table_name, field, seqno)

    @error_2_send_email
    def sync_update_bwl_list(self, table_name, field):
        assert not self.get_bwl_miss_seqno_list(table_name), '数据库{}的SeqNo同步未完成'.format(table_name)
        for seqno in self.get_distinct_seqno(self.query_online, table_name):
            self.sync_update_2_max(table_name, field, seqno)
            self.sync_update_2_min(table_name, field, seqno)

    def sync_bwl_list(self):
        miss_seqno_list = self.get_bwl_miss_seqno_list('BwlListType')
        self.sync_bwl_seqno(miss_seqno_list, 'BwlListType')
        self.sync_update_bwl_list('BwlListType', 'GdsSeqno')

    def sync_special_bwl_list(self):
        miss_seqno_list = self.get_bwl_miss_seqno_list('SpecialBwlListType')
        self.sync_bwl_seqno(miss_seqno_list, 'SpecialBwlListType')
        self.sync_update_bwl_list('SpecialBwlListType', 'GdsSeqno')

    def get_local_db_max_or_min_gdsseqno(self, sql, tabname, field, seqNo, max=True):
        if max:
            _sql = 'SELECT max({}) as gdsSeqno FROM {} WHERE SEQNO = '.format(field, tabname) + "%s"
        else:
            _sql = 'SELECT min({}) as gdsSeqno FROM {} WHERE SEQNO = '.format(field, tabname) + "%s"
        ret = sql.raw_sql(_sql, seqNo)
        if ret.get('status'):
            gdsSeqno = ret['ret_tuples'][0][0]
            return gdsSeqno


if __name__ == "__main__":
    sql = SyncSqlGold()
    sql.run_sync()
    # ret = sql.sql_gold.raw_sql("SELECT DISTINCT SEQNO from BwlListType")
    # print('ret = ', ret)
