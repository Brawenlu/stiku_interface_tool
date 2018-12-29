#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
import re
from util.file_util import FileUtil
from util.account_mgr import AccountMgr
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
from util.file_util import IniUtil
from service.student_service import StudentService
from service.problem_service import ProblemService
from service.sigma_service import SigmaService
from util.week_test_util import WeekTestUtil

import json
import random
import time

def get_book_list(student_id):
    host = DomainMgr.get_domain("sigma_student_host")
    http_util = HttpConnectMgr.get_http_connect()
    params = dict()
    params['studentId'] = student_id
    params['project'] = 1
    response,res_code = http_util.get(host, "/web-sigma/app/teachercourse/getBookList",params)
    return response

def get_student_pass_list(student_id,book_id,module_type):
    host = DomainMgr.get_domain("sigma_student_host")
    http_util = HttpConnectMgr.get_http_connect()
    params = dict()
    params['studentId'] = student_id
    params['id'] = book_id
    params['moduleType'] = module_type
    response,res_code = http_util.get(host, "/web-sigma/app/studentpass/getStudentPassList",params)
    return response

def get_student_pass_content(student_id,book_id,module_type,task_type):
    host = DomainMgr.get_domain("sigma_student_host")
    http_util = HttpConnectMgr.get_http_connect()
    params = dict()
    params['studentId'] = student_id
    params['taskId'] = book_id
    params['moduleType'] = module_type
    params["taskType"] = task_type
    response,res_code = http_util.get(host, "/web-sigma/app/studentpass/getStudentPassContent",params)
    return response

def submit_answers(homework_id,data):
    host = DomainMgr.get_domain("sigma_student_host")
    http_util = HttpConnectMgr.get_http_connect()
    params = dict()
    handInHw=[{"status":1,"homeworkId":homework_id}]
    handInHw = json.dumps(handInHw)
    params['data'] = data
    params['handInHw'] = handInHw
    response,res_code = http_util.post(host, "/web-sigma/app/studentpass/updateStudentPassProblems",params)
    return response

def get_answer_data(exerciseProblems):
    answer_data = list()
    for exerciseProblem in exerciseProblems:
        answer = dict()
        answer["homeworkProblemId"] = exerciseProblem["homeworkProblemId"]
        answer["isGrasp"] = 1
        answer["time"] = random.randint(10,100)
        answer["answerPath"] = WeekTestUtil.get_answer_picture()
        answer["selectAnswer"] = exerciseProblem["selectStandardAnswer"]
        answer["problemId"] = exerciseProblem["problemId"]
        answer_data.append(answer)
    answer_data_json = json.dumps(answer_data)
    return answer_data_json

def get_answer_data2(exerciseProblems,need_pass):
    answer_data = list()
    problem_service = ProblemService()
    for exerciseProblem in exerciseProblems:
        answer = dict()
        answer["homeworkProblemId"] = exerciseProblem["homeworkProblemId"]
        answer["problemId"] = exerciseProblem["problemId"]
        answer["time"] = random.randint(10,100)
        answer["answerPath"] = WeekTestUtil.get_answer_picture()
        if need_pass:
            answer["selectAnswer"] = exerciseProblem["selectStandardAnswer"]
            answer["isGrasp"] = 1
        else:
            right_answer = problem_service.get_right_answer_by_id(exerciseProblem["problemId"])
            rand_wrong_answer = problem_service.get_rand_wrong_answer(right_answer)
            rand_wrong_answer_str = problem_service.get_answer_str(rand_wrong_answer)
            answer["selectAnswer"] = rand_wrong_answer_str
            answer["isGrasp"] = 0
        answer_data.append(answer)
    answer_data_json = json.dumps(answer_data)
    return answer_data_json

