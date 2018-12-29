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
from service.student_service import StudentService


def apply_sigma(account):
    student_service = StudentService()
    student_infos = student_service.get_student_profile_info(account)
    student_id = student_infos[11]
    school_id = student_infos[0]
    grade_year = student_infos[12]

    http_util = HttpConnectMgr.get_http_connect()
    host = DomainMgr.get_domain("ms_host")
    params = dict()
    params["studentId"] = student_id
    params["schoolId"] = school_id
    params["gradeYear"] = grade_year
    response,response_code = http_util.post(host, "/web-ms/stuAccountManage/applySigma", params)
    try:
        res_data = json.loads(response)
    except:
        print(res_data)
    print("account=[%s],result=[%s]" % (account, res_data["message"]))
    if res_data["message"] == "报名成功" or res_data["message"] == "已经报名":
        return True
    else:
        return False

if __name__ == "__main__":
    account_info = dict()
    account_info['loginName'] = "jianghao2"
    account_info['password'] = "123456"
    login_res,login_res_code = AccountMgr.login(account_info)
    if re.search("错误报告", login_res):
        print("[%s]login fail,please check you card and password" % "jianghao2")
        exit()
    root_dir = FileUtil.get_app_root_dir()
    account_list = AccountMgr.get_account_list(root_dir+"/coach/apply_sigma.csv")
    all_feed_count = 0
    for account in account_list:
        if apply_sigma(account[0]):
            all_feed_count += 1
    print("total apply=[%s]，succeed=[%s]" % (len(account_list), all_feed_count))
    input("press enter to exit")
    """#t18开头全部开通西格玛
    student_service = StudentService()
    all_feed_count = 0
    t18_students = student_service.get_t18_students()
    for student in t18_students:
        if apply_sigma(student[3]):
            all_feed_count += 1
    print("总报名人数=[%s],成功报名人数=[%s]" % (len(t18_students), all_feed_count))"""
    """student_service = StudentService()
    all_feed_count = 0
    bjcs_students = student_service.get_bjcs_students()
    for student in bjcs_students:
        if apply_sigma(student[3]):
            all_feed_count +=1
    print("总报名人数=[%s],成功报名人数=[%s]" % (len(bjcs_students), all_feed_count))"""
