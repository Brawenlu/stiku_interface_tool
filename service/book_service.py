#!/usr/bin/env python
# -*- coding:utf-8 -*-

from util.file_util import FileUtil
from util.mysql_util import MysqlUtil
from service.student_service import StudentService
import random

class BookService:
    def __init__(self):
        self.root_dir = FileUtil.get_app_root_dir()
        self.cur_env = FileUtil.get_cur_env()

    def get_school_book_sort_list(self, school_id, grade_year, subject_type):
        """查某学校某年级某文理科的教材"""
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT * FROM `tb_book_sort` WHERE school_id = "+str(school_id)+" AND grade_year="+str(grade_year)+" AND subject_type = "+str(subject_type)+" ORDER BY fd_order"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_school_bookpoint_sort_list(self, book_sort_id):
        """查教材下的章"""
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT * FROM `tb_book_point_sort` WHERE tb_book_sort_id="+str(book_sort_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_bookpoint_list(self, book_point_id):
        """查章下的知识点"""
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT * FROM `tb_book_point` WHERE parent_id = "+str(book_point_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data



