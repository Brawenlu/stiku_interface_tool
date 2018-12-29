#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
import re
import time
from util.account_mgr import AccountMgr
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
from util.file_util import FileUtil
from service.problem_service import ProblemService


def do_all_problem_wrong(account, homework_id, expect_count):
    problem_service = ProblemService()
    host = DomainMgr.get_domain("student_host")
    http_util = HttpConnectMgr.get_http_connect()
    all_problem_count = problem_service.get_homework_cout(homework_id)
    done_problem_count = problem_service.get_homework_problem_done_count(account, homework_id)
    problem_count = all_problem_count - done_problem_count

    if problem_count > expect_count:
        problem_count = expect_count
    for problem_index in range(done_problem_count, (done_problem_count + problem_count)):
        params = dict()
        params['currentIndexNo'] = problem_index
        params['pageNo'] = 1
        params['startTime'] = time.strftime("%Y-%m-%d %H:%M:%S.00")
        params['status'] = 'tHomework'
        params['homeworkId'] = homework_id
        params['indexNo'] = problem_index+1
        params['nextType'] = 0
        params['effective'] = 0     # 1:限时 0:不限时
        params['answer'] = 0
        params['answerA'] = "E"
        http_util.get(host, "/web-student/teacherHomework/doHomeworkProblem", params)
    return problem_count

"""错题本数据库表：tb_error_subject_library"""
if __name__ == "__main__":
    root_dir = FileUtil.get_app_root_dir()
    account_list = AccountMgr.get_account_list(root_dir+"/student/wrong_book.csv")
    problem_service = ProblemService()
    for account in account_list:
        login_param = dict()
        login_param['loginName'] = account[0]
        login_param['password'] = account[1]
        login_res,res_code = AccountMgr.login(login_param)
        if re.search("错误报告", login_res):
            print("[%s]login fail,please check you card and password" % account[0])
            continue
        http_util = HttpConnectMgr.get_http_connect()
        host = DomainMgr.get_domain("student_host")
        homework_list = problem_service.get_undo_homework_list(account[0])
        add_count = 0
        expect_count = int(account[2])
        pre_error_problem_count = problem_service.get_error_problem_count(account[0])
        for homework in homework_list:
            if add_count < expect_count:
                left_count = expect_count - add_count
                wrong_count = do_all_problem_wrong(account[0], homework[0], left_count)
                add_count += wrong_count
        now_error_problem_count = problem_service.get_error_problem_count(account[0])
        if add_count < expect_count:
            print("account[%s],lack exercise,please arrange him some self_study_exercise" % account[0])
        print("account=[%s],wrong book added[%d],curr_items[%d]" %
              (account[0], add_count, now_error_problem_count))
        AccountMgr.logout()
    input("press enter to exit")