"""
名师思维
tbt_teacher_course

kk 2016/8/3 10:31:17
data_type：3 章，4-节
"""
def doing_mssw_student_pass(student_card,student_id,module_type,book_name):
    book_list_rsp = get_book_list(student_id)
    book_list_data = json.loads(book_list_rsp)
    sigma_service = SigmaService()
    student_service = StudentService()
    add_scores = 0
    student_info = student_service.get_student_profile_info(student_card)
    class_id = student_info[1]

    if book_list_data['type'] == "success":
        for book_info in book_list_data["data"]:
            if book_info["name"] == book_name:
                book_id = book_info["id"]
                student_pass_list_rsp = get_student_pass_list(student_id,book_id,module_type)
                student_pass_list_info = json.loads(student_pass_list_rsp)
                if student_pass_list_info["type"] == "success":
                    for student_pass_info in student_pass_list_info["data"]:
                        if student_pass_info["status"] == 1:
                            for period_data in student_pass_info["periodData"]:
                                exercise_status = period_data["exerciseStatus"]
                                if exercise_status == 0 or exercise_status == 2 or exercise_status == 3:
                                    task_type = period_data["peroidType"]
                                    course_id = period_data["id"]
                                    course_name = period_data["name"]
                                    task_content_rsp = get_student_pass_content(student_id,period_data["id"],module_type,task_type)
                                    task_content = json.loads(task_content_rsp)
                                    if task_content["type"] == "success":
                                        homework_id = task_content["data"]["exerciseProblem"][0]["homeworkId"]
                                        answer_data = get_answer_data(task_content["data"]["exerciseProblem"])
                                        first_pass = sigma_service.get_student_pass_first_pass(student_id,course_id)
                                        class_rank = sigma_service.get_student_pass_class_rank(class_id,course_id)
                                        course_type = sigma_service.get_mssw_course_type(course_id)
                                        add_score = 0
                                        if course_type == 3:  # 章测
                                            if first_pass:
                                                #print("course_id=%d,course_name=%s,章测首次通关" % (course_id,course_name))
                                                add_scores += 6
                                                add_score += 6
                                            add_scores += 15
                                            add_score += 15
                                            if class_rank < 3:
                                                #print("course_id=%d,course_name=%s,章测班级前3" % (course_id,course_name))
                                                add_scores += 3
                                                add_score += 3
                                        elif course_type == 4: #节测
                                            if first_pass:
                                                #print("course_id=%d,course_name=%s,节测首次通关" % (course_id,course_name))
                                                add_scores += 2
                                                add_score += 2
                                            add_scores += 5
                                            add_score += 5
                                            if class_rank < 3:
                                                #print("course_id=%d,course_name=%s,节测班级前3" % (course_id,course_name))
                                                add_scores += 1
                                                add_score += 1
                                        else:
                                            pass
                                        #print("course_id=%d,add_score=%d" % (course_id,add_score))
                                        submit_rsp = submit_answers(homework_id,answer_data)
                                        submit_rsp_info = json.loads(submit_rsp)
                                        time.sleep(0.5)
                                        if submit_rsp_info["type"] == "failure":
                                            print(submit_rsp_info)
                                            return
                print("card=[%s],book=[%s]全部通关了" % (student_card,book_name))
    return add_scores

def doing_mssw_student_pass2(student_card,student_id,module_type,book_name,pass_round):
    book_list_rsp = get_book_list(student_id)
    book_list_data = json.loads(book_list_rsp)
    sigma_service = SigmaService()
    student_service = StudentService()
    add_scores = 0
    student_info = student_service.get_student_profile_info(student_card)
    class_id = student_info[1]

    if book_list_data['type'] == "success":
        for book_info in book_list_data["data"]:
            if book_info["name"] == book_name:
                book_id = book_info["id"]
                student_pass_list_rsp = get_student_pass_list(student_id,book_id,module_type)
                student_pass_list_info = json.loads(student_pass_list_rsp)
                if student_pass_list_info["type"] == "success":
                    for student_pass_info in student_pass_list_info["data"]:
                        if student_pass_info["status"] == 1:
                            for period_data in student_pass_info["periodData"]:
                                exercise_status = period_data["exerciseStatus"]
                                if exercise_status == 0 or exercise_status == 2 or exercise_status == 3:
                                    task_type = period_data["peroidType"]
                                    course_id = period_data["id"]
                                    course_name = period_data["name"]
                                    for pass_round_index in range(pass_round):
                                        need_pass = False
                                        if pass_round_index == pass_round-1:
                                            need_pass = True
                                        task_content_rsp = get_student_pass_content(student_id,period_data["id"],module_type,task_type)
                                        task_content = json.loads(task_content_rsp)
                                        if task_content["type"] == "success":
                                            homework_id = task_content["data"]["exerciseProblem"][0]["homeworkId"]
                                            answer_data = get_answer_data2(task_content["data"]["exerciseProblem"],need_pass)
                                            first_pass = sigma_service.get_student_pass_first_pass(student_id,course_id)
                                            class_rank = sigma_service.get_student_pass_class_rank(class_id,course_id)
                                            course_type = sigma_service.get_mssw_course_type(course_id)
                                            add_score = 0
                                            if course_type == 3:  # 章测
                                                if first_pass:
                                                    print("course_id=%d,course_name=%s,章测首次通关" % (course_id,course_name))
                                                    add_scores += 6
                                                    add_score += 6
                                                add_scores += 15
                                                add_score += 15
                                                if class_rank < 3:
                                                    print("course_id=%d,course_name=%s,章测班级前3" % (course_id,course_name))
                                                    add_scores += 3
                                                    add_score += 3
                                            elif course_type == 4: #节测
                                                if first_pass:
                                                    print("course_id=%d,course_name=%s,节测首次通关" % (course_id,course_name))
                                                    add_scores += 2
                                                    add_score += 2
                                                add_scores += 5
                                                add_score += 5
                                                if class_rank < 3:
                                                    print("course_id=%d,course_name=%s,节测班级前3" % (course_id,course_name))
                                                    add_scores += 1
                                                    add_score += 1
                                            else:
                                                pass
                                            print("course_id=%d,add_score=%d" % (course_id,add_score))
                                            submit_rsp = submit_answers(homework_id,answer_data)
                                            submit_rsp_info = json.loads(submit_rsp)
                                            time.sleep(0.5)
                                            if submit_rsp_info["type"] == "failure":
                                                print(submit_rsp_info)
                                                return
                print("card=[%s],book=[%s]全部通关了" % (student_card,book_name))
    return add_scores


