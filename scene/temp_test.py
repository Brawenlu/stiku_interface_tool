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
from util.log import logger

class TempTest:
    def __init__(self):
        root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(root_dir + "/config/teacher_account.ini")
        cur_env = FileUtil.get_cur_env()
        self.http_util = HttpConnectMgr.get_http_connect()
        self.teacher_host = DomainMgr.get_domain("teacher_host")
        self.sigma_student_host = DomainMgr.get_domain("sigma_student_host")
        self.student_service = StudentService()
        self.problem_service = ProblemService()
        self.teacher_account = ini_util.get_item_attr(cur_env, "user")
        self.teacher_password = ini_util.get_item_attr(cur_env, "password")
        self.teacher_id = 0
        self.student_account = ""
        self.student_password = ""
        self.student_id = 0
        self.student_name = ""
        self.teacher_week_test_id = 0
        self.stu_task_id = 0
        self.student_score = 0
        self.school_id = 0
        self.class_id = 0
        self.grade_year = 0
        self.token = ""
        self.paper_name = ""
        self.rand_problem_id = 0
        self.gk_exam_test_data = ""

    def app_login(self, account):
        login_param = dict()
        login_param['loginName'] = account
        login_param['password'] = "123456"  # 使用了默认的密码 @warning
        login_res, login_code = AccountMgr.app_login(login_param)
        login_res_json = json.loads(login_res)
        if login_res_json["type"] == "failure":
            logger.info("account=%s,登录失败，原因：%s", account,login_res_json["message"])
            return False
        login_res_json = json.loads(login_res)
        self.token = login_res_json["userdata"]["token"]
        self.student_id = login_res_json["userdata"]["serverStudentId"]
        return True

    def login(self, account, password):
        login_param = dict()
        login_param['loginName'] = account
        login_param['password'] = password
        login_res, login_code = AccountMgr.login(login_param)
        if re.search("错误报告", login_res):
            logger.error("(%s)login fail,please check you card and password" % account)
            return False
        return True

    def vertify_get_chapter_info(self, interface, response, vertify_param):
        response_json = json.loads(response)
        err_problem_list = response_json["problemListData"]
        logger.info("sum="+str(len(err_problem_list)))
        index = 0
        for err_problem in err_problem_list:
            index += 1
            if err_problem["sequence"] == 2704577:
                logger.info(err_problem)
                break
        #logger.error(response)
        return True

    def vertify_error_problem_pick(self, interface, response, vertify_param):
        response_json = json.loads(response)
        err_problem_list = response_json["problemListData"]
        logger.info("sum="+str(len(err_problem_list)))
        index = 0
        for err_problem in err_problem_list:
            index += 1
            if err_problem["sequence"] == 2414808:
                logger.info("page=%s,did=%s,right=%s,class=%s,all=%s",
                            index,err_problem["didSize"],err_problem["rightSize"],
                            err_problem["classRightRate"],err_problem["allRightRate"])
                break
        logger.error(response)
        return True

    def vertify_gk_2017_index(self, interface, response, vertify_param):
        response_json = json.loads(response)
        subject_type = vertify_param["s_type"]
        if response_json["type"] != "success":
            return False
        evaluateDataList = response_json["data"]["evaluateDataList"]
        if len(evaluateDataList)<=0:
            self.get_exam_test(subject_type)
            if self.do_exam_test():
                return True
            logger.info("evaluateDataList<0")
            return False

        jie_count = 0
        for evaluateDate in evaluateDataList:
            sectionData = evaluateDate["sectionData"]
            if len(sectionData) <= 0:
                logger.info("sectionData<0")
                return False
            jie_count += len(sectionData)
        if subject_type == 1: # 文科
            if jie_count != 63:
                logger.info("jie_count != 63,=%s",jie_count)
                return False
        if subject_type == 2:
            if jie_count != 76:
                logger.info("jie_count != 76,=%s",jie_count)
                return False
        return True

    def vertify_gk_2017_exampaper(self,interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["type"] != "success":
            return False
        self.gk_exam_test_data = response_json["data"]
        return True

    def vertify_common(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["type"] == "success":
            return True
        return False

    def do_exam_test(self):
        gk_2017_update_problem = InterfaceMgr.get_interface("sigma_student","gk_2017_update_problem")
        for problem_info in self.gk_exam_test_data:
            problem_data = dict()
            problem_data["time"] = random.randint(10, 100)
            problem_data["businessProblemId"] = problem_info["businessProblemId"]
            problem_data["resultPathString"] = ""
            if problem_info["problemType"] == 0:
                problem_data["isGrasp"] = 1
                problem_data["selectAnswer"] = problem_info["selectStandardAnswer"]
                problem_data["score"] = problem_info["problemScore"]
            else:
                problem_data["isGrasp"] = 0
                problem_data["selectAnswer"] = "-1"
                problem_data["score"] = 0

            gk_2017_update_problem_param = dict()
            if problem_info["indexNo"] == len(self.gk_exam_test_data):
                gk_2017_update_problem_param["flag"] = 1
            else:
                gk_2017_update_problem_param["flag"] = 0
            gk_2017_update_problem_param["_token_"] = self.token
            gk_2017_update_problem_param["studentId"] = self.student_id
            gk_2017_update_problem_param["data"] = problem_data
            if not CommonFun.test_interface(self.sigma_student_host,gk_2017_update_problem,
                                            "post",gk_2017_update_problem_param,self.vertify_common):
                return False
        return True

    def get_exam_test(self,s_type):
        gk_2017_exampaper = InterfaceMgr.get_interface("sigma_student","gk_2017_exampaper")
        paper_id = 0
        if s_type == 1: # 文科
            paper_id = 14608
        else:
            paper_id = 14511
        gk_2017_exampaper_param = dict()
        gk_2017_exampaper_param["studentId"] = self.student_id
        gk_2017_exampaper_param["_tokem_"] = self.token
        gk_2017_exampaper_param["paperId"] = paper_id
        if CommonFun.test_interface(self.sigma_student_host,gk_2017_exampaper,"post",gk_2017_exampaper_param,
                                    self.vertify_gk_2017_exampaper):
            return False
        return True

    def test_get_chapter_problem_info(self):
        get_chapater_problem_info = InterfaceMgr.get_interface("web_teacher", "get_chapater_problem_info")
        get_chapater_problem_info_param = dict()
        get_chapater_problem_info_param["tbBookId"] = 1
        get_chapater_problem_info_param["tbBookPointId"] = 1
        get_chapater_problem_info_param["subjectType"] = 1
        if not CommonFun.test_interface(self.teacher_host, get_chapater_problem_info, "get", get_chapater_problem_info_param, self.vertify_get_chapter_info):
            return False
        return True

    def get_error_problem_pick(self):
        error_problem_pick = InterfaceMgr.get_interface("web_teacher", "error_problem_pick")
        error_problem_pick_param = dict()
        error_problem_pick_param["modelType"] = 0
        error_problem_pick_param["classId"] = 3461
        error_problem_pick_param["startTime"] = "2016-01-26"
        error_problem_pick_param["endTime"] = "2016-10-26"
        if not CommonFun.test_interface(self.teacher_host, error_problem_pick, "get", error_problem_pick_param,self.vertify_error_problem_pick):
            return False
        return True

    def test_gaokao_2017_1(self,s_type):
        gk_2017_index = InterfaceMgr.get_interface("sigma_student", "gk_2017_index")
        gk_2017_index_param = dict()
        gk_2017_index_param["studentId"] = self.student_id
        gk_2017_index_param["targetType"] = 1
        gk_2017_index_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host,gk_2017_index,
                                        "post",gk_2017_index_param,self.vertify_gk_2017_index,{"s_type":s_type}):
            return False
        return True

    def test_gaokao_2017_2(self,s_type):
        gk_2017_index = InterfaceMgr.get_interface("sigma_student", "gk_2017_index")
        gk_2017_index_param = dict()
        gk_2017_index_param["studentId"] = self.student_id
        gk_2017_index_param["targetType"] = 2
        gk_2017_index_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host,gk_2017_index,
                                        "post",gk_2017_index_param,self.vertify_gk_2017_index,{"s_type":s_type}):
            return False
        return True

    def get_all_student(self):
        student_info_list = self.student_service.get_all_student_info()
        return student_info_list


if __name__ == "__main__":
    temp_test = TempTest()
    # 老师
    """if not temp_test.login(temp_test.teacher_account,temp_test.teacher_password):
        exit("")
    if not temp_test.test_get_chapter_problem_info():
        exit("")"""
    student_list = temp_test.student_service.get_all_grade_3_student_info()
    logger.info("all_student_count:%s",len(student_list))
    for student_info in student_list:
        student_card = student_info[1]
        s_type = student_info[2]
        if not temp_test.app_login(student_card):
            continue
        logger.info("gaokao_1 student=%s",student_card)
        if not temp_test.test_gaokao_2017_1(s_type):
            continue
        logger.info("gaokao_2 student=%s",student_card)
        if not temp_test.test_gaokao_2017_2(s_type):
            continue



