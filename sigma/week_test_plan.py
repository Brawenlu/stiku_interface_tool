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
from util.interface_mgr import InterfaceMgr
from util.common_fun import CommonFun
from service.student_service import StudentService
from service.problem_service import ProblemService
import re
import random
import time
import json
from util.log import logger


class WeekTestPlan:
    def __init__(self):
        self.root_dir = FileUtil.get_app_root_dir()
        self.http_util = HttpConnectMgr.get_http_connect()
        self.sigma_student_host = DomainMgr.get_domain("sigma_student_host")
        self.student_service = StudentService()
        self.problem_service = ProblemService()
        self.token = ""
        self.student_id = 0
        self.stu_task_id = 0
        self.recommend_problem_data = []
        self.layer_problem_data = []
        self.jd_pic = ("pre_pic0__1478915622049.jpg",
                       "pre_pic0__1478872280482.jpg",
                       "pre_pic0__1478872280482.jpg",
                       "pre_pic0__1478868929053.jpg",
                       "pre_pic0__1478905299026.jpg",
                       "pre_pic0__1478916477597.jpg")

    def vertify_get_recommend_problem(self, interface, res, vertify_param):
        # "获取举一反三 题目数据成功！"
        res_json = json.loads(res)
        if res_json["type"] != "success":
            return Falset
        self.recommend_problem_data = res_json["data"]
        return True

    def vertify_get_layer_problem(self, interface, res, vertify_param):
        # "获取分层作业题目数据成功！"
        res_json = json.loads(res)
        if res_json["type"] != "success":
            return False
        self.layer_problem_data = res_json["data"]
        return True

    def vertify_update_problem(self, interface, res, vertify_param):
        res_json = json.loads(res)
        if res_json["type"] != "success":
            return False
        return True

    def app_login(self, account):
        login_param = dict()
        login_param['loginName'] = account
        login_param['password'] = "123456"  # 使用了默认的密码 @warning
        login_res, login_code = AccountMgr.app_login(login_param)
        login_res_json = json.loads(login_res)
        if login_res_json["type"] == "failure":
            logger.info("account=%s,登录失败，原因：%s", account,login_res_json["message"])
            return False
        self.token = login_res_json["userdata"]["token"]
        self.student_id = login_res_json["userdata"]["serverStudentId"]
        return True

    def week_test_increase_score_plan(self):
        # 举一反三
        get_recommend_problem = InterfaceMgr.get_interface("sigma_student", "get_recommend_problem")
        get_recommend_problem_param = dict()
        get_recommend_problem_param["studentId"] = self.student_id
        get_recommend_problem_param["taskId"] = self.stu_task_id
        get_recommend_problem_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_recommend_problem,
                                        "post", get_recommend_problem_param, "获取举一反三 题目数据成功！"):
            return False

        # 分层作业
        get_layer_problem = InterfaceMgr.get_interface("sigma_student", "get_layer_problem")
        get_layer_problem_param = dict()
        get_layer_problem_param["studentId"] = self.student_id
        get_layer_problem_param["taskId"] = self.stu_task_id
        get_layer_problem_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_layer_problem,
                                        "post", get_layer_problem_param, "获取分层作业题目数据成功！"):
            return False
        return True

    def get_week_test_tasks(self):
        # 获取任务列表
        get_task_list = InterfaceMgr.get_interface("sigma_student", "get_task_list")
        get_task_param = dict()
        get_task_param["studentId"] = self.student_id
        get_task_param["date"] = int(time.time()*1000)
        get_task_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_task_list,
                                        "post", get_task_param, "获取学习任务包任务列表成功！"):
            return False
        return True

    def student_check_report(self):
        # 查看报告
        get_test_report = InterfaceMgr.get_interface("sigma_student", "get_test_report")
        get_test_report_param = dict()
        get_test_report_param["studentId"] = self.student_id
        get_test_report_param["paperType"] = 1
        get_test_report_param["taskId"] = self.stu_task_id
        get_test_report_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_test_report,
                                        "post", get_test_report_param, "获取一周速测的报告数据成功！"):
            return False
        return True

    def get_increase_score_plan(self):
        # 举一反三
        get_recommend_problem = InterfaceMgr.get_interface("sigma_student", "get_recommend_problem")
        get_recommend_problem_param = dict()
        get_recommend_problem_param["studentId"] = self.student_id
        get_recommend_problem_param["taskId"] = self.stu_task_id
        get_recommend_problem_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_recommend_problem,
                                        "post", get_recommend_problem_param, self.vertify_get_recommend_problem):
            return False

        # 分层作业
        get_layer_problem = InterfaceMgr.get_interface("sigma_student", "get_layer_problem")
        get_layer_problem_param = dict()
        get_layer_problem_param["studentId"] = self.student_id
        get_layer_problem_param["taskId"] = self.stu_task_id
        get_layer_problem_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_layer_problem,
                                        "post", get_layer_problem_param, self.vertify_get_layer_problem):
            return False
        return True

    def get_update_problem_param_data(self, problem_list, problem_index):
        problem_data = problem_list[problem_index]

        week_test_problem_data = dict()
        week_test_problem_data["time"] = random.randint(60, 300)
        week_test_problem_data["problemId"] = problem_data["problemId"]
        week_test_problem_data["pkId"] = problem_data["pkId"]
        problem_score = 0
        rand_num = random.randint(0,1)

        # 0:选择 1:填空 2:解答
        problem_type = problem_data["problemType"]
        if problem_type == 0:
            right_answer = problem_data["selectStandardAnswer"]
            if rand_num == 0:
                week_test_problem_data["isChoosed"] = 0
                week_test_problem_data["isGrasp"] = 0
                week_test_problem_data["selectAnswer"] = self.problem_service.get_rand_wrong_answer(right_answer, ("A","B","C","D","E"))
                week_test_problem_data["score"] = 0
                week_test_problem_data["answerPath"] = ""
            else:
                week_test_problem_data["isChoosed"] = 0
                week_test_problem_data["isGrasp"] = 1
                week_test_problem_data["selectAnswer"] = right_answer
                week_test_problem_data["score"] = problem_score
                week_test_problem_data["answerPath"] = ""
        elif problem_type == 1 or problem_type == 2:
            if rand_num == 0:
                week_test_problem_data["isChoosed"] = 0
                week_test_problem_data["isGrasp"] = 0
                week_test_problem_data["selectAnswer"] = self.problem_service.get_rand_wrong_answer(1,(1,0,-1))
                week_test_problem_data["score"] = 0
                week_test_problem_data["answerPath"] = self.jd_pic[random.randint(0,len(self.jd_pic)-1)]
            else:
                week_test_problem_data["isChoosed"] = 0
                week_test_problem_data["isGrasp"] = 1
                week_test_problem_data["selectAnswer"] = 1
                week_test_problem_data["score"] = problem_score
                week_test_problem_data["answerPath"] = self.jd_pic[random.randint(0,len(self.jd_pic)-1)]
        return week_test_problem_data

    def do_increase_score_plan(self):
        # 举一反三
        update_recommend_problem = InterfaceMgr.get_interface("sigma_student", "update_recommend_problem")
        problem_count = len(self.recommend_problem_data)
        for problem_index in range(problem_count):
            if self.recommend_problem_data[problem_index]["isGrasp"] == -1:
                update_recommend_problem_param = dict()
                update_recommend_problem_param["studentId"] = self.student_id
                update_recommend_problem_param["data"] = [self.get_update_problem_param_data(self.recommend_problem_data, problem_index)]
                update_recommend_problem_param["_token_"] = self.token
                if not CommonFun.test_interface(self.sigma_student_host, update_recommend_problem,
                                                "post", update_recommend_problem_param, self.vertify_update_problem):
                    return False
        # 分层作业
        update_layer_problem = InterfaceMgr.get_interface("sigma_student", "update_layer_problem")
        problem_count = len(self.layer_problem_data)
        for problem_index in range(problem_count):
            if self.layer_problem_data[problem_index]["isGrasp"] == -1:
                update_layer_problem_param = dict()
                update_layer_problem_param["studentId"] = self.student_id
                update_layer_problem_param["data"] = [self.get_update_problem_param_data(self.layer_problem_data, problem_index)]
                update_layer_problem_param["_token_"] = self.token
                if not CommonFun.test_interface(self.sigma_student_host, update_layer_problem,
                                                "post", update_layer_problem_param, self.vertify_update_problem):
                    return False

        return True

