#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
from util.file_util import FileUtil
from util.account_mgr import AccountMgr
from util.file_util import IniUtil
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
from util.interface_mgr import InterfaceMgr
from util.week_test_util import WeekTestUtil
from util.common_fun import CommonFun
from service.student_service import StudentService
from service.problem_service import ProblemService
from service.common_service import CommonService
import re
import random
import time
import json
import copy
from util.log import logger

PROBLEM_NUM = 10
TARGET = "自动化测试寄语"

class TeacherCommonTestProcess:
    def __init__(self):
        root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(root_dir + "/config/teacher_account.ini")
        cur_env = FileUtil.get_cur_env()
        self.http_util = HttpConnectMgr.get_http_connect()
        self.teacher_host = DomainMgr.get_domain("teacher_host")
        self.student_host = DomainMgr.get_domain("student_host")
        self.sigma_student_host = DomainMgr.get_domain("sigma_student_host")
        self.student_service = StudentService()
        self.problem_service = ProblemService()
        self.teacher_account = ini_util.get_item_attr(cur_env, "user")
        self.teacher_password = ini_util.get_item_attr(cur_env, "password")

    def login(self, account, password):
        login_param = dict()
        login_param['loginName'] = account
        login_param['password'] = password
        login_res, login_code = AccountMgr.login(login_param)
        if re.search("错误报告", login_res):
            logger.error("(%s)login fail,please check you card and password" % account)
            return False
        return True

    def get_class_info(self, teacher_account):
        common_service = CommonService()
        self.teacher_id = common_service.get_teacher_id_by_account(teacher_account)
        self.school_id = common_service.get_school_id_by_teacher_id(self.teacher_id)
        tbt_class_info = common_service.get_teacher_teaching_classes(self.teacher_id)
        self.class_id = tbt_class_info[0][0]
        class_info = self.student_service.get_class_info(self.class_id)
        self.grade_year = class_info[0][0]
        self.subject_type = class_info[0][1]
        self.class_name = class_info[0][2]

    def vertify_common(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["success"] is True:
            return True
        return False

    # 分组管理
    def group_manage(self):
        # 查看分组
        student_section_view = InterfaceMgr.get_interface("web_teacher", "student_section_view")
        if not CommonFun.test_interface(self.teacher_host, student_section_view, "get", None, "调整分数段"):
            return False

        # 保存分组结果
        student_list = self.student_service.get_student_list_by_section(self.school_id, self.class_id, random.randint(0, 4))
        rand_student_info = student_list[random.randint(0, len(student_list)-1)]
        rand_student_id = rand_student_info[2]
        rand_student_name = rand_student_info[0]
        rand_student_section = rand_student_info[3]
        if rand_student_section is None:
            rand_student_section = 2
        save_student_section_change = InterfaceMgr.get_interface("web_teacher", "save_student_section_change")
        student_info_array = list()
        student_info_array.append(str(rand_student_id)+"%"+rand_student_name)
        data_obj_str_param = dict()
        data_obj_str_param["studentInfoArray"] = student_info_array
        data_obj_str_param["scoreSection"] = rand_student_section
        save_student_section_change_param = dict()
        save_student_section_change_param["dataObjStr"] = data_obj_str_param
        if not CommonFun.test_interface(self.teacher_host, save_student_section_change, "post",
                                        save_student_section_change_param, self.vertify_common):
            return False
        return True

    # 分组教学建议
    def group_teaching_suggest(self):
        get_school_exam_paper_list = InterfaceMgr.get_interface("web_teacher", "get_school_exam_paper_list")
        get_school_exam_paper_list_param = dict()

if __name__ == "__main__":
    common_test_process = TeacherCommonTestProcess()
    # 老师
    if not common_test_process.login(common_test_process.teacher_account, common_test_process.teacher_password):
        exit("")
    if not common_test_process.get_class_info(common_test_process.teacher_account):
        exit("")