def doing_gk_studnet_pass(student_id,module_type,chapter_start,chapter_sum):
    student_pass_list_rsp = get_student_pass_list(student_id,0,module_type)
    student_pass_list_info = json.loads(student_pass_list_rsp)
    add_scores = 0
    student_info = student_service.get_student_profile_info(student_card)
    class_id = student_info[1]
    if student_pass_list_info["type"] == "success":
        chapter_index = 1
        for student_pass_info in student_pass_list_info["data"]:
            if chapter_index >= chapter_start and chapter_index < chapter_start+chapter_sum:
                for period_data in student_pass_info["periodData"]:
                    exercise_status = period_data["exerciseStatus"]
                    if exercise_status == 0 or exercise_status == 2 or exercise_status == 3:
                        task_type = period_data["peroidType"]
                        course_id = period_data["id"]
                        course_name = period_data["name"]
                        task_content_rsp = get_student_pass_content(student_id,period_data["id"],module_type,task_type)
                        #print(task_content_rsp)
                        task_content = json.loads(task_content_rsp)
                        if task_content["type"] == "success":
                            homework_id = task_content["data"]["exerciseProblem"][0]["homeworkId"]
                            answer_data = get_answer_data(task_content["data"]["exerciseProblem"])
                            first_pass = sigma_service.get_student_pass_first_pass(student_id,course_id)
                            class_rank = sigma_service.get_student_pass_class_rank(class_id,course_id)
                            course_type = sigma_service.get_gk1_course_type(course_id)
                            add_score = 0
                            if course_type == 3:  # 章测
                                if first_pass:
                                    print("course_id=%d,course_name=%s,章测首次通关" % (course_id,course_name))
                                    add_scores += 6
                                    add_score += 6
                                add_scores += 15
                                add_score += 15
                                if class_rank < 3:
                                    print("course_id=%d,course_name=%s,章测班级前3" % (course_id,course_name))
                                    add_scores += 3
                                    add_score += 3
                            elif course_type == 4: #节测
                                if first_pass:
                                    print("course_id=%d,course_name=%s,节测首次通关" % (course_id,course_name))
                                    add_scores += 2
                                    add_score += 2
                                add_scores += 5
                                add_score += 5
                                if class_rank < 3:
                                    print("course_id=%d,course_name=%s,节测班级前3" % (course_id,course_name))
                                    add_scores += 1
                                    add_score += 1
                            else:
                                pass
                            print("course_id=%d,add_score=%d" % (course_id,add_score))
                            submit_rsp = submit_answers(homework_id,answer_data)
                            submit_rsp_info = json.loads(submit_rsp)
                            time.sleep(0.5)
                            if submit_rsp_info["type"] == "failure":
                                print(submit_rsp_info)
                                return
            chapter_index += 1
    print("card=[%s],高考1轮,从第[%d]章到第[%d]章已通关了" % (student_card,chapter_start,chapter_start+chapter_sum))
    return add_scores

