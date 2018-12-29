#!/usr/bin/env python
# -*- coding:utf-8 -*-

from util.file_util import *
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
import csv

class AccountMgr:
    def __init__(self):
        pass

    @staticmethod
    def get_account_list(file_full_path):
        account_list = []
        with open(file_full_path, 'r', encoding='gbk') as f:
            reader = csv.reader(f)
            for row_index, row in enumerate(reader):
                if row_index != 0:
                    account_list.append(row)
        return account_list

    @staticmethod
    def get_accountant_account():
        cur_env = FileUtil.get_cur_env()
        root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(root_dir + "/config/accountant_account.ini")
        account_info = dict()
        account_info["loginName"] = ini_util.get_item_attr(cur_env, "user")
        account_info["password"] = ini_util.get_item_attr(cur_env, "password")
        return account_info

    @staticmethod
    def get_admin_account():
        cur_env = FileUtil.get_cur_env()
        root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(root_dir + "/config/admin_account.ini")
        account_info = dict()
        account_info["loginName"] = ini_util.get_item_attr(cur_env, "user")
        account_info["password"] = ini_util.get_item_attr(cur_env, "password")
        return account_info

    @staticmethod
    def login(account_info):
        http_util = HttpConnectMgr.get_http_connect()
        host = DomainMgr.get_domain("passport_host")
        response, res_code = http_util.post(host, "/web-passport/user/login/doLogon", account_info)
        return response, res_code

    @staticmethod
    def app_login(account_info):
        http_util = HttpConnectMgr.get_http_connect()
        host = DomainMgr.get_domain("passport_host")
        response, res_code = http_util.post(host, "/web-passport/app/user/login/doLogon", account_info)
        return response, res_code

    @staticmethod
    def logout():
        http_util = HttpConnectMgr.get_http_connect()
        host = DomainMgr.get_domain("passport_host")
        response = http_util.get(host, "/web-passport/user/login/doLogout", None)
        return response