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
import json
import random


def get_yxzd_catalog(student_id, book_id):
    """预习指导目录
    :param student_id: 学生id
    :param book_id: 课本id"""
    host = DomainMgr.get_domain("sigma_student_host")
    http_util = HttpConnectMgr.get_http_connect()
    params = dict()
    params['studentId'] = student_id
    params['bookId'] = book_id
    response,res_code = http_util.get(host, "/web-sigma/app/teachercourse/getYXZDBookChildrenList",params)
    return response


def get_course_content_list(student_id, period_id):
    host = DomainMgr.get_domain("sigma_student_host")
    http_util = HttpConnectMgr.get_http_connect()
    params = dict()
    params['studentId'] = student_id
    params['peroidId'] = period_id
    response,res_code = http_util.get(host, "/web-sigma/app/teachercourse/getCourseContentList", params)
    return response


def submit_answer(student_id, homework_problem_id,problem_id, right_or_wrong, select_answer):
    host = DomainMgr.get_domain("sigma_student_host")
    http_util = HttpConnectMgr.get_http_connect()
    params = dict()
    datas = dict()
    datas["homeworkProblemId"] = homework_problem_id
    datas["isGrasp"] = right_or_wrong
    datas["time"] = random.randint(5, 60)
    datas["answerPath"] = ""
    datas["selectAnswer"] = select_answer
    datas["problemId"] = problem_id
    params["data"] = datas
    response,res_code = http_util.get(host, "/web-sigma/app/teachercourse/updateProblem", params)
    return response

def get_select_chapter_ids(catalog_infos, select_chapter_id_list):
    select_chapter_ids = list()
    catalog_infos_data = catalog_infos['data']
    for select_chapter_id in select_chapter_id_list:
        for chapter_rsp in catalog_infos_data:
            if str(chapter_rsp['id']) == select_chapter_id:
                if len(chapter_rsp['periodData']) > 0:
                    for period_data in chapter_rsp['periodData']:
                        select_chapter_ids.append(period_data['id'])
                chapter_rsp_section_data = chapter_rsp['sectionData']
                for section_data in chapter_rsp_section_data:
                    if len(section_data['periodData']) > 0:
                        for peroid_data in section_data['periodData']:
                            select_chapter_ids.append(peroid_data['id'])
    return select_chapter_ids

def get_xz_count(problem_ids):
    xz_count = 0
    for problem in problem_ids:
        if problem['type'] == 0:
            xz_count += 1
    return xz_count

def get_strategy_answer_list(xz_count, student_level, problem_count):
    root_dir = FileUtil.get_app_root_dir()
    ini_util = IniUtil(root_dir + "/student/feedback_strategy.ini")
    level = "level_"+str(student_level)
    xz_dividing_rate = float(ini_util.get_item_attr(level, "xz_dividing_rate"))
    xz_high_score_rate = float(ini_util.get_item_attr(level, "xz_high_score_rate"))
    xz_low_score_rate = float(ini_util.get_item_attr(level, "xz_low_score_rate"))
    jd_dividing_rate = float(ini_util.get_item_attr(level, "jd_dividing_rate"))
    jd_high_score_rate = float(ini_util.get_item_attr(level, "jd_high_score_rate"))
    jd_low_score_rate = float(ini_util.get_item_attr(level, "jd_low_score_rate"))
    answer_list = [0] * problem_count
    other_count = problem_count - xz_count
    for index in range(xz_count):
        if index < xz_dividing_rate * xz_count:
            if random.random() < xz_high_score_rate:
                answer_list[index] = 1
        else:
            if random.random() < xz_low_score_rate:
                answer_list[index] = 1
    for index2 in range(xz_count, problem_count):
        if (index2-xz_count) < jd_dividing_rate * other_count:
            if random.random() < jd_high_score_rate:
                answer_list[index2] = 1
        else:
            if random.random() < jd_low_score_rate:
                answer_list[index2] = 1
    return answer_list

