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


class StudentPassProcess:
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
        login_res_json = json.loads(login_res)
        if login_res_json["type"] == "failure":
            logger.info("account=%s,登录失败，原因：%s", account,login_res_json["message"])
            return False
        login_res_json = json.loads(login_res)
        self.token = login_res_json["userdata"]["token"]
        self.student_id = login_res_json["userdata"]["serverStudentId"]
        return True

    def get_answer_data(self, exercise_problems, need_pass):
        answer_data = list()
        for exerciseProblem in exercise_problems:
            answer = dict()
            answer["homeworkProblemId"] = exerciseProblem["homeworkProblemId"]
            answer["problemId"] = exerciseProblem["problemId"]
            answer["time"] = random.randint(10, 100)
            answer["answerPath"] = WeekTestUtil.get_answer_picture()
            if need_pass:
                answer["selectAnswer"] = exerciseProblem["selectStandardAnswer"]
                answer["isGrasp"] = 1
            else:
                right_answer = self.problem_service.get_right_answer_by_id(exerciseProblem["problemId"])
                rand_wrong_answer = self.problem_service.get_rand_wrong_answer(right_answer)
                rand_wrong_answer_str = self.problem_service.get_answer_str(rand_wrong_answer)
                answer["selectAnswer"] = rand_wrong_answer_str
                answer["isGrasp"] = 0
            answer_data.append(answer)
        return answer_data

    @staticmethod
    def get_course_pass_score(first_pass, course_type, class_rank):
        add_score = 0
        if course_type == 3:  # 章测
            if first_pass:
                add_score += 6
            add_score += 15
            if class_rank < 3:
                add_score += 3
        elif course_type == 4: #节测
            if first_pass:
                add_score += 2
            add_score += 5
            if class_rank < 3:
                add_score += 1
        return add_score

    def submit_answers(self, homework_id, answer_data, param):
        upload_pass_data = InterfaceMgr.get_interface("sigma_student", "upload_pass_data")
        upload_pass_data_param = dict()
        hand_in_hw = [{"status": 1, "homeworkId": homework_id}]

        data = dict()
        data["id"] = param["task_id"]
        data["isLocalTrain"] = 0
        data["moduleType"] = param["module_type"]
        data["studentId"] = self.student_id
        data["doDate"] = int(time.time()*1000)
        data["taskType"] = param["task_type"]
        data["problemData"] = answer_data
        data = [data]

        upload_pass_data_param["handInHw"] = hand_in_hw
        upload_pass_data_param["data"] = data
        upload_pass_data_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, upload_pass_data, "post", upload_pass_data_param,
                                        "上传离线过关数据成功！"):
            return False
        return True

    def vertify_get_book_list(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["type"] != "success":
            return False
        rand_num = random.randint(0, (len(response_json["data"])-1))
        rand_data = response_json["data"][rand_num]
        self.rand_book_id = rand_data["id"]
        self.rand_book_name = rand_data["name"]
        logger.info("选择书本：%s", self.rand_book_name)
        return True

    def vertify_get_student_pass_list(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["type"] != "success":
            return False
        module_type = vertify_param["module_type"]
        if not self.do_pass_practice(response_json, module_type):
            return False
        return True

    def vertify_get_student_pass_content(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["type"] != "success":
            return False
        homework_id = response_json["data"]["exerciseProblem"][0]["homeworkId"]
        need_pass = vertify_param["need_pass"]
        answer_data = self.get_answer_data(response_json["data"]["exerciseProblem"], need_pass)
        if not self.submit_answers(homework_id, answer_data, vertify_param):
            return False
        return True

    def vertify_get_class_ranking(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["type"] != "success":
            return False
        return True

    def vertify_get_grade_ranking(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["type"] != "success":
            return False
        return True

    def get_class_ranking(self):
        get_class_ranking = InterfaceMgr.get_interface("sigma_student", "get_class_ranking")
        get_class_ranking_param = dict()
        get_class_ranking_param["studentId"] = self.student_id
        get_class_ranking_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_class_ranking, "post",
                                        get_class_ranking_param, self.vertify_get_class_ranking):
            return False
        return True

    def get_grade_ranking(self):
        get_grade_ranking = InterfaceMgr.get_interface("sigma_student", "get_grade_ranking")
        get_grade_ranking_param = dict()
        get_grade_ranking_param["studentId"] = self.student_id
        get_grade_ranking_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_grade_ranking, "post",
                                        get_grade_ranking_param, self.vertify_get_grade_ranking):
            return False
        return True

    def do_pass_practice(self, get_student_pass_response_json, module_type):
        for student_pass_info in get_student_pass_response_json["data"]:
            for student_pass_period in student_pass_info["periodData"]:
                exercise_status = student_pass_period["exerciseStatus"]
                task_type = student_pass_period["peroidType"]
                course_id = student_pass_period["id"]
                course_name = student_pass_period["name"]

                first_pass = self.sigma_service.get_student_pass_first_pass(self.student_id,course_id)
                class_rank_record = self.sigma_service.get_student_pass_class_rank(self.test_class_id,course_id)
                class_rank = class_rank_record + 1
                if module_type == ModuleType["mingshi"]:
                    course_type = self.sigma_service.get_mssw_course_type(course_id)
                elif module_type == ModuleType["gaokao_1"]:
                    course_type = self.sigma_service.get_gk1_course_type(course_id)
                pre_score = self.sigma_service.get_student_pass_score(self.student_id)
                need_add_score = self.get_course_pass_score(first_pass, course_type, class_rank)

                need_pass = False
                pass_round = random.randint(1, 2)
                for round_index in range(pass_round):
                    if round_index == pass_round - 1:
                        need_pass = True
                if not self.get_student_pass_content(course_id, module_type, task_type, need_pass):
                    return False

                after_score = self.sigma_service.get_student_pass_score(self.student_id)
                real_add_score = after_score-pre_score
                if real_add_score != need_add_score:
                    logger.error("student_account=%s,chapter_name=%s,course_name=%s,%d次通关后,积分增加值不符,"
                                 "exercise_status=%s,first_add=%s,course_type=%d,class_rank=%d,need_add=%d,real_add=%d",
                                 self.student_account, student_pass_info["name"], course_name, pass_round,
                                 exercise_status, first_pass, course_type, class_rank, need_add_score, real_add_score)
                else:
                    logger.info("student_account=%s,chapter_name=%s,course_name=%s,%d次通关后,积分增加正确,"
                                "exercise_status=%s,first_add=%s,course_type=%d,class_rank=%d,need_add=%d,real_add=%d",
                                self.student_account, student_pass_info["name"], course_name, pass_round,
                                exercise_status, first_pass, course_type, class_rank, need_add_score, real_add_score)
            return True # todo
        return True

    def get_student_pass_content(self, course_id, module_type, task_type, need_pass):
        get_student_pass_content = InterfaceMgr.get_interface("sigma_student", "get_student_pass_content")
        get_student_pass_content_param = dict()
        get_student_pass_content_param["studentId"] = self.student_id
        get_student_pass_content_param["taskId"] = course_id
        get_student_pass_content_param["moduleType"] = module_type
        get_student_pass_content_param["taskType"] = task_type
        if not CommonFun.test_interface(self.sigma_student_host, get_student_pass_content,
                                        "post", get_student_pass_content_param, self.vertify_get_student_pass_content,
                                        {"task_id":course_id, "module_type":module_type, "task_type":task_type, "need_pass":need_pass}):
            return False
        return True

    def get_rand_book(self):
        get_book_list = InterfaceMgr.get_interface("sigma_student", "get_book_list")
        get_book_list_param = dict()
        get_book_list_param["project"] = 1
        get_book_list_param["studentId"] = self.student_id
        get_book_list_param["moduleType"] = 1
        get_book_list_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_book_list,
                                        "post", get_book_list_param, self.vertify_get_book_list):
            return False
        return True

    def get_period_data(self, book_id, module_type):
        get_student_pass_list = InterfaceMgr.get_interface("sigma_student", "get_student_pass_list")
        get_student_pass_list_param = dict()
        get_student_pass_list_param["studentId"] = self.student_id
        get_student_pass_list_param["id"] = book_id
        get_student_pass_list_param["moduleType"] = module_type
        get_student_pass_list_param["taskType"] = TaskType["student_pass"]
        get_student_pass_list_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_student_pass_list,
                                        "post", get_student_pass_list_param, self.vertify_get_student_pass_list,
                                        {"module_type": module_type}):
            return False
        return True

if __name__ == "__main__":
    student_pass_process = StudentPassProcess()
    student_pass_process.get_rand_student()
    if not student_pass_process.app_login(student_pass_process.student_account):
        exit("")
    if not student_pass_process.get_rand_book():
        exit("")
    logger.info("名师思维攻关")
    if not student_pass_process.get_period_data(student_pass_process.rand_book_id,ModuleType["mingshi"]):
        exit("")
    logger.info("高考一轮攻关")
    if not student_pass_process.get_period_data(None, ModuleType["gaokao_1"]):
        exit("")
    if not student_pass_process.get_class_ranking():
        exit("")
    if not student_pass_process.get_grade_ranking():
        exit("")

    logger.info("攻关测试完成")