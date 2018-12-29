#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
import re
from util.account_mgr import AccountMgr
from util.file_util import FileUtil
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr

if __name__ == "__main__":
    root_dir = FileUtil.get_app_root_dir()
    account_list = AccountMgr.get_account_list(root_dir+"/student/modify_password.csv")
    for account in account_list:
        account_info = dict()
        account_info["loginName"] = account[0]
        account_info["password"] = account[1]
        login_res,res_code = AccountMgr.login(account_info)
        if re.search("错误报告", login_res):
            print("[%s]login fail,please check you card and password" % account[0])
            continue
        host = DomainMgr.get_domain("passport_host")
        http_util = HttpConnectMgr.get_http_connect()
        mod_pass_params = dict()
        mod_pass_params["oldpwd"] = account[1]
        mod_pass_params["password"] = account[2]
        mod_pass_params["retype"] = account[2]
        response,res_code = http_util.post(host, "/web-passport/user/pwd/reset", mod_pass_params)
        if not re.search("恭喜您，修改密码成功", response):
            print("modify password fail")
        else:
            print("modify password succeed")
        AccountMgr.logout()
    input("press enter to exit")