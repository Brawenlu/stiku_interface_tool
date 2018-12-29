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
from util.file_util import IniUtil
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
from util.common_fun import CommonFun
from service.problem_service import ProblemService
from service.student_service import StudentService
import re
import time
import random
import codecs
import json
import copy


def get_week_test_tasks():
    http_util = HttpConnectMgr.get_http_connect()
    host = DomainMgr.get_domain("student_host")
    http_util.get(host, "/web-student/weekTest/viewMain", None)


def get_xz_count(week_test_id, problem_count):
    xz_count = 0
    for problem_index in range(problem_count):
        paper_problem_id = problem_service.get_week_test_paper_problem_id(week_test_id,problem_index+1)
        problem_type = problem_service.get_problem_type_by_id(paper_problem_id)
        if problem_type == 0:
            xz_count += 1
    return xz_count

def hand_in_paper(week_test_id):
    http_util = HttpConnectMgr.get_http_connect()
    host = DomainMgr.get_domain("student_host")
    http_util.post(host, "/web-student/weekTest/handIn", {"wtId":week_test_id})


def do_all_problem(week_test_id, problem_count, strategy_answer_list, account, student_level):
    problem_service = ProblemService()
    host = DomainMgr.get_domain("student_host")
    http_util = HttpConnectMgr.get_http_connect()
    ini_util = IniUtil(root_dir + "/student/feedback_strategy.ini")
    level = "level_"+str(student_level)
    jd_high_score_rate = float(ini_util.get_item_attr(level, "jd_high_score_rate"))
    jd_low_score_rate = float(ini_util.get_item_attr(level, "jd_low_score_rate"))
    week_test_info = problem_service.get_week_test_info(week_test_id)
    class_id = week_test_info[6]
    teacher_week_test_id = week_test_info[10]
    params = dict()
    params["wtId"] = week_test_id
    answers = ""
    week_test_status = problem_service.get_week_test_status(teacher_week_test_id, class_id)
    has_feedback = False
    choose_str = ""
    choose_list = list()
    temp_choose_list = list()
    index_pointer = 0
    for problem_index in range(problem_count):
        all_list = list()
        week_test_problem_id, paper_problem_id,index_no, score, is_grasp, grasp_score, student_grasp_score,first_index,all_count,choose_count,student_choose = problem_service.get_week_test_problem_info(week_test_id,problem_index+1)
        if first_index != -1:
            for xz_problem_index in range(first_index,first_index+all_count):
                all_list.append(xz_problem_index)
        if week_test_status == 2 or week_test_status ==1:   # 1:已收卷 2:已阅卷
            has_feedback = True
            if (problem_index+1) in all_list:
                if student_choose == 1:
                    choose_list.append(index_no)
                    strategy_answer_list[problem_index] = grasp_score
                else:
                    strategy_answer_list[problem_index] = 0
            else:
                strategy_answer_list[problem_index] = grasp_score
        else:
            if is_grasp != -1:
                has_feedback = True
                if (problem_index+1) in all_list:
                    if student_choose == 1:
                        choose_list.append(index_no)
                        strategy_answer_list[problem_index] = grasp_score
                    else:
                        strategy_answer_list[problem_index] = 0
                else:
                    strategy_answer_list[problem_index] = grasp_score
            else:
                if first_index != -1 and problem_index>=index_pointer:
                    temp_choose_list = CommonFun.get_rand_n_value(all_list,choose_count)
                    for value in temp_choose_list:
                        choose_list.append(value)
                    index_pointer = problem_index + all_count
                if (problem_index+1) in temp_choose_list:   #选做题
                    choose_str += str(problem_index+1)+","
                if problem_index >= index_pointer:
                    temp_choose_list.clear()

                problem_type = problem_service.get_problem_type_by_id(paper_problem_id)
                strategy_answer = strategy_answer_list[problem_index]
                if problem_type == 0:   # 选择
                    right_answer = problem_service.get_right_answer_by_id(paper_problem_id)
                    rand_wrong_answer = problem_service.get_rand_wrong_answer(right_answer, (1,10,100,1000,2))
                    if strategy_answer == 1:
                        answers += str(right_answer)
                        if (problem_index+1) in all_list:
                            if (problem_index+1) in choose_list:
                                strategy_answer_list[problem_index] = score
                            else:
                                strategy_answer_list[problem_index] = 0
                        else:
                            strategy_answer_list[problem_index] = score
                    else:
                        answers += str(rand_wrong_answer)
                        strategy_answer_list[problem_index] = 0
                elif problem_type == 1:  # 填空
                    if strategy_answer == 1:
                        answers += "1"  # 1:正确 0:错误
                        if (problem_index+1) in all_list:
                            if (problem_index+1) in choose_list:   #选做题
                                strategy_answer_list[problem_index] = score
                            else:
                                strategy_answer_list[problem_index] = 0
                        else:
                            strategy_answer_list[problem_index] = score
                    else:
                        answers += "0"
                        strategy_answer_list[problem_index] = 0
                else:   # 解答
                    student_score = 0
                    if strategy_answer == 1:
                        student_score = random.randint(int(score * jd_low_score_rate),int(score * jd_high_score_rate))
                        answers += str(student_score)
                    else:
                        student_score = random.randint(1,int(score * jd_low_score_rate))
                        answers += str(student_score)
                    if (problem_index+1) in all_list:
                        if (problem_index+1) in choose_list:   #选做题
                            strategy_answer_list[problem_index] = student_score
                        else:
                            strategy_answer_list[problem_index] = 0
                    else:
                        strategy_answer_list[problem_index] = student_score
        if problem_index != problem_count-1:
            answers += ","
    if not has_feedback:
        params["answers"] = answers
        params["chooseStr"] = choose_str
        res,res_code = http_util.post(host, "/web-student/weekTest/answerFeedback", params)
        if re.search("错误报告", res):
            print("account=[%s],week_test_id=[%s]week_test_error" % (account, week_test_id))
            err_file_name = "week_test_error_%s_%s.html" % (account, week_test_id)
            FileUtil.create_file(err_file_name, res)
    return strategy_answer_list,choose_list

if __name__ == "__main__":
    root_dir = FileUtil.get_app_root_dir()
    config_list = AccountMgr.get_account_list(root_dir+"/student/week_test_by_person.csv")
    student_service = StudentService()
    problem_service = ProblemService()
    log_name = "week_test_by_person"+"_"+time.strftime("%Y_%m_%d")+".txt"
    file_obj = codecs.open(log_name, "w", encoding="utf-8")
    all_feed_back_count = 0
    actual_feed_back_count = 0
    for config in config_list:
        login_param = dict()
        login_param['loginName'] = config[0]
        login_param['password'] = config[1]
        login_res,res_code = AccountMgr.login(login_param)
        if re.search("错误报告", login_res):
            print("[%s]login fail,please check you card and password" % config[0])
            continue
        else:
            all_feed_back_count += 1
        get_week_test_tasks()
        student_id = student_service.get_student_id(config[0])
        week_test_name = config[3]
        week_test_id = problem_service.get_week_test_id(week_test_name, student_id)
        if week_test_id is not None:
            problem_count = problem_service.get_week_test_count(week_test_id)
            student_level = config[2]
            student_profile = student_service.get_student_profile_info(config[0])
            if student_level == "":
                if student_profile[6] is None:
                    student_level = 3
                else:
                    student_level = student_profile[6]+1
            xz_count = get_xz_count(week_test_id, problem_count)
            strategy_answer_list = CommonFun.get_strategy_answer_list(xz_count, student_level, problem_count)
            actual_answer_list,choose_list = do_all_problem(week_test_id, problem_count, strategy_answer_list, config[0], student_level)
            actual_feed_back_count += 1
            log_str = "account=[%s],name=[%s],paper=[%s],level=[%s],detail%s,choose_list=%s" % \
                      (config[0],student_profile[2], config[3], student_level, str(actual_answer_list),str(choose_list))
            print(log_str)
            file_obj.write(log_str+"\n")
        else:
            print("account=[%s],found no week_test" % (config[0]))
        hand_in_paper(week_test_id)

    log_str = "total feedback=[%d],effective feedback=[%d]" % \
              (all_feed_back_count, actual_feed_back_count)
    print(log_str)
    file_obj.write(log_str+"\n")
    file_obj.close()
    input("press enter to exit")