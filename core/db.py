import re
from urllib.parse import urlparse

import pymysql
from dbutils.pooled_db import PooledDB
from loguru import logger
from pymysql.cursors import DictCursor, Cursor

from fastod.tools import getfv


class Feedback:
    """执行SQL的反馈"""

    def __init__(
        self, cursor: Cursor | DictCursor = None, mode: bool = None, e: Exception = None
    ):
        """
        Args:
            cursor: 默认游标或者字典游标
            mode: 决定result的值，为True则调用fetchall、为False调用fetchone、为None则不调用
            e: 执行SQL时触发的异常
        """
        if e:
            self.ok = False
            self.affect = None
            self.result = None
            self.error = str(e)
            return
        assert cursor, "Cursor is None"
        self.ok = True
        self.affect: int = cursor.rowcount
        self.result: list | dict | tuple = (
            None if mode is None else cursor.fetchall() if mode else cursor.fetchone()
        )
        self.error = None

    def __str__(self):
        args = self.__class__.__name__, self.ok, self.affect, self.result, self.error
        show = "{}(\n\tok={}\n\taffect={}\n\tresult={}\n\terror={}\n)".format(*args)
        return show


class GenSQL:
    """快速生成SQL语句"""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self._select = None
        self._where_conds = []
        self._limit = None

    def select(self, fileds="*"):
        self._select = fileds
        return self

    @staticmethod
    def parse_conds(conds: dict) -> list[str]:
        result = []
        for key, value in conds.items():
            if value is None:
                result.append(f"{key} IS NULL")
            elif isinstance(value, bool):
                tail = "IS NOT NULL" if value is True else "IS NULL"
                result.append(f"{key} {tail}")
            elif isinstance(value, list):
                some = ", ".join([repr(v) for v in value])
                result.append(f"{key} IN ({some})")
            else:
                result.append(f"{key} = {repr(value)}")
        return result

    def where(self, kv: dict = None, **conds):
        """
        构建where部分

        1. 布尔值查询
            where(f1=True, f2=False)\n
            "...WHERE f1 NOT IS NULL and f2 IS NULL"
        2. IN查询
            where(id=[1, 2 ,3])\n
            "...WHERE id IN (1, 2 ,3)"
        3. 常规等值查询
            where(name="Wauo", age=None)\n
            "...WHERE name = 'Wauo' and age IS NULL"
        Args:
            kv: 传入了则覆盖conds
            **conds: 条件
        """
        conds = kv if kv else conds
        self._where_conds = self.parse_conds(conds)
        return self

    def limit(self, n=1):
        self._limit = n
        return self

    def build(self) -> str:
        """返回具体的SQL语句"""
        _select = self._select if self._select is not None else "*"
        _where = " WHERE " + " AND ".join(self._where_conds) if self._where_conds else ""
        _limit = f" LIMIT {self._limit}" if self._limit else ""
        sql = f"SELECT {_select} FROM {self.table_name}{_where}{_limit}"
        return sql

    def to_string(self) -> str:
        return self.build()


