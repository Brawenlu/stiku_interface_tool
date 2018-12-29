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
from service.student_service import StudentService
from service.problem_service import ProblemService
import re
import random
import codecs
import time


def get_paper_info(paper_id):
    root_dir = FileUtil.get_app_root_dir()
    cur_env = FileUtil.get_cur_env()
    mysql_util = MysqlUtil()
    conn = mysql_util.connect(cur_env, root_dir+"/config/stiku_db_config.ini")
    cursor = conn.cursor()
    sql = "SELECT tp.id,tp.type,tepp.problem_no,tepp.score,tepp.parent_id,tepp.group_sub_count " + \
          "FROM `tb_exam_paper_prom` AS tepp,`tb_problem` AS tp " + \
          "WHERE tepp.problem_id = tp.id  AND tepp.exam_paper_id =" + str(paper_id) + \
          " ORDER BY tepp.problem_no"
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    mysql_util.close()
    paper_info = []
    for problem_info in data:
        temp_info = dict()
        temp_info['id'] = problem_info[0]
        temp_info['type'] = problem_info[1]
        temp_info['index'] = problem_info[2]
        temp_info['score'] = problem_info[3]
        temp_info['parent_id'] = problem_info[4]
        temp_info['group_sub_count'] = problem_info[5]
        paper_info.append(temp_info)
    return paper_info


def get_level_score(subject_index, problem_info, xz_num, tk_num, jd_num, target_score_level):
    level_score = 0
    root_dir = FileUtil.get_app_root_dir()
    ini_util = IniUtil(root_dir + "/student/feedback_strategy.ini")
    level = "level_"+str(target_score_level)
    xz_dividing_rate = float(ini_util.get_item_attr(level, "xz_dividing_rate"))
    xz_high_score_rate = float(ini_util.get_item_attr(level, "xz_high_score_rate"))
    xz_low_score_rate = float(ini_util.get_item_attr(level, "xz_low_score_rate"))
    tk_dividing_rate = float(ini_util.get_item_attr(level, "tk_dividing_rate"))
    tk_high_score_rate = float(ini_util.get_item_attr(level, "tk_high_score_rate"))
    tk_low_score_rate = float(ini_util.get_item_attr(level, "tk_low_score_rate"))
    jd_dividing_rate = float(ini_util.get_item_attr(level, "jd_dividing_rate"))
    jd_high_score_rate = float(ini_util.get_item_attr(level, "jd_high_score_rate"))
    jd_low_score_rate = float(ini_util.get_item_attr(level, "jd_low_score_rate"))
    type = problem_info['type']
    total_score = problem_info['score']
    if type == 0:   #选择题
        if subject_index < int(xz_dividing_rate*xz_num):
            if random.random() < xz_high_score_rate:
                level_score = total_score
        else:
            if random.random() < xz_low_score_rate:
                level_score = total_score
    elif type == 1: #填空题
        if subject_index < int(tk_dividing_rate*tk_num):
            if random.random() < tk_high_score_rate:
                level_score = total_score
        else:
            if random.random() <tk_low_score_rate:
                level_score = total_score
    elif type == 2: #解答题
        if subject_index < int(jd_dividing_rate*jd_num):
            if random.random() < jd_high_score_rate:
                level_score = int(total_score*random.uniform(jd_high_score_rate, 1))
            else:
                level_score = int(total_score*random.uniform(0, jd_high_score_rate))
        else:
            if random.random() < jd_low_score_rate:
                level_score = int(total_score*random.uniform(jd_high_score_rate, 1))
            else:
                level_score = int(total_score*random.uniform(0, jd_low_score_rate))
    return level_score


def get_problem_score(subject_index, problem_info, xz_num, tk_num, jd_num, target_score_level):
    problem_score = 0
    if target_score_level == '0':
        problem_score = 0
    elif target_score_level == '100':
        problem_score = problem_info['score']
    else:
        problem_score = get_level_score(subject_index, problem_info, xz_num, tk_num, jd_num, target_score_level)
    return problem_score


def get_subject_index(index, type, xz_num, tk_num):
    subject_index = 0
    if type == 0:
        subject_index = index
    elif type == 1:
        subject_index = index - xz_num
    elif type == 2:
        subject_index = index - xz_num - tk_num
    return subject_index


def get_subject_index_str(subject_index):
    return "第" + str(subject_index) + "题"


def get_type_str(type):
    type_str = ""
    if type == 0:
        type_str = "选择题"
    elif type == 1:
        type_str = "填空题"
    elif type == 2:
        type_str = "解答题"
    return type_str


