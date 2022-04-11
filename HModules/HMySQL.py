#-*- coding:utf-8 -*-

import time
import json

from HModules import HLog
log = HLog.LOG()

import pymysql

class HSQL(object):
    def __init__(self, data_base: str):
        self.data_base = data_base
        self.con = self.get_sql_connection()
        self.port_table = 'ports'
        self.port_fields = ['id', 'name', 'local']
        self.data_table = 'datas'
        self.data_fields = {
            'dht': ['temperature', 'humidity', 'check_datetime'],
            'light': ['light', 'check_datetime'],
        }

    def get_sql_connection(self):
        con = pymysql.connect(host = 'zinchon.com', port = 336, user = 'zinc', passwd = 'zinchon.cn', db = self.data_base, charset = 'utf8')
        return con

#####################          插入操作          ##########################

    def sql_insert(self, sql: str, save_data: list):
        log.linfo(f"sql_insert sql = {sql} | data = {save_data}")
        try:
            cur = self.con.cursor()
            cur.execute(sql, save_data)
            self.con.commit()
            cur.close()
            return True
        except pymysql.err.OperationalError:
            return False
        except pymysql.err.InterfaceError:
            if cur: cur.close()
            if self.con: self.con.close()
            self.con = self.get_sql_connection()

    def data_save(self, data: dict) -> bool:
        try:
            this_data_fields = ['pid'] + self.data_fields[data['type']]
            save_data = [data[k] for k in this_data_fields[:-1]]
            save_data.append(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        except KeyError:
            log.lerror(f"KeyError - data_save data = {data}")
            return False

        sql = f"insert into `{data['type']}_{self.data_table}`({', '.join(['`' + f + '`' for f in this_data_fields])}) values({', '.join(['%s']*len(this_data_fields))})"
        return self.sql_insert(sql, save_data)

    def dht_save(self, data: dict) -> bool:
        data['type'] = 'dht'
        return self.data_save(data)

    def light_save(self, data: dict) -> bool:
        data['type'] = 'light'
        return self.data_save(data)

    def add_port(self, name: str, local: str):
        save_data = [name, local]

        sql = f"insert into `{self.port_table}`(`name`, `local`) values(%s, %s)"
        return self.sql_insert(sql, save_data)

#####################          查询操作          ##########################

    def sql_select(self, fields: list, sql: str) -> list:
        r"""
        查询数据库并返回一个字典
        Arguments:
        fields -- 请求字段，用于打包查询的数据
        sql -- 查询语句，用于从数据库中查询数据

        Return value / exceptions raised:
        - 返回一个列表，每个数据是一个字典
            - [{key - 字段: value - 数据}, ]
        """
        print(f"sql_select info: sql = [{sql}]")
        try:
            cur = self.con.cursor()
            cur.execute(sql)
            rdata = cur.fetchall()
            cur.close()
            return [dict(zip(fields, d)) for d in rdata]
        except Exception as e:
            print(f"sql_select error: e = {e}")
            return []

    def get_ports(self, query_data: dict = None) -> list:
        r"""
        获取数据库里的节点信息
        Arguments:
        query_data -- 请求数据，默认为 None 是请求所有节点数据
                    - 如果有数据则按照 ['id', 'name', 'local'] 的顺序查询数据，前者的优先级高

        Return value / exceptions raised:
        - 返回一个列表，包含查询到的节点数据
        [
            {
                "id": 1,
                "name": "阿庄",
                "local": "三千宫险断",
            },
        ]
        """
        sql = f"select * from `{self.port_table}`"
        if query_data:
            for k in self.port_fields:
                if k in query_data:
                    sql += f" where `{k}` = {query_data[k]}"
                    break
        data = self.sql_select(self.port_fields, sql)
        return data

    def get_data(self, query_data: dict) -> dict:
        data = dict()
        # 检查数据正确性
        if 'data_type' not in query_data:
            data['state'] = 'error'
            data['error_info']  = "缺少数据类型 (data_type = dht/light)"
            data['error_info'] += "\nLack data of (data_type = dht/light)"
            return data
        if 'pid' in query_data:
            pid = query_data['pid']
        else:
            ports_data = self.get_ports(query_data)
            if len(ports_data) > 1:
                data['state'] = 'error'
                data['error_info']  =  "数据库中存在重复 节点名或地点，请尝试用节点 id 搜索"
                data['error_info'] +=  "\nThere are multiple port_name or port_local in database, please try search by port_id"
                data['error_info'] += f"\n{json.dumps(ports_data)}"
                return data
            pid = ports_data[0]['id']

        # 生成 sql 语句
        fields = ', '.join([f"`{field}`" for field in self.data_fields[query_data['data_type']]])
        sql = f"SELECT {fields} FROM `{query_data['data_type']}_{self.data_table}` WHERE pid = {pid}"
        if 'query_num' in query_data:
            sql += f" ORDER BY id DESC LIMIT {query_data['query_num']}"
        elif 'start_date' in query_data and 'end_date' in query_data:
            sql += f" AND `check_datetime` BETWEEN '{query_data['start_date']}' AND '{query_data['end_date']}'"
            sql = f"""
            SELECT {fields} FROM `{query_data['data_type']}_{self.data_table}` WHERE `id` in (
                SELECT `cid` FROM (
                        SELECT MAX(`id`) as `cid`, DATE_FORMAT(`check_datetime`, '%Y-%m-%d %H') as `cdate`
                        FROM `{query_data['data_type']}_{self.data_table}` WHERE `check_datetime` BETWEEN '{query_data['start_date']}' AND '{query_data['end_date']}' AND `pid` = {pid}
                        GROUP BY `cdate`
                ) as cdid
            )
            """
            sql = f"""
            SELECT {fields} FROM `{query_data['data_type']}_{self.data_table}` WHERE `id` in (
                SELECT `cid` FROM (
                        SELECT MAX(`id`) as `cid`, DATE_FORMAT(`check_datetime`, '%Y-%m-%d %H') as `cdate`
                        FROM `{query_data['data_type']}_{self.data_table}` WHERE `pid` = {pid}
                        GROUP BY `cdate`
                ) as cdid
            )
            """

        # 获取并返回数据
        rdata = self.sql_select(self.data_fields[query_data['data_type']], sql)
        data['data'] = rdata
        data['state'] = 'ok'
        return data

    def __del__(self):
        self.con.close()

if __name__ == '__main__':
    s = HSQL('HGreenhouse')
    # s.add_port('海洋神庙', '西弗纳海底')
    print(s.get_ports())
    # s.dht_save({
    #     'pid': 2,
    #     'temperature': 34.5,
    #     'humidity': 45,
    #     })

