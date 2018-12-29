#!/usr/bin/env python
# -*- coding:utf-8 -*-
import pymysql
from util.file_util import IniUtil
import platform


class MysqlUtil:
    def __init__(self):
        self.cur_env = ""
        self.conn = None

    def connect_ignore_env(self, key, db_ini_config):
        ini_util = IniUtil(db_ini_config)
        ip = ini_util.get_item_attr(key, "ip")
        if platform.system() == "Linux":
            ip = ini_util.get_item_attr(key, "direct_ip")
        port = ini_util.get_item_attr(key, "port")
        user = ini_util.get_item_attr(key, "user")
        password = ini_util.get_item_attr(key, "password")
        db = ini_util.get_item_attr(key, "db")
        self.conn = pymysql.connect(host=ip, user=user, passwd=password, db=db, port=int(port), charset="utf8")
        return self.conn

    def connect(self, cur_env, db_ini_config):
        ini_util = IniUtil(db_ini_config)
        ip = ini_util.get_item_attr(cur_env, "ip")
        if platform.system() == "Linux":
            ip = ini_util.get_item_attr(cur_env, "direct_ip")
        port = ini_util.get_item_attr(cur_env, "port")
        user = ini_util.get_item_attr(cur_env, "user")
        password = ini_util.get_item_attr(cur_env, "password")
        db = ini_util.get_item_attr(cur_env, "db")
        self.conn = pymysql.connect(host=ip, user=user, passwd=password, db=db, port=int(port), charset="utf8")
        return self.conn

    def close(self):
        if self.conn is not None:
            self.conn.close()