def doing_gk_studnet_pass2(student_id,module_type,chapter_start,chapter_sum,pass_round):
    student_pass_list_rsp = get_student_pass_list(student_id,0,module_type)
    student_pass_list_info = json.loads(student_pass_list_rsp)
    add_scores = 0
    student_info = student_service.get_student_profile_info(student_card)
    class_id = student_info[1]
    if student_pass_list_info["type"] == "success":
        chapter_index = 1
        for student_pass_info in student_pass_list_info["data"]:
            if chapter_index >= chapter_start and chapter_index < chapter_start+chapter_sum:
                for period_data in student_pass_info["periodData"]:
                    exercise_status = period_data["exerciseStatus"]
                    if exercise_status == 0 or exercise_status == 2 or exercise_status == 3:
                        task_type = period_data["peroidType"]
                        course_id = period_data["id"]
                        course_name = period_data["name"]
                        for pass_round_index in range(pass_round):
                            need_pass = False
                            if pass_round_index == pass_round-1:
                                need_pass = True
                            task_content_rsp = get_student_pass_content(student_id,period_data["id"],module_type,task_type)
                            task_content = json.loads(task_content_rsp)
                            if task_content["type"] == "success":
                                homework_id = task_content["data"]["exerciseProblem"][0]["homeworkId"]
                                answer_data = get_answer_data2(task_content["data"]["exerciseProblem"],need_pass)
                                first_pass = sigma_service.get_student_pass_first_pass(student_id,course_id)
                                class_rank = sigma_service.get_student_pass_class_rank(class_id,course_id)
                                course_type = sigma_service.get_gk1_course_type(course_id)
                                add_score = 0
                                if course_type == 3:  # 章测
                                    if first_pass:
                                        print("course_id=%d,course_name=%s,章测首次通关" % (course_id,course_name))
                                        add_scores += 6
                                        add_score += 6
                                    add_scores += 15
                                    add_score += 15
                                    if class_rank < 3:
                                        print("course_id=%d,course_name=%s,章测班级前3" % (course_id,course_name))
                                        add_scores += 3
                                        add_score += 3
                                elif course_type == 4: #节测
                                    if first_pass:
                                        print("course_id=%d,course_name=%s,节测首次通关" % (course_id,course_name))
                                        add_scores += 2
                                        add_score += 2
                                    add_scores += 5
                                    add_score += 5
                                    if class_rank < 3:
                                        print("course_id=%d,course_name=%s,节测班级前3" % (course_id,course_name))
                                        add_scores += 1
                                        add_score += 1
                                else:
                                    pass
                                print("course_id=%d,add_score=%d" % (course_id,add_score))
                                submit_rsp = submit_answers(homework_id,answer_data)
                                submit_rsp_info = json.loads(submit_rsp)
                                time.sleep(0.5)
                                if submit_rsp_info["type"] == "failure":
                                    print(submit_rsp_info)
                                    return
            chapter_index += 1
    print("card=[%s],高考1轮,从第[%d]章到第[%d]章已通关了" % (student_card,chapter_start,chapter_start+chapter_sum))
    return add_scores

if __name__ == "__main__":
    root_dir = FileUtil.get_app_root_dir()
    account_list = AccountMgr.get_account_list(root_dir+"/sigma/student_pass_by_class.csv")
    student_service = StudentService()
    sigma_service = SigmaService()
    for config_info in account_list:
        school_id = student_service.get_school_id(config_info[0])
        class_id = student_service.get_class_id(school_id, config_info[1])
        student_list = student_service.get_student_list(school_id, class_id)
        for student_info in student_list:
            student_id, student_card, student_name,student_section = student_info[0],student_info[1],student_info[2],student_info[3]
            login_param = dict()
            login_param['loginName'] = student_card
            login_param['password'] = "123456"
            login_res,res_code = AccountMgr.app_login(login_param)
            if re.search("错误报告", login_res):
                print("[%s]login fail,please check you card and password" % student_card)
                continue
            module_type = int(config_info[2])
            book_name = config_info[3]
            chapter_start = int(config_info[4])
            chapter_sum = int(config_info[5])
            pass_round = int(config_info[6])
            student_id = student_service.get_student_id(student_card)
            init_score = sigma_service.get_student_pass_score(student_id)
            add_scores = 0
            if module_type == 1:
                add_scores = doing_mssw_student_pass2(student_card,student_id,module_type,book_name,pass_round)
            else:
                add_scores = doing_gk_studnet_pass2(student_id,module_type,chapter_start,chapter_sum,pass_round)
            print("student=[%s],org_score=[%d],expect_add=[%d],expect_score=[%d]" % (student_card,init_score,add_scores,init_score+add_scores))
    input("press enter to exit")