class MySQL:
    def __init__(
        self, host=None, port=None, username=None, password=None, db=None, **kwargs
    ):
        """
        连接MySQL数据库

        Args:
            host: 地址
            port: 端口
            username: 用户
            password: 密码
            db: 数据库
            **kwargs: 跟PooledDB参数保持一致
        """
        cfg = dict(
            host=host or "localhost",
            port=port or 3306,
            user=username,
            password=password,
            db=db,
            mincached=1,
            maxcached=20,
            charset="utf8mb4",
            maxconnections=10,
            blocking=True,
        )
        cfg.update(kwargs)
        self._cfg = cfg
        self._pool = PooledDB(pymysql, **self._cfg)

    @classmethod
    def from_url(cls, url: str):
        """
        连接MySQL\n
        地址格式为：mysql://username:password@host:port/db
        """
        result = urlparse(url)
        return cls(
            host=result.hostname,
            port=result.port,
            username=result.username,
            password=result.password,
            db=result.path.strip("/"),
        )

    def __getitem__(self, name: str):
        assert name in self.get_table_names(), f"table <{name}> is not exists"
        from fastod.core.table import Table

        return Table(name, self._pool, self._cfg)

    def pick_table(self, name: str):
        """选择表"""
        return self.__getitem__(name)

    @staticmethod
    def panic(sql, msg):
        """错误日志"""
        sql = re.sub("\s+", " ", sql).strip()
        logger.error(
            """
            sql     {}
            msg     {}
            """.format(
                sql, msg
            )
        )

    def open_connect(self, dict_cursor=False):
        """打开连接"""
        con = self._pool.connection()
        cur = con.cursor(DictCursor) if dict_cursor else con.cursor()
        return cur, con

    def close_connect(self, cur, con):
        """关闭连接"""
        if cur:
            cur.close()
        if con:
            con.close()

    def exe_sql(
        self, sql: str, args=None, query_all=None, to_dict=True, allow_failed=True
    ) -> Feedback:
        """执行SQL"""
        cur, con = None, None
        try:
            cur, con = self.open_connect(to_dict)
            sql = re.sub("\s+", " ", sql).strip()
            args = args or None
            cur.execute(sql.strip(), args=args)
            con.commit()
            return Feedback(cursor=cur, mode=query_all)
        except Exception as e:
            if allow_failed is False:
                raise e
            self.panic(sql, e)
            return Feedback(e=e)
        finally:
            self.close_connect(cur, con)

    def exem_sql(self, sql: str, args=None) -> int:
        """批量执行SQL"""
        cur, con = None, None
        try:
            cur, con = self.open_connect()
            sql = re.sub("\s+", " ", sql).strip()
            args = args or None
            line = cur.executemany(sql, args=args)
            con.commit()
            return line
        except Exception as e:
            self.panic(sql, e)
            return 0
        finally:
            self.close_connect(cur, con)

    def _add_one(
        self, table: str, item: dict, update: str = None, unique: str = None
    ) -> int:
        """
        添加数据

        Args:
            table: 表
            item: 数据
            update: 唯一索引重复时，则触发 ON DUPLICATE KEY UPDATE <update>
            unique: 唯一索引的字段

        Returns:
            已添加的行数
        """
        fields, values = getfv(item)
        new = (
            ""
            if not (update or unique)
            else "ON DUPLICATE KEY UPDATE {}".format(
                update or "{}={}".format(unique, unique)
            )
        )
        sql = "insert into {}({}) value({}) {}".format(table, fields, values, new)
        args = tuple(item.values())
        r = self.exe_sql(sql, args=args)
        return r.affect

    def _add_many(
        self, table: str, items: list, update: str = None, unique: str = None
    ) -> int:
        """
        批量添加数据

        Args:
            table: 表
            items: 多条数据
            update: 唯一索引重复时，则触发 ON DUPLICATE KEY UPDATE <update>
            unique: 唯一索引

        Returns:
            已添加的行数
        """
        fields, values = getfv(items)
        new = (
            ""
            if not (update or unique)
            else "ON DUPLICATE KEY UPDATE {}".format(
                update or "{}={}".format(unique, unique)
            )
        )
        sql = "insert into {}({}) value({}) {}".format(table, fields, values, new)
        args = [tuple(item.values()) for item in items]
        affect = self.exem_sql(sql, args=args)
        return affect

    def get_table_names(self) -> list:
        """获取当前数据库的所有表名称"""
        sql = "show tables"
        r = self.exe_sql(sql, to_dict=False, query_all=True)
        names = [v[0] for v in r.result]
        return names

    def remove_table(self, name: str) -> bool:
        """删除表"""
        sql = "DROP TABLE {}".format(name)
        return self.exe_sql(sql).ok

    def gen_test_table(self, name: str, once=1000, total=10000):
        """生成测试表并补充数据，然后返回这个表格对象"""
        import random
        from faker import Faker

        faker = Faker("zh_cn")
        n = 0

        def create_table():
            """新建测试表"""
            sql = """
                create table {}
                (
                    id          int NOT NULL    AUTO_INCREMENT,
                    name        varchar(20)     DEFAULT NULL,
                    gender      varchar(1)      DEFAULT NULL,
                    age         int(3)          DEFAULT NULL,
                    phone       varchar(11)     DEFAULT NULL,
                    ssn         varchar(18)     DEFAULT NULL,
                    job         varchar(200)    DEFAULT NULL,
                    salary      int(8)          DEFAULT NULL,
                    company     varchar(200)    DEFAULT NULL,
                    address     varchar(200)    DEFAULT NULL,
                    mark        varchar(1)      DEFAULT NULL,
                    primary key (id)
                ) 
                ENGINE=InnoDB    DEFAULT CHARSET=utf8mb4;
            """.format(
                name
            )
            return self.exe_sql(sql).ok

        def make_one():
            """制造一条数据"""
            one = {
                "name": faker.name(),
                "gender": random.choice(["男", "女"]),
                "age": faker.random.randint(18, 60),
                "phone": faker.phone_number(),
                "ssn": faker.ssn(),
                "job": faker.job(),
                "salary": faker.random_number(digits=4),
                "company": faker.company(),
                "address": faker.address(),
                "mark": faker.random_letter(),
            }
            return one

        def todb(target, count):
            """数据进入MySQL"""
            items = [make_one() for _ in range(count)]
            line = self._add_many(target, items, unique="id")
            nonlocal n
            n += line
            logger.success("MySQL，插入{}，累计{}".format(line, n))

        if not create_table():
            raise Exception("表创建失败，可能表已存在")

        if total < once:
            todb(name, total)
            return self.pick_table(name)

        for _ in range(total // once):
            todb(name, once)

        if other := total % once:
            todb(name, other)

        logger.success("新表，{}/{}".format(self._cfg["db"], name))

        return self.pick_table(name)