def get_type_subject_num(paper_info):
    xz_num, tk_num, jd_num = 0, 0, 0
    for problem_info in paper_info:
        if problem_info['type'] == 0:
            xz_num = xz_num + 1
        elif problem_info['type'] == 1:
            tk_num = tk_num + 1
        elif problem_info['type'] == 2:
            jd_num = jd_num + 1
    return xz_num, tk_num, jd_num


def parse_problem_parent_id(problem_info):
    parent_id = problem_info['parent_id']
    if parent_id is not None:
        return str(parent_id)
    else:
        return str(problem_info['id'])


def parse_problem_sub_count(problem_info):
    if problem_info['group_sub_count'] is not None:
        return str(problem_info['group_sub_count'])
    else:
        return '1'


def get_feedback_result(paper_name, target_score_level):
    problem_service = ProblemService()
    paper_id = problem_service.get_paper_id(paper_name)
    feedback_result = list()
    feedback_result.append(('paper_id', paper_id))
    paper_info = get_paper_info(paper_id)
    xz_num, tk_num, jd_num = get_type_subject_num(paper_info)

    total_score = 0
    for problem_info in paper_info:
        subject_index = get_subject_index(problem_info['index'], problem_info['type'], xz_num, tk_num)
        problem_socre = get_problem_score(subject_index, problem_info, xz_num, tk_num, jd_num, target_score_level)
        total_score += problem_socre
        problem_seq_str = str(problem_info['id']) + '_' \
                          + str(problem_socre) + '_' \
                          + str(problem_info['index']) + '_' \
                          + str(problem_info['score']) + '_' \
                          + parse_problem_parent_id(problem_info) + '_'\
                          + parse_problem_sub_count(problem_info)
        group_count_sel = get_type_str(problem_info['type']) + get_subject_index_str(subject_index)
        feedback_result.append(('problemId', problem_seq_str))
        feedback_result.append(('group_count_sel', group_count_sel))
    return feedback_result,total_score


if __name__ == "__main__":
    root_dir = FileUtil.get_app_root_dir()
    student_service = StudentService()
    account_list = AccountMgr.get_account_list(root_dir+"/student/paper_feedback_by_class.csv")
    student_service = StudentService()
    problem_service = ProblemService()
    for config_info in account_list:
        log_name = config_info[0]+"_"+config_info[1]+"_"+config_info[2]+"_"+time.strftime("%Y_%m_%d")+".txt"
        file_obj = codecs.open(log_name, "w", encoding="utf-8")
        school_id = student_service.get_school_id(config_info[0])
        class_id = student_service.get_class_id(school_id, config_info[1])
        all_feed_back_count = 0
        actual_feed_back_count = 0
        paper_name = config_info[2]
        paper_id = problem_service.get_paper_id(paper_name)
        # 遍历各个分数段
        for section_index in range(5):
            # 获取到此分数段的学生列表
            student_list = student_service.get_student_list_by_section(school_id, class_id, section_index)

            for student_index, student_info in enumerate(student_list):
                login_param = dict()
                login_param['loginName'] = student_info[0]
                login_param['password'] = "123456"  # 使用了默认的密码 @warning
                login_res,res_code = AccountMgr.login(login_param)
                student_id = student_service.get_student_id(student_info[0])
                if re.search("错误报告", login_res):
                    print("[%s]login fail,please check you card and password" % student_info[0])
                    continue
                else:
                    all_feed_back_count += 1
                student_profile = student_service.get_student_profile_info(student_info[0])
                student_level = student_profile[6]
                if student_level is None:
                    student_level = 3
                else:
                    student_level += 1
                total_score = problem_service.get_paper_feedback_score(paper_id,student_id)
                if total_score is None:
                    feedback_result_params,total_score = get_feedback_result(paper_name,student_level)
                    http_util = HttpConnectMgr.get_http_connect()
                    host = DomainMgr.get_domain("student_host")
                    feedback_result = http_util.post(host, "/web-student/studentPaper/feedback", feedback_result_params)
                    if re.search("错误报告", feedback_result):
                        input("feedback error,account="+student_info[0]+",paper="+paper_name)
                        continue
                    print("account=[%s],paper=[%s]feedback succeed,expect=[%s],total=[%d]" %
                          (student_info[0], paper_name, student_level, total_score))
                else:
                    print("account=[%s],paper=[%s]feedback succeed,expect=[%s],total=[%d]" %
                          (student_info[0], paper_name, student_level, total_score))
                AccountMgr.logout()
        print("school=[%s],class=[%s],paper=[%s],all_feedback=[%d]" %
              (config_info[0],config_info[1],config_info[2],all_feed_back_count))
    input("press enter to exit")