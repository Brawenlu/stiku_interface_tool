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
from service.student_service import StudentService
from service.problem_service import ProblemService
import random
import time


def get_default_mod_profile_params(account):
    student_service = StudentService()
    profile_infos = student_service.get_student_profile_info(account)
    class_infos = student_service.get_class_info(profile_infos[1])
    student_id = student_service.get_student_id(account)
    params = dict()
    params["studentId"] = student_id
    params["cardNum"] = account
    params["name"] = profile_infos[2]
    params["phoneNum"] = profile_infos[4] or ""
    params["className"] = class_infos[2]
    params["classId"] = profile_infos[1]
    params["sex"] = profile_infos[3]
    params["qqNum"] = profile_infos[5] or ""
    params["email"] = ""
    params["schoolId"] = profile_infos[0]
    params["gradeYear"] = class_infos[0]
    params["stype"] = class_infos[1]
    params["contact"] = profile_infos[7] or ""

    return params

if __name__ == "__main__":
    account_info = dict()
    account_info['loginName'] = "jianghao2"
    account_info['password'] = "123456"
    login_res,login_res_code = AccountMgr.login(account_info)
    if re.search("错误报告", login_res):
        print("[%s]login fail,please check you card and password" % "jianghao2")
        exit()
    root_dir = FileUtil.get_app_root_dir()
    account_list = AccountMgr.get_account_list(root_dir+"/coach/modify_profile.csv")
    for info in account_list:
        host = DomainMgr.get_domain("ms_host")
        http_util = HttpConnectMgr.get_http_connect()
        modify_profile_params = get_default_mod_profile_params(info[0])
        if info[2] != "":
            modify_profile_params["name"] = info[2]
        if info[3] != "":
            modify_profile_params["sex"] = int(info[3])
        if info[4] != "":
            modify_profile_params["qqNum"] = info[4]
        if info[5] != "":
            modify_profile_params["contact"] = info[5]
        if info[6] != "":
            modify_profile_params["phoneNum"] = info[6]
        if info[7] != "":
            modify_profile_params["classId"] = int(info[7])
        if info[8] != "":
            modify_profile_params["gradeYear"] = int(info[8])
        if info[9] != "": #1:文科 2:理科
            modify_profile_params["stype"] = int(info[9])
        rsp,rsp_code = http_util.post(host, "/web-ms/stuAccountManage/updateStudentInfo", modify_profile_params)
        if int(rsp) != 1:
            print(rsp)
        time.sleep(0.5)
        print("account=[%s]modify complete" % (info[0]))
    input("press enter to exit")