def get_problem_ids_in_period(period_infos):
    problem_ids = list()
    exerciseProblem = period_infos['data']['exerciseProblem']
    if len(exerciseProblem) > 0:
        for problem in exerciseProblem:
            problem_dic = dict()
            problem_dic['homeworkProblemId'] = problem['homeworkProblemId']
            problem_dic['problemId'] = problem['problemId']
            problem_dic['type'] = problem['problemType']
            problem_ids.append(problem_dic)
    return problem_ids

def do_all_problem(student_id, problem_ids, strategy_answer_list):
    problem_service = ProblemService()
    answer_list = list()
    for index, problem in enumerate(problem_ids):
        homework_problem_id = problem['homeworkProblemId']
        is_right = sigma_service.get_problem_answer(homework_problem_id)
        if is_right == -1:
            answer = strategy_answer_list[index]
            answer_list.append(answer)
            if problem['type'] == 0:
                sequence = problem_service.get_problem_sequence(problem['problemId'])
                right_answer = problem_service.get_right_answer(sequence)
                if answer == 0:
                    rand_wrong_answer = problem_service.get_rand_wrong_answer(right_answer)
                    rand_wrong_answer_str = problem_service.get_answer_str(rand_wrong_answer)
                    submit_answer(student_id, problem['homeworkProblemId'], problem['problemId'], 0, rand_wrong_answer_str)
                else:
                    right_answer_str = problem_service.get_answer_str(right_answer)
                    submit_answer(student_id, problem['homeworkProblemId'], problem['problemId'], 1, right_answer_str)
            else:
                if answer == 0:
                    submit_answer(student_id, problem['homeworkProblemId'], problem['problemId'], 0, "")
                else:
                    submit_answer(student_id, problem['homeworkProblemId'], problem['problemId'], 1, "")
        else:
            answer_list.append(is_right)
    return answer_list

if __name__ == "__main__":
    root_dir = FileUtil.get_app_root_dir()
    account_list = AccountMgr.get_account_list(root_dir+"/sigma/teacher_thinking_class.csv")
    student_service = StudentService()
    sigma_service = SigmaService()
    for config_info in account_list:
        school_id = student_service.get_school_id(config_info[0])
        class_id = student_service.get_class_id(school_id, config_info[1])
        #book_id = sigma_service.get_course_id_by_name(config_info[2])
        book_id = config_info[2]
        select_chapter_id_list = config_info[3].split("#")
        student_list = student_service.get_student_list(school_id, class_id)
        for student_info in student_list:
            student_id, student_card, student_name,student_section = student_info[0],student_info[1],student_info[2],student_info[3]
            login_param = dict()
            login_param['loginName'] = student_card
            login_param['password'] = "123456"
            login_res,res_code = AccountMgr.login(login_param)
            if re.search("错误报告", login_res):
                print("[%s]login fail,please check you card and password" % student_card)
                continue
            catalog_rsp = get_yxzd_catalog(student_id, book_id)
            catalog_infos = json.loads(catalog_rsp)
            if catalog_infos['type'] == "success":
                select_chapter_ids = get_select_chapter_ids(catalog_infos, select_chapter_id_list)
                for period_id in select_chapter_ids:
                    period_name = sigma_service.get_course_name_by_id(period_id)
                    period_content_rsp = get_course_content_list(student_id, period_id)
                    period_infos = json.loads(period_content_rsp)
                    if period_infos['type'] == "success":
                        problem_ids = get_problem_ids_in_period(period_infos)
                        problem_count = len(problem_ids)
                        xz_count = get_xz_count(problem_ids)
                        student_level = student_section
                        if student_level is None:
                            student_level = 3
                        else:
                            student_level += 1
                        strategy_answer_list = get_strategy_answer_list(xz_count, student_level, problem_count)
                        answer_list = do_all_problem(student_id, problem_ids, strategy_answer_list)
                        print("card=[%s],name=[%s],level=[%s],period=[%s],answer_list=%s" %
                             (student_card,student_name,period_name,student_level,str(answer_list)))
                    else:
                        print("student_card=[%s],student_name=[%s],period_id=[%d] get_course_content出错" %
                              (student_card,student_name,period_id))
            else:
                print("student_card=[%s],student_name=[%s],book_id=[%d] get_yxzd_catalog出错" %
                      (student_card, student_name,book_id))
    input("press enter to exit")
