#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
from util.file_util import FileUtil
from util.account_mgr import AccountMgr
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
from service.student_service import StudentService
import re

if __name__ == "__main__":
    account_info = AccountMgr.get_admin_account()
    login_res,res_code = AccountMgr.login(account_info)
    if re.search("错误报告", login_res):
        print("[%s]login fail,please check you card and password" % account_info[0])
        exit()
    host = DomainMgr.get_domain("ms_host")
    root_dir = FileUtil.get_app_root_dir()
    http_util = HttpConnectMgr.get_http_connect()
    account_list = AccountMgr.get_account_list(root_dir+"/coach/reset_password.csv")
    student_service = StudentService()
    for account in account_list:
        userId = student_service.get_user_id(account[0])
        reset_res,res_code = http_util.post(host, "/web-ms/auth/user/resetPasswd",
                                   {'userId': userId, 'password': '123456'})
        if re.search("操作成功", reset_res):
            print("[%s]'s password has reset to [123456]" % (account[0]))
        else:
            print("[%s]reset password fail" % (account[0]))
    AccountMgr.logout()
    input("press enter to exit")