if __name__ == "__main__":
    week_test_plan = WeekTestPlan()
    account_list = AccountMgr.get_account_list(week_test_plan.root_dir+"/sigma/week_test_by_class.csv")

    for config_info in account_list:
        school_id = week_test_plan.student_service.get_school_id(config_info[0])
        class_id = week_test_plan.student_service.get_class_id(school_id, config_info[1])
        week_test_name = config_info[2]
        teacher_week_test_id = week_test_plan.problem_service.get_week_test_work_id(week_test_name)
        total_count = 0
        feedback_count = 0
        # 遍历各个分数段
        for section_index in range(5):
            # 获取到此分数段的学生列表
            student_list = week_test_plan.student_service.get_student_list_by_section(school_id, class_id, section_index)
            for student_index, student_info in enumerate(student_list):
                result = week_test_plan.app_login(student_info[0])
                total_count += 1
                if result is False:
                    continue
                week_test_plan.stu_task_id = week_test_plan.problem_service.get_stu_week_test_task_id(week_test_plan.student_id,teacher_week_test_id)
                if week_test_plan.stu_task_id is None:
                    logger.error("student=%s,teacher_wt_id=%s,找不到任务id",student_info[0],teacher_week_test_id)
                    continue
                # 获取任务
                if not week_test_plan.get_week_test_tasks():
                    continue
                # 查看报告
                if not week_test_plan.student_check_report():
                    continue
                # 获取举一反三和分层作业题目
                if not week_test_plan.get_increase_score_plan():
                    continue
                # 作答举一反三和分层作业
                if not week_test_plan.do_increase_score_plan():
                    continue
                feedback_count += 1
                logger.info("student=%s,反馈完成",student_info[0])
        logger.info("school=%s,class=%s,week_test=%s,total=%s,feedback=%s",
                    config_info[0],config_info[1],config_info[2],total_count,feedback_count)
