#!/usr/bin/env python
# -*- coding:utf-8 -*-

from util.file_util import FileUtil
from util.mysql_util import MysqlUtil


class CommonService:
    def __init__(self):
        self.root_dir = FileUtil.get_app_root_dir()
        self.cur_env = FileUtil.get_cur_env()

    def get_teacher_id_by_account(self, account):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT tt.id FROM `tbt_teacher` AS tt,`tbl_auth_user` AS tau " \
              "WHERE tt.user_id=tau.id AND tau.sign_name='"+account+"'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return int(data[0][0])

    def get_teacher_teaching_classes(self, teacher_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT class_id FROM `tbt_teacher_class` WHERE teacher_id="+str(teacher_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_school_id_by_teacher_id(self,teacher_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT school_id FROM `tbt_teacher` WHERE id="+str(teacher_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]


    def get_grade_year_by_class_id(self, class_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT grade_year FROM `tb_class` WHERE id="+str(class_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

