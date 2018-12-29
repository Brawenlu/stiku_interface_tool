#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
from util.file_util import FileUtil
from util.account_mgr import AccountMgr
from util.mysql_util import MysqlUtil
from util.common_fun import CommonFun
from util.file_util import IniUtil
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
from util.week_test_util import WeekTestUtil
from service.problem_service import ProblemService
from service.student_service import StudentService
from util.interface_mgr import InterfaceMgr
import re
import time
import random
import codecs
import json
from util.log import logger

class WeekTestByClass:
    def __init__(self):
        self.root_dir = FileUtil.get_app_root_dir()
        self.http_util = HttpConnectMgr.get_http_connect()
        self.teacher_host = DomainMgr.get_domain("teacher_host")
        self.sigma_student_host = DomainMgr.get_domain("sigma_student_host")
        self.student_service = StudentService()
        self.problem_service = ProblemService()
        self.student_score = 0
        self.school_id = 0
        self.class_id = 0
        self.student_id = 0
        self.token = ""
        self.paper_name = ""
        self.stu_task_id = 0
        self.problem_count = 0
        self.task_status = 0
        self.week_test_problems = []
        self.jd_pic = ("pre_pic0__1478915622049.jpg",
                       "pre_pic0__1478872280482.jpg",
                       "pre_pic0__1478872280482.jpg",
                       "pre_pic0__1478868929053.jpg",
                       "pre_pic0__1478905299026.jpg",
                       "pre_pic0__1478916477597.jpg")

    def vertify_get_task_list(self, interface, res, vertify_param):
        # "获取学习任务包任务列表成功！"
        res_json = json.loads(res)
        if res_json["type"] != "success":
            return False
        task_list_data = res_json["data"]
        change = False
        for task_data in task_list_data:
            if task_data["paperType"] == 1:# 周测
                vertify_paper_name = "周测卷："+vertify_param["paper_name"]
            else:
                vertify_paper_name = "章测卷："+vertify_param["paper_name"]
            if task_data["name"] == vertify_paper_name:
                self.stu_task_id = task_data["taskId"]
                self.problem_count = task_data["problemCount"]
                self.task_status = task_data["status"]
                change = True
                break
        return change

    def vertify_get_stu_week_test_problem(self, interface, res, vertify_param):
        res_json = json.loads(res)
        if res_json["type"] != "success":
            return False
        self.week_test_problems = res_json["data"]
        return True

    def vertify_update_problem_data(self, interface, res, vertify_param):
        res_json = json.loads(res)
        if res_json["type"] != "success":
            return False
        return True

    def vertify_common(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["type"] == "success":
            return True
        return False

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

    def get_week_test_task(self, paper_name):
        # 获取任务列表
        get_task_list = InterfaceMgr.get_interface("sigma_student", "get_task_list")
        get_task_param = dict()
        get_task_param["studentId"] = self.student_id
        get_task_param["date"] = int(time.time()*1000)
        get_task_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_task_list,
                                        "post", get_task_param, self.vertify_get_task_list, {"paper_name": paper_name}):
            return False
        return True

    def get_student_week_test_problem(self):
        get_stu_week_test_problem = InterfaceMgr.get_interface("sigma_student", "get_stu_week_test_problem")
        get_stu_week_test_problem_param = dict()
        get_stu_week_test_problem_param["studentId"] = self.student_id
        get_stu_week_test_problem_param["taskId"] = self.stu_task_id
        get_stu_week_test_problem_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_stu_week_test_problem,
                                        "post", get_stu_week_test_problem_param, self.vertify_get_stu_week_test_problem):
            return False
        return True

    def get_update_problem_param_data(self, problem_list, answer_strategy, problem_index, student_level):
        problem_data = problem_list[problem_index]

        week_test_problem_data = dict()
        week_test_problem_data["time"] = random.randint(60, 300)
        week_test_problem_data["problemId"] = problem_data["problemId"]
        week_test_problem_data["pkId"] = problem_data["pkId"]
        problem_score = problem_data["problemScore"]
        week_test_problem_data["isChoosed"] = problem_data["isChoosed"]

        rand_num = answer_strategy

        # 0:选择 1:填空 2:解答
        problem_type = problem_data["problemType"]
        if problem_type == 0:
            right_answer = problem_data["selectStandardAnswer"]
            if rand_num == 0:
                week_test_problem_data["isGrasp"] = 0
                week_test_problem_data["selectAnswer"] = self.problem_service.get_rand_wrong_answer(right_answer, ("A","B","C","D"))
                week_test_problem_data["score"] = 0
                week_test_problem_data["answerPath"] = ""
            else:
                week_test_problem_data["isGrasp"] = 1
                week_test_problem_data["selectAnswer"] = right_answer
                week_test_problem_data["score"] = problem_score
                week_test_problem_data["answerPath"] = ""
        elif problem_type == 1: # 填空
            if rand_num == 0:
                week_test_problem_data["isGrasp"] = 0
                week_test_problem_data["selectAnswer"] = self.problem_service.get_rand_wrong_answer(1,(1,0,-1))
                week_test_problem_data["score"] = 0
                week_test_problem_data["answerPath"] = self.jd_pic[random.randint(0,len(self.jd_pic)-1)]
            else:
                week_test_problem_data["isGrasp"] = 1
                week_test_problem_data["selectAnswer"] = 1
                week_test_problem_data["score"] = problem_score
                week_test_problem_data["answerPath"] = self.jd_pic[random.randint(0,len(self.jd_pic)-1)]
        else: # 解答
            ini_util = IniUtil(self.root_dir + "/student/feedback_strategy.ini")
            level = "level_"+str(student_level)
            jd_high_score_rate = float(ini_util.get_item_attr(level, "jd_high_score_rate"))
            jd_low_score_rate = float(ini_util.get_item_attr(level, "jd_low_score_rate"))
            week_test_problem_data["selectAnswer"] = 1
            week_test_problem_data["answerPath"] = self.jd_pic[random.randint(0,len(self.jd_pic)-1)]
            if rand_num == 1:
                week_test_problem_data["isGrasp"] = 1
                week_test_problem_data["score"] = random.randint(int(problem_score * jd_low_score_rate), int(problem_score * jd_high_score_rate))
            else:
                week_test_problem_data["isGrasp"] = 0
                week_test_problem_data["score"] = random.randint(0, int(problem_score * jd_low_score_rate))
        return week_test_problem_data

    def get_xz_count(self):
        xz_count = 0
        for problem_data in self.week_test_problems:
            if problem_data["problemType"] == 0:
                xz_count += 1
        return xz_count

    def get_ready_choose_list(self):
        ready_choose_list = list()
        first_index = 0
        for problem_index in range(len(self.week_test_problems)):
            problem_data = self.week_test_problems[problem_index]
            if problem_data["firstIndex"] != -1 and problem_data["firstIndex"] != first_index:
                first_index = problem_data["firstIndex"]
                temp_problem_list = list()
                temp_choose = dict()
                for temp_index in range(first_index, first_index+problem_data["allCount"]):
                    temp_problem_data = self.week_test_problems[temp_index-1]
                    temp_problem_list.append({"pkId": temp_problem_data["pkId"],
                                              "problemId": temp_problem_data["problemId"],
                                              "index": temp_index})
                temp_choose["list"] = temp_problem_list
                temp_choose["firstIndex"] = first_index
                temp_choose["allCount"] = problem_data["allCount"]
                temp_choose["chooseCount"] = problem_data["chooseCount"]
                ready_choose_list.append(temp_choose)
        return ready_choose_list

    def get_has_choose_problem(self):
        for problem in self.week_test_problems:
            if problem["isChoosed"] != 0:
                return True
        return False

    def do_week_test_problem(self, student_level):
        update_problem_data = InterfaceMgr.get_interface("sigma_student", "update_problem_data")
        student_answer_list = list()
        student_choose_list = list()
        xz_count = self.get_xz_count()
        strategy_answer_list = WeekTestUtil.get_app_strategy_answer_list(student_level, self.problem_count, xz_count)
        # 勾选选做题
        choose_problem = InterfaceMgr.get_interface("sigma_student", "choose_problem")
        ready_choose_list = self.get_ready_choose_list()
        for temp_choose in ready_choose_list:
            temp_choose_list = temp_choose["list"]
            rand_choose_index_list = CommonFun.get_rand_n_num(len(temp_choose_list), temp_choose["chooseCount"])
            for rand_choose_index in rand_choose_index_list:
                rand_choose = temp_choose_list[rand_choose_index]
                student_choose_list.append(temp_choose["firstIndex"]+rand_choose_index)
                choose_problem_param = dict()
                choose_problem_param["pkId"] = rand_choose["pkId"]
                choose_problem_param["problemId"] = rand_choose["problemId"]
                choose_problem_param["_token_"] = self.token
                choose_problem_param["chooseType"] = 1
                self.week_test_problems[(rand_choose["index"]-1)]["isChoosed"] = 1
                if not CommonFun.test_interface(self.sigma_student_host, choose_problem,
                                                "post", choose_problem_param, self.vertify_common):
                    return False, None, None
        # 做题
        for problem_index in range(len(self.week_test_problems)):
            update_problem_data_param = dict()
            update_problem_param_data = self.get_update_problem_param_data(self.week_test_problems, strategy_answer_list[problem_index], problem_index, student_level)
            update_problem_data_param["studentId"] = self.student_id
            update_problem_data_param["data"] = [update_problem_param_data]
            update_problem_data_param["_token_"] = self.token
            if not CommonFun.test_interface(self.sigma_student_host, update_problem_data, "post",
                                            update_problem_data_param, self.vertify_update_problem_data):
                return False, None, None
            if self.week_test_problems[problem_index]["problemType"] == 0:
                student_answer_list.append(update_problem_param_data["isGrasp"])
            else:
                student_answer_list.append(update_problem_param_data["score"])
        return True, student_answer_list, student_choose_list

    def student_submit_task(self):
        # 提交
        hand_in = InterfaceMgr.get_interface("sigma_student", "hand_in")
        hand_in_param = dict()
        hand_in_param["studentId"] = self.student_id
        hand_in_param["taskId"] = self.stu_task_id
        hand_in_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, hand_in, "post", hand_in_param, "一周速测 交卷成功！"):
            return False
        return True

    def get_student_do_problem_data(self):
        stu_answer_list = list()
        stu_choose_list = list()
        for problem_index in range(len(self.week_test_problems)):
            problem_data = self.week_test_problems[problem_index]
            if problem_data["problemType"] == 0:
                stu_answer_list.append(problem_data["isGrasp"])
            else:
                stu_answer_list.append(problem_data["score"])
            if problem_data["isChoosed"] != 0:
                stu_choose_list.append(problem_index+1)
        return stu_answer_list, stu_choose_list

    def get_date_list(self):
        get_date_list = InterfaceMgr.get_interface("sigma_student", "get_date_list")
        get_date_list_param = dict()
        get_date_list_param["studentId"] = self.student_id
        get_date_list_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_date_list,
                                        "post", get_date_list_param, "获取时间列表成功！"):
            return False
        return True

