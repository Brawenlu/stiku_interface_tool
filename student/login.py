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
    root_dir = FileUtil.get_app_root_dir()
    config_list = AccountMgr.get_account_list(root_dir+"/student/login.csv")
    for config in config_list:
        login_param = dict()
        login_param['loginName'] = config[0]
        login_param['password'] = config[1]
        login_res,res_code = AccountMgr.login(login_param)
        if re.search("错误报告", login_res):
            print("[%s]login fail,please check you card and password" % config[0])
        else:
            print("[%s]login success" % config[0])
