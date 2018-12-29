#!/usr/bin/env python
# -*- coding:utf-8 -*-

from util.file_util import FileUtil
from util.mysql_util import MysqlUtil
import time


class StudentService:
    def __init__(self):
        self.root_dir = FileUtil.get_app_root_dir()
        self.cur_env = FileUtil.get_cur_env()

    def get_school_id(self, school_name):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tb_school` WHERE NAME = '" + school_name + "'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return int(data[0][0])

    def get_school_name(self, school_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT name FROM `tb_school` WHERE id =" + str(school_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_student_school_id(self, account):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT school_id FROM `tb_student` WHERE card_num='"+account+"'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return int(data[0][0])

    def get_student_grade_year(self, account):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT grade_year FROM `tb_student` WHERE card_num='"+account+"'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return int(data[0][0])

    def get_class_id(self, school_id, class_name):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tb_class` WHERE school_id ="+str(school_id)+" AND name="+class_name
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return int(data[0][0])

    def get_student_list(self, school_id, class_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id,card_num,real_name,student_section " \
              "FROM `tb_student` " \
              "WHERE school_id ="+str(school_id)+" AND class_id="+str(class_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_student_list_by_section(self, school_id, class_id, section):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = ""
        #系统默认被分到第三等(0,1,2,3,4)
        if(section != 2):
            sql = "SELECT card_num,real_name,id,student_section " \
                  "FROM `tb_student` " \
                  "WHERE school_id ="+str(school_id)+\
                  " AND class_id="+str(class_id) + \
                  " AND student_section = "+str(section)
        else:
            sql = "SELECT card_num,real_name,id,student_section " \
                  "FROM `tb_student` " \
                  "WHERE school_id ="+str(school_id)+\
                  " AND class_id="+str(class_id) + \
                  " AND (student_section = "+str(section)+" or student_section IS NULL)"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_student_id(self, user_card):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tb_student` WHERE card_num='" + user_card + "'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_user_id(self, user_card):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tbl_auth_user` WHERE sign_name='" + user_card + "'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_student_profile_info(self, user_card):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT school_id,class_id,real_name,sex,phone_num,qq_number,student_section,parent_name,parent_telephone,target,motto,id,grade_year " \
              "FROM `tb_student` WHERE card_num='" + user_card + "'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0]

    def get_student_profile_info_by_id(self, user_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT school_id,class_id,real_name,sex,phone_num,qq_number,student_section,parent_name,parent_telephone,target,motto " \
              "FROM `tb_student` WHERE id='" + str(user_id) + "'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0]

    def get_class_info(self, class_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT grade_year,type,name FROM `tb_class` WHERE id=" + str(class_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0]

    def get_t18_students(self):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT * FROM `tb_student` WHERE card_num LIKE 't18%' ORDER BY card_num"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_t18_classes(self):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT * FROM `tb_class` WHERE school_id = 685 AND (grade_year=2015 OR grade_year = 2014)"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_bjcs_students(self):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT * FROM `tb_student` WHERE school_id = 692"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_all_grade_3_student_info(self):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        cur_year = time.localtime().tm_year
        cur_month = time.localtime().tm_mon
        grade_3_grade = 0
        if cur_month >= 9:
            grade_3_grade = cur_year - 2
        else:
            grade_3_grade = cur_year - 3
        sql = "SELECT id,card_num,s_type FROM `tb_student` where class_id=3371 AND grade_year="+str(grade_3_grade)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data