if __name__ == '__main__':
    week_test = WeekTestByClass()
    account_list = AccountMgr.get_account_list(week_test.root_dir+"/sigma/week_test_by_class.csv")
    for config_info in account_list:
        log_name = config_info[0]+"_"+config_info[1]+"_"+config_info[2]+"_"+time.strftime("%Y_%m_%d")+".txt"
        week_test.school_id = week_test.student_service.get_school_id(config_info[0])
        week_test.class_id = week_test.student_service.get_class_id(week_test.school_id, config_info[1])
        all_feed_back_count = 0
        actual_feed_back_count = 0
        week_test_name = config_info[2]
        # 遍历各个分数段
        for section_index in range(5):
            # 获取到此分数段的学生列表
            student_list = week_test.student_service.get_student_list_by_section(week_test.school_id, week_test.class_id, section_index)
            for student_index, student_info in enumerate(student_list):
                student_level = section_index + 1
                result = week_test.app_login(student_info[0])
                student_name = student_info[1]
                if result is False:
                    continue
                # 时间列表
                if not week_test.get_date_list():
                    continue
                # 获取任务列表
                if not week_test.get_week_test_task(week_test_name):
                    print(student_info[0])
                    continue
                # 获取任务
                if not week_test.get_student_week_test_problem():
                    continue
                if week_test.task_status == 1 and week_test.get_has_choose_problem():
                    logger.info("student=%s,name=%s,已经勾选过选做题，这个逻辑还没想好怎么处理",
                                student_info[0], student_name)
                    continue
                if week_test.task_status == 2: # 2：交卷 3：生成报告
                    stu_answer_list, stu_choose_list = week_test.get_student_do_problem_data()
                    logger.info("student=%s,student_name=%s,已交卷,answer_list=%s,choose_list=%s",
                                student_info[0], student_name, str(stu_answer_list), str(stu_choose_list))
                    continue
                if week_test.task_status == 3:
                    logger.info("student=%s,student_name=%s,已生成报告",
                                student_info[0], student_name)
                    continue
                # 作答
                do_result, stu_answer_list, stu_choose_list = week_test.do_week_test_problem(student_level)
                if not do_result:
                    continue
                # 提交
                if not week_test.student_submit_task():
                    continue
                logger.info("student=%s,name=%s,answer_list=%s,choose_list=%s",
                            student_info[0], student_name, str(stu_answer_list), str(stu_choose_list))
    input("press enter to exit")