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

def apply_sigma(account):
    student_service = StudentService()
    student_id = student_service.get_student_id(account)
    school_id = student_service.get_student_school_id(account)
    grade_year = student_service.get_student_grade_year(account)
    http_util = HttpConnectMgr.get_http_connect()
    host = DomainMgr.get_domain("ms_host")
    params = dict()
    params["studentId"] = student_id
    params["schoolId"] = school_id
    params["gradeYear"] = grade_year
    response,res_code = http_util.post(host, "/web-ms/stuAccountManage/applySigma", params)
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
    root_dir = FileUtil.get_app_root_dir()
    account_list = AccountMgr.get_account_list(root_dir+"/coach/apply_sigma_by_class.csv")
    student_service = StudentService()
    account_info = dict()
    account_info['loginName'] = "jianghao2"
    account_info['password'] = "123456"
    login_res,res_code = AccountMgr.login(account_info)
    if re.search("错误报告", login_res):
        print("[%s]login fail,please check you card and password" % "jianghao2")
        exit()
    for config_info in account_list:
        school_id = student_service.get_school_id(config_info[0])
        class_id = student_service.get_class_id(school_id, config_info[1])
        student_list = student_service.get_student_list(school_id, class_id)
        all_feed_count = 0
        for student_info in student_list:
            student_id, student_card, student_name,student_section = student_info[0],student_info[1],student_info[2],student_info[3]

            if apply_sigma(student_card):
                all_feed_count += 1
        print("school=[%s],class=[%s],total apply=[%s]，succeed=[%s]" %
              (config_info[0],config_info[1],len(student_list), all_feed_count))
    input("press enter to exit")
