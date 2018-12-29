#!/usr/bin/env python
# -*- coding:utf-8 -*-

from util.file_util import *
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
from util.log import logger
import random
import copy
import time
import types
import re
import datetime

class CommonFun:
    @staticmethod
    def get_rand_n_value(all_list,count):
        cur_list = copy.copy(all_list)
        rand_n_num = list()
        for i in range(count):
            rand_num = random.randint(0, (len(cur_list)-1))
            rand_n_num.append(cur_list[rand_num])
            del cur_list[rand_num]
        return rand_n_num

    """
    student_level:1~5
    """
    @staticmethod
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

    @staticmethod
    def get_rand_n_num(all_count,choose_count):
        cur_list = [i for i in range(all_count)]
        rand_n_num = list()
        for i in range(choose_count):
            rand_num = random.randint(0, (len(cur_list)-1))
            rand_n_num.append(cur_list[rand_num])
            del cur_list[rand_num]
        return rand_n_num

    @staticmethod
    def get_grade_year_str(grade_year):
        grade_year_str = ""
        cur_year = time.localtime().tm_year
        if cur_year - grade_year == 1:
            grade_year_str = "高一"
        elif cur_year - grade_year == 2:
            grade_year_str = "高二"
        else:
            grade_year_str = "高三"
        return grade_year_str

    @staticmethod
    def get_grade_type(grade_year):
        cur_year = time.localtime().tm_year
        return cur_year - grade_year

    @staticmethod
    def get_kq_paper_type_name(paper_type):
        kq_paper_type_name = ""
        if paper_type == 1:
            kq_paper_type_name = "月考"
        elif paper_type == 2:
            kq_paper_type_name = "期中考"
        elif paper_type == 3:
            kq_paper_type_name = "期末考"
        return kq_paper_type_name

    @staticmethod
    def get_subject_type_name(subject_type):
        subject_type_name = ""
        if subject_type == 1:
            subject_type_name = "文科"
        else:
            subject_type_name = "理科"
        return subject_type_name

    @staticmethod
    def get_next_n_day_date(format, day_between):
        next_n_day = int(time.time()) + 24*60*60*day_between
        next_n_day_date = time.strftime(format, time.localtime(next_n_day))
        return next_n_day_date

    @staticmethod
    def get_utc_to_local_time(utc_time_str):
        utc_dt = datetime.datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        utc_dt = utc_dt + datetime.timedelta(hours=8)
        local_time_str = utc_dt.strftime("%Y-%m-%d %H:%M:%S:%f")
        return local_time_str

    @staticmethod
    def test_interface(host, interface, method, param, vertify, vertify_param=None):
        http_util = HttpConnectMgr.get_http_connect()
        res, res_code = "", 0
        if method == "get":
            res, res_code = http_util.get(host, interface, param)
        else:
            res, res_code = http_util.post(host, interface, param)
        if res_code != 200:
            logger.error("%s 返回码错误%s", interface, res_code)
            return False
        if isinstance(vertify, str):
            if not re.search(vertify, str(res)):
                logger.error("%s 接口验证失败", interface)
                logger.error("请求链接：%s", http_util.get_url())
                logger.error("接口请求参数：%s", param)
                logger.error("接口返回信息：%s", res)
                return False
        elif hasattr(vertify,'__call__'):
            if not vertify(interface, res, vertify_param):
                logger.error("%s 接口验证失败", interface)
                logger.error("请求链接：%s",http_util.get_url())
                logger.error("接口请求参数：%s", param)
                logger.error("接口返回信息：%s", res)
                return False
        logger.debug("%s 接口验证通过", interface)
        return True