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
from service.sigma_service import SigmaService
from service.common_service import CommonService
from config.common_config import *
import re
import random
import time
import json
from util.log import logger

class StudentPass:
    def __init__(self):
        root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(root_dir + "/config/school_class.ini")
        cur_env = FileUtil.get_cur_env()
        self.http_util = HttpConnectMgr.get_http_connect()
        self.teacher_host = DomainMgr.get_domain("teacher_host")
        self.sigma_student_host = DomainMgr.get_domain("sigma_student_host")
        self.student_service = StudentService()
        self.problem_service = ProblemService()
        self.sigma_service = SigmaService()
        self.token = ""
        self.test_school_id = ini_util.get_item_attr(cur_env, "test_school_id")
        self.test_class_id = ini_util.get_item_attr(cur_env, "test_class_id")
        self.student_id = 0
        self.student_account = ""
        self.student_name = ""
        self.score = 0
        self.class_rank = 0
        self.grade_rank = 0
        self.rand_book_id = 0
        self.rand_book_name = ""
        self.start_chapter_id = 0

    def get_rand_student(self):
        student_list = self.student_service.get_student_list(self.test_school_id, self.test_class_id)
        rand_num = random.randint(0, len(student_list)-1)
        student_info = student_list[rand_num]
        self.student_id = student_info[0]
        self.student_account = student_info[1]
        self.student_name = student_info[2]
        logger.info("%s,%s是被选召的孩子", self.student_account, self.student_name)

    def app_login(self, account):
        login_param = dict()
        login_param['loginName'] = account
        login_param['password'] = "123456"  # 使用了默认的密码 @warning
        login_res, login_code = AccountMgr.app_login(login_param)
        if re.search("错误报告", login_res):
            logger.error("(%s)login fail,please check you card and password" % account)
            return False
        login_res_json = json.loads(login_res)
        self.token = login_res_json["userdata"]["token"]
        self.student_id = login_res_json["userdata"]["serverStudentId"]
        return True