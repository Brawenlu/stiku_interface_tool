#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
import re
import json
from util.file_util import FileUtil
from util.account_mgr import AccountMgr
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
from service.problem_service import ProblemService
from service.student_service import StudentService

def enable_account(account):
    student_service = StudentService()
    student_id = student_service.get_student_id(account)
    http_util = HttpConnectMgr.get_http_connect()
    host = DomainMgr.get_domain("ms_host")
    params = dict()
    params["userId"] = student_id
    http_util.get(host, "/web-ms/auth/user/resetNormal", params)
    print("启用【%s】" % account)
    return True

if __name__ == "__main__":
    account_info = dict()
    account_info['loginName'] = "adminjiang"
    account_info['password'] = "123456"
    login_res,login_res_code = AccountMgr.login(account_info)
    if re.search("错误报告", login_res):
        print("[%s]login fail,please check you card and password" % "adminjiang")
        exit()
    root_dir = FileUtil.get_app_root_dir()
    account_list = AccountMgr.get_account_list(root_dir+"/accountant/enable_account.csv")
    all_feed_count = 0
    for account in account_list:
        if enable_account(account[0]):
            all_feed_count += 1
    print("total =[%s]" % (len(account_list)))
    print("press enter to exit")