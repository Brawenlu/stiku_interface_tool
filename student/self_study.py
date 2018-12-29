#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
import re
import time
import random
from util.file_util import FileUtil
from util.account_mgr import AccountMgr
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
from service.student_service import StudentService
from service.problem_service import ProblemService


def get_latest_homework_id():
    host = DomainMgr.get_domain("student_host")
    http_util = HttpConnectMgr.get_http_connect()
    res,res_code = http_util.get(host, "/web-student/teacherHomework/showTeacherHomework", {})
    homework_id = None
    try:
        homework_id = re.search("startDoHomework\(\'(.*?)\'\)", res).group(1)
    except:
        pass
    return homework_id


def get_problem_count(homework_id):
    problem_service = ProblemService()
    return problem_service.get_homework_cout(homework_id)


def get_problem_sequence(homework_id, problem_index):
    problem_service = ProblemService()
    problem_id = problem_service.get_homework_problem_id(homework_id, problem_index)
    sequence = problem_service.get_problem_sequence(problem_id)
    return sequence


def get_strategy_answer_list(student_index, student_count, problem_count):
    """题号：
        0：全错
        1：50%对
        2：80%对
        3：100对
        4:0~50%
        5:50%~80%
        6:80%~100%
        其余：无要求"""
    answer_list = [1] * problem_count
    answer_list[0] = 0
    # 0~50%段学生
    if student_index < 0.5*student_count and problem_count > 1:
        answer_list[1] = 0
        if random.randint(0, 1) == 0 and problem_count>4:
            answer_list[4] = 0
    # 50%~80%段学生
    elif student_index >= 0.5*student_count and student_index < 0.8*student_count:
        if problem_count > 4:
            answer_list[4] = 0
        if random.randint(0, 1) == 0 and problem_count > 5:
            answer_list[5] = 0
    # 80%~100%段学生
    else:
        if problem_count > 2:
            answer_list[2] = 0
        if problem_count > 4:
            answer_list[4] = 0
        if problem_count > 5:
            answer_list[5] = 0
        for problem_index in range(6, problem_count-1):
            if 0 == random.randint(0, 1):
                answer_list[problem_index] = 0
    return answer_list


def do_all_problem(homework_id, feedback_type, problem_count, strategy_answer_list, account):
    """做一套自习课任务的所有题目
    feedback_type: 0:部分完成 1:全部完成
    """
    problem_service = ProblemService()
    host = DomainMgr.get_domain("student_host")
    http_util = HttpConnectMgr.get_http_connect()
    if feedback_type == 0:
        problem_count = random.randint(0, problem_count-1)

    for problem_index in range(problem_count):
        sequence = get_problem_sequence(homework_id, problem_index+1)
        problem_type = problem_service.get_problem_type(sequence)
        strategy_answer = strategy_answer_list[problem_index]

        params = dict()
        params['currentIndexNo'] = problem_index
        params['pageNo'] = 1
        params['startTime'] = time.strftime("%Y-%m-%d %H:%M:%S.00")
        params['status'] = 'tHomework'
        params['homeworkId'] = homework_id
        params['indexNo'] = problem_index+1
        params['nextType'] = 0
        params['effective'] = 0     # 1:限时 0:不限时
        if problem_type == 0:
            right_answer = problem_service.get_right_answer(sequence)
            right_answer_str = problem_service.get_answer_str(right_answer)
            rand_wrong_answer_str = problem_service.get_answer_str(problem_service.get_rand_wrong_answer(right_answer))
            if strategy_answer == 1:
                params['answer'] = 1    # 1:正确 0:错误
                params['answerA'] = right_answer_str     # 选项ABCDE
            else:
                params['answer'] = 0
                params['answerA'] = rand_wrong_answer_str
        else:
            if strategy_answer == 1:
                params['answer'] = 1    # 1:正确 0:错误
                params['answerA'] = ""     # 选项ABCDE
            else:
                params['answer'] = 0
                params['answerA'] = ""

        res,res_code = http_util.get(host, "/web-student/teacherHomework/doHomeworkProblem", params)
        if re.search("错误报告", res):
            print("account=[%s],homework_id=[%s],index=[%d]self study feedback error" % (account, homework_id, problem_index))
            err_file_name = "self_study_error_%s_%s_%d.html" % (account, homework_id, problem_index)
            FileUtil.create_file(err_file_name, res)
        time.sleep(0.2)

if __name__ == "__main__":
    root_dir = FileUtil.get_app_root_dir()
    account_list = AccountMgr.get_account_list(root_dir+"/student/self_study.csv")
    student_service = StudentService()
    # 遍历配置
    for config_info in account_list:
        school_id = student_service.get_school_id(config_info[0])
        class_id = student_service.get_class_id(school_id, config_info[1])
        # 遍历各个分数段
        for section_index in range(5):
            feedback_info = config_info[section_index+2]
            # 获取到此分数段的学生列表
            student_list = student_service.get_student_list_by_section(school_id, class_id, section_index)
            if feedback_info != "":
                not_answer_rate = float(feedback_info.split('#')[0])
                part_answer_rate = float(feedback_info.split('#')[1])
                complete_answer_rate = float(feedback_info.split('#')[2])
                for student_index, student_info in enumerate(student_list):
                    login_param = dict()
                    login_param['loginName'] = student_info[0]
                    login_param['password'] = "123456"  # 使用了默认的密码 @warning
                    login_res,res_code = AccountMgr.login(login_param)
                    if re.search("错误报告", login_res):
                        print("[%s]login fail,please check you card and password" % student_info[0])
                        continue
                    homework_id = get_latest_homework_id()
                    if homework_id is not None:
                        problem_count = get_problem_count(homework_id)
                        strategy_answer_list = get_strategy_answer_list(student_index, len(student_list), problem_count)
                        not_answer_student = int(len(student_list) * not_answer_rate)
                        part_answer_student = int(len(student_list) * (part_answer_rate+not_answer_rate))
                        if student_index < not_answer_student:
                            print("section=%d,account=[%s],name=[%s],not answer" %
                                  (section_index, student_info[0],student_info[1]))
                        elif student_index >= not_answer_student \
                                and student_index < part_answer_student:
                            problem_count = random.randint(1, problem_count-1)
                            strategy_answer_list = get_strategy_answer_list(student_index,len(student_list),problem_count)
                            do_all_problem(homework_id, 0, problem_count, strategy_answer_list, student_info[0])
                            print("section=%d,account=[%s],name=[%s],partly answer,detail%s" %
                                  (section_index,student_info[0],student_info[1],str(strategy_answer_list)))
                        else:
                            do_all_problem(homework_id, 1, problem_count, strategy_answer_list, student_info[0])
                            print("section=%d,account=[%s],name=[%s],all answer,detail%s" %
                                  (section_index,student_info[0],student_info[1],str(strategy_answer_list)))
                    else:
                        print("section=%d,account=[%s],name=[%s],found no self study task" %
                              (section_index,student_info[0],student_info[1]))

                    AccountMgr.logout()
            else:
                for student_info in student_list:
                    print("section=%d,account=[%s],name=[%s],has no strategy,will not feedback" %
                          (section_index,student_info[0],student_info[1]))
    input("press enter to exit")


