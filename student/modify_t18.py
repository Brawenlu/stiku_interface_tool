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

def reset_password(t18_students):
    account_info = AccountMgr.get_admin_account()
    login_res = AccountMgr.login(account_info)
    if re.search("错误报告", login_res):
        print("登录失败，请检查配置的用户名和密码,"+account_info[0])
        exit()
    host = DomainMgr.get_domain("ms_host")
    root_dir = FileUtil.get_app_root_dir()
    http_util = HttpConnectMgr.get_http_connect()
    student_service = StudentService()
    for index, student_info in enumerate(t18_students):
        if index%100 == 0 and index !=0:
            num = (int(index/100))*100
            print("has reset "+ str(num) +" 个")
        userId = student_service.get_user_id(student_info[3])
        reset_res = http_util.post(host, "/web-ms/auth/user/resetPasswd",
                                   {'userId': userId, 'password': '123456'})
        if re.search("操作成功", reset_res):
            pass    # print("[%s]已将密码重置为[123456]" % (student_info[3]))
        else:
            print("[%s]重置密码失败,检查配置账号或者配置的管理员是否有权限" % (student_info[3]))
    AccountMgr.logout()

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

def get_rand_name():
    first_name = ("赵","钱","孙","李","周","吴","郑","王",
                  "冯","陈","褚","魏","蒋","沈","韩","杨",
                  "朱","秦","尤","许","何","吕","施","张",
                  "孔","曹","严","华","金","魏","陶","姜",
                  "戚","谢","邹","喻","柏","水","窦","章",
                  "云","苏","潘","葛","奚","范","彭","郎",
                  "鲁","韦","昌","马","苗","凤","花","方",
                  "俞","任","袁","柳","酆","鲍","史","唐",
                  "费","廉","岑","薛","雷","贺","倪","汤",
                  "滕","殷","罗","毕","郝","邬","安","常",
                  "乐","于","时","傅","皮","卞","齐","康",
                  "伍","余","元","卜","顾","孟","平","黄",
                  "和","穆","萧","尹","姚","邵","湛","汪",)
    last_name = ("云","正","帅","想","尚","飞","单","玉","倩","洋","聪","雷","平","顺",
                 "霞","婷","田","合","国","超","明","亚",
                 "洛","璟","煜","芮","睿","晨","熠","悟","莹","颖","语","烜","瑄","萱",
                 "轩","珸","羽","璇","允","芸","沺","苒","阳","煦","珊","灿","耀","烨",
                 "诺","玥","悦","跃","峥","知","智","旭","珝","珬","珂","姁","琬","妧",
                 "炎","妍","珚","彦","琰","婷","琅","朗","卓","琢","凡","思","宇","郁",)
    name_count = random.randint(2,3)
    rand_first_name = first_name[random.randint(0,(len(first_name)-1))]
    rand_name = ""
    if name_count == 2:
        rand_last_name = last_name[random.randint(0,(len(last_name)-1))]
        rand_name = rand_first_name + rand_last_name
    else:
        rand_num1 = random.randint(0,(len(last_name)-1))
        temp = [i for i in range(len(last_name))]
        temp.remove(rand_num1)
        rand_num2 = temp[random.randint(0,(len(temp)-1))]
        rand_last_name = last_name[rand_num1] + last_name[rand_num2]
        rand_name = rand_first_name + rand_last_name
    return rand_name

if __name__ == "__main__":
    student_service = StudentService()
    t18_students = student_service.get_t18_students()
    t18_classes = student_service.get_t18_classes()
    # reset_password(t18_students)
    total_num = 0
    for index,account in enumerate(t18_students):
        class_index = int(index/50)
        t18_target_class_id = t18_classes[class_index][0]
        t18_target_class_grade_year = t18_classes[class_index][3]
        t18_target_class_type = t18_classes[class_index][5]
        if index%50 == 0:
            print("dealing class id=[%d],grade_year=[%d]" % (t18_target_class_id,t18_target_class_grade_year))
        account_info = dict()
        account_info["loginName"] = account[3]
        account_info["password"] = "123456"
        login_res = AccountMgr.login(account_info)
        if re.search("错误报告", login_res):
            print("[%s]login fail,please check you card and password" % account[0])
            continue
        host = DomainMgr.get_domain("passport_host")
        http_util = HttpConnectMgr.get_http_connect()

        params = dict()
        params["provinceId"] = 43
        params["cityId"] = 4301
        params["countyId"] = 430102
        params["schoolId"] = 685
        params["icon"] = ""
        params["sex"] = 1
        params["gradeYear"] = t18_target_class_grade_year
        params["classId"] = t18_target_class_id
        params["sType"] = t18_target_class_type
        params["scoreSegment"] = ""
        params["qqNum"] = ""
        params["realName"] = get_rand_name()
        params["telePhone"] = ""
        params["parentName"] = get_rand_name()
        params["parentPhone"] = ""
        params["email"] = ""
        params["targetScore"] = ""
        params["motto"] = "天道酬勤"
        params["phoneNum"] = (18232787425 + index*2)
        params["studentSection"] = 2
        params["parentTelephone"] = (18569451356 + index*2)
        params["target"] = 100
        params["qqNumber"] = (1253563252 + index)
        params["userIcon"] = "/images/header-pic.png"

        """mod_res = http_util.post(host, "/web-passport/priv/info/save", params)
        if re.search("错误报告", mod_res):
            print("modify fail,"+account[0])
            continue"""
        total_num += 1
        AccountMgr.logout()
        time.sleep(0.5)
    print("success num ="+str(total_num))
    input("press enter to exit")