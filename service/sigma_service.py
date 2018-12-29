#!/usr/bin/env python
# -*- coding:utf-8 -*-

from util.file_util import FileUtil
from util.mysql_util import MysqlUtil
from service.student_service import StudentService
from util.domain_mgr import IniUtil
import random

class SigmaService:
    def __init__(self):
        self.root_dir = FileUtil.get_app_root_dir()
        self.cur_env = FileUtil.get_cur_env()

    def get_course_id_by_name(self, course_name):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/sigma_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id  FROM `tbt_teacher_course` WHERE NAME ='"+course_name+"'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_gk_period_id_by_name(self, period_name,course_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/sigma_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tbs_gk1_review_course_period` " \
              "WHERE NAME ='"+period_name+"' And course_id="+str(course_id)+" AND status=1"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_course_name_by_id(self, id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/sigma_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT name  FROM `tbt_teacher_course_period` WHERE id ="+str(id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_problem_answer(self, id):
        """获取做题情况，查询`tbs_homework_problem`表
        -1：还没做过
        0：错
        1：对"""
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/sigma_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT is_right FROM `tbs_homework_problem` WHERE id ="+str(id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_student_pass_class_rank(self,class_id,course_id):
        """班级第几个通关某一关卡"""
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/sigma_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT count(*) FROM `tbs_student_pass_scoring_log` WHERE class_id ="+str(class_id)+" and course_id="+str(course_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        if len(data[0]) == 0:
            return 0
        else:
            return data[0][0]

    def get_student_pass_first_pass(self,student_id,course_id,):
        """是否首次通关某一个关卡"""
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/sigma_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT count(*) FROM `tbs_student_pass` " \
              "WHERE student_id ="+str(student_id)+" and index_no = 1 and status =1 " \
                                                   "and course_id="+str(course_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        if data[0][0] == 0:
            return True
        else:
            return False

    def get_student_pass_score(self,student_id):
        """基础攻关分数"""
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/sigma_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT scoring FROM `tbs_student_pass_scoring` WHERE student_id ="+str(student_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        if len(data) == 0 or len(data[0]) == 0:
            return 0
        else:
            return data[0][0]

    def get_mssw_course_type(self,course_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/sigma_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT data_type FROM `tbt_teacher_course` WHERE id ="+str(course_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_gk1_course_type(self,course_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/sigma_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT data_type FROM `tbs_gk1_review_course` WHERE id ="+str(course_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_strategy_answer_list(self,xz_count, student_level, problem_count):
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