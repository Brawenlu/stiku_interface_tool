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
from service.problem_service import ProblemService


def get_homework_problem_list(account, problem_count):
    problem_service = ProblemService()
    problem_list = problem_service.get_homework_problem_list(account, problem_count)
    return problem_list

if __name__ == "__main__":
    root_dir = FileUtil.get_app_root_dir()
    account_list = AccountMgr.get_account_list(root_dir+"/student/collect_item.csv")
    problem_service = ProblemService()
    for account in account_list:
        login_param = dict()
        login_param['loginName'] = account[0]
        login_param['password'] = account[1]
        login_res,res_code = AccountMgr.login(login_param)
        if re.search("错误报告", login_res):
            print("[%s]login fail,please check your card and password" % account[0])
            continue
        http_util = HttpConnectMgr.get_http_connect()
        host = DomainMgr.get_domain("student_host")
        homework_problem_list = problem_service.get_uncollected_problem_list(account[0], account[2] or 10)
        pre_collect_count = problem_service.get_collected_problem_count(account[0])
        for problem in homework_problem_list:
            if not problem_service.get_if_problem_has_collected(account[0], problem[0]):
                params = dict()
                params['problemId'] = problem[0]
                params['collection'] = 1
                http_util.post(host, "/web-student/favorite/doCollection", params)
        if len(homework_problem_list) < int(account[2]):
            print("account[%s],lack exercises,please arrange him a self-study test" % account[0])
        cur_collect_count = problem_service.get_collected_problem_count(account[0])

        print("account=[%s],wrong book added exercise num %d,now total exercises%d" %
              (account[0], (cur_collect_count-pre_collect_count), cur_collect_count))
        AccountMgr.logout()
    input("press enter to exit")
