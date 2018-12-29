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

def get_rand_name():
    first_name = ("赵","钱","孙","李","周","吴","郑","王","冯","陈","褚","魏","蒋","沈","韩","杨")
    last_name = ("云","正","帅","想","尚","飞","单","玉","倩","洋","聪","雷","平","顺","霞","婷","田","合","国","超","明","亚")
    name_count = random.randint(2,3)
    rand_first_name = first_name[random.randint(0, (len(first_name)-1))]
    rand_name = ""
    if name_count == 2:
        rand_last_name = last_name[random.randint(0, (len(last_name)-1))]
        rand_name = rand_first_name + rand_last_name
    else:
        rand_num1 = random.randint(0, (len(last_name)-1))
        temp = [i for i in range(len(last_name))]
        temp.remove(rand_num1)
        rand_num2 = temp[random.randint(0,(len(temp)-1))]
        rand_last_name = last_name[rand_num1] + last_name[rand_num2]
        rand_name = rand_first_name + rand_last_name
    return rand_name

def get_default_mod_profile_params(account):
    student_service = StudentService()
    profile_infos = student_service.get_student_profile_info(account)
    class_infos = student_service.get_class_info(profile_infos[1])
    params = dict()
    params["provinceId"] = ""
    params["cityId"] = ""
    params["countyId"] = ""
    params["schoolId"] = profile_infos[0]
    params["icon"] = ""
    params["sex"] = profile_infos[3]
    params["gradeYear"] = class_infos[0]
    params["classId"] = profile_infos[1]
    params["sType"] = class_infos[1]
    params["scoreSegment"] = ""
    params["qqNum"] = ""
    params["realName"] = profile_infos[2]
    params["telePhone"] = ""
    params["parentName"] = profile_infos[7]
    params["parentPhone"] = ""
    params["email"] = ""
    params["targetScore"] = ""
    params["motto"] = profile_infos[10]
    params["phoneNum"] = profile_infos[4]
    params["studentSection"] = profile_infos[6]
    params["parentTelephone"] = profile_infos[8]
    params["target"] = profile_infos[9]
    params["qqNumber"] = profile_infos[5]
    params["userIcon"] = "/images/header-pic.png"
    return params

if __name__ == "__main__":
    root_dir = FileUtil.get_app_root_dir()
    account_list = AccountMgr.get_account_list(root_dir+"/student/modify_profile.csv")
    for info in account_list:
        account_info = dict()
        account_info["loginName"] = info[0]
        account_info["password"] = info[1]
        login_res,res_code = AccountMgr.login(account_info)
        if re.search("错误报告", login_res):
            print("[%s]login fail,please check you card and password" % info[0])
            continue
        # randname = get_rand_name()
        host = DomainMgr.get_domain("passport_host")
        http_util = HttpConnectMgr.get_http_connect()
        modify_profile_params = get_default_mod_profile_params(info[0])

        if info[2] != "":
            modify_profile_params["realName"] = info[2]
        if info[3] != "":
            modify_profile_params["sex"] = info[3]
        if info[4] != "":
            modify_profile_params["phoneNum"] = info[4]
        if info[5] != "":
            modify_profile_params["qqNumber"] = info[5]
        if info[6] != "":
            modify_profile_params["studentSection"] = int(info[6])-1
        if info[7] != "":
            modify_profile_params["parentName"] = info[7]
        if info[8] != "":
            modify_profile_params["parentTelephone"] = info[8]
        if info[9] != "":
            modify_profile_params["target"] = info[9]
        if info[10] != "":
            modify_profile_params["motto"] = info[10]
        if info[11] != "":
            modify_profile_params["classId"] = info[11]
        if info[12] != "": #1:文科 2:理科
            modify_profile_params["sType"] = info[12]
        print(modify_profile_params )
        http_util.post(host, "/web-passport/priv/info/save", modify_profile_params)
        AccountMgr.logout()
        time.sleep(0.5)
        print("account=[%s]modify complete" % (info[0]))
    input("press enter to exit")
