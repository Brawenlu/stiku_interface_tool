#!/usr/bin/env python
# -*- coding:utf-8 -*-

from util.file_util import FileUtil
from util.mysql_util import MysqlUtil
from service.student_service import StudentService
import random

class ProblemService:
    def __init__(self):
        self.root_dir = FileUtil.get_app_root_dir()
        self.cur_env = FileUtil.get_cur_env()

    def get_all_problem_ids(self):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tb_problem` order by id"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_all_xz_problems(self):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id,sequence,content FROM `tb_problem` WHERE content!=\"\" AND type=0 " \
              "AND created_dt>'2016-01-01 06:01:01'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_right_answer_by_id(self, id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT answer FROM `tb_problem` WHERE id = "+str(id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_right_answer(self, sequence):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT answer FROM `tb_problem` WHERE sequence = "+str(sequence)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()

        return int(data[0][0])

    def get_problem_type_by_id(self, id):
        """ 0：选择
            1:填空
            2：解答"""
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT type FROM `tb_problem` WHERE id = "+str(id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return int(data[0][0])

    def get_problem_type(self, sequence):
        """ 0：选择
            1:填空
            2：解答"""
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT type FROM `tb_problem` WHERE sequence = "+str(sequence)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return int(data[0][0])

    def get_homework_cout(self, homework_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT COUNT(*) FROM `tb_homework_problem` WHERE homework_id = '"+homework_id+"'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return int(data[0][0])

    def get_homework_problem_list(self, account, count):
        student_service = StudentService()
        student_id = student_service.get_student_id(account)
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT problem_id FROM `tb_homework_problem` WHERE student_id = '"+str(student_id)+"' limit "+str(count)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_uncollected_problem_list(self, account, count):
        student_service = StudentService()
        student_id = student_service.get_student_id(account)
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT problem_id FROM `tb_homework_problem` WHERE student_id ="+str(student_id)+" AND problem_id NOT IN " \
            "(SELECT problem_id FROM `tb_problem_collect` WHERE student_id ="+str(student_id)+" AND collect=1) limit "+str(count)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_undo_homework_list(self, account):
        student_service = StudentService()
        student_id = student_service.get_student_id(account)
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT DISTINCT(homework_id) FROM `tb_homework_problem` " \
              "WHERE student_id = '"+str(student_id)+"' AND updated_dt IS NULL "
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_error_problem_count(self, account):
        student_service = StudentService()
        student_id = student_service.get_student_id(account)
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT COUNT(*) FROM `tb_error_subject_library` WHERE student_id = '"+str(student_id)+"'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        count = 0
        try:
            count = int(data[0][0])
        except:
            pass
        return count

    def get_homework_problem_done_count(self, account, homework_id):
        student_service = StudentService()
        student_id = student_service.get_student_id(account)
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT COUNT(*) FROM `tb_homework_problem` " \
              "WHERE homework_id = '"+str(homework_id)+"' AND student_id = "+str(student_id)+" AND updated_dt IS NOT NULL"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return int(data[0][0])

    def get_homework_problem_id(self, homework_id, index):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT problem_id FROM `tb_homework_problem` WHERE " \
              "homework_id='"+str(homework_id)+"' AND index_no="+str(index)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_collected_problem_count(self, account):
        student_service = StudentService()
        student_id = student_service.get_student_id(account)
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT COUNT(*) FROM `tb_problem_collect` " \
              "WHERE student_id ="+str(student_id)+" AND collect=1"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return int(data[0][0])

    def get_problem_sequence(self, problem_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT sequence FROM `tb_problem` WHERE id="+str(problem_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_if_problem_has_collected(self, account, problem_id):
        student_service = StudentService()
        student_id = student_service.get_student_id(account)
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT collect FROM `tb_problem_collect` " \
              "WHERE student_id = "+str(student_id)+" AND problem_id = "+str(problem_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()

        if len(data) == 0 or data[0][0] == 0:
            return False
        else:
            return True

    def get_stu_week_test_task_id(self, student_id, teacher_week_test_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tb_week_test` " \
              "WHERE student_id="+str(student_id)+" AND teacher_week_test_id="+str(teacher_week_test_id)+\
              " ORDER BY begin_date DESC"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        if len(data) == 0:
            return None
        return data[0][0]

    def get_week_test_id(self, week_test_name, student_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tb_week_test` WHERE student_id="+str(student_id)+" AND name='"+week_test_name+"' ORDER BY begin_date desc"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        if len(data) == 0:
            return None
        return data[0][0]

    def get_week_test_info(self, week_test_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT * FROM `tb_week_test` WHERE id="+str(week_test_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0]

    def get_week_test_problem_info(self, week_test_id, index):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id,problem_id,index_no,score,is_grasp,grasp_score,student_grasp_score,first_index,all_count,choose_count,student_choose FROM `tb_week_test_problem` WHERE week_test_id="+str(week_test_id)+" AND index_no='"+str(index)+"'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0]

    def get_week_test_status(self, week_test_id, class_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT status from `tbt_teacher_week_test` where week_test_id="+str(week_test_id)+" and class_id="+str(class_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        if len(data) < 1:
            return 0
        return data[0][0]

    def get_week_test_count(self, week_test_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT COUNT(*) FROM `tb_week_test_problem` WHERE week_test_id="+str(week_test_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_stu_week_test_score(self, week_test_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT SUM(student_grasp_score) FROM `tb_week_test_problem` WHERE week_test_id="+str(week_test_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_week_test_grasp(self,problem_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT is_grasp FROM `tb_week_test_problem` WHERE id="+str(problem_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    # ============ tb_exam_paper ==================
    def get_paper_id(self,paper_name):
        root_dir = FileUtil.get_app_root_dir()
        cur_env = FileUtil.get_cur_env()
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(cur_env, root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tb_exam_paper` WHERE name='" + paper_name + "'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_need_ajax_down_test_paper(self):
        root_dir = FileUtil.get_app_root_dir()
        cur_env = FileUtil.get_cur_env()
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(cur_env, root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "select id,pdf_url_at_last,pdf_url_no_answer from tb_exam_paper WHERE pdf_url_at_last is NOT null OR pdf_url_no_answer is NOT null"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_paper_feedback_score(self, paper_id,student_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT count_score FROM `tb_student_paper` WHERE paper_id="+str(paper_id)+\
              " AND student_id="+str(student_id)+" AND feedback_status=2"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        if len(data) < 1:
            return None
        return data[0][0]

    def get_stu_week_test_problem_id(self, week_test_id, t_problem_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tb_week_test_problem` WHERE week_test_id="+str(week_test_id)+" AND problem_id='"+str(t_problem_id)+"'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_week_test_paper_problem_id(self, week_test_id, index):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT problem_id FROM `tb_week_test_problem` WHERE week_test_id="+str(week_test_id)+" AND index_no='"+str(index)+"'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_cur_max_homework_id(self):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT MAX(id) FROM `tbt_teacher_new_homework`"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_max_autotest_week_test_name_index(self):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT exampaper_name FROM `tbt_weektest_work` WHERE exampaper_name LIKE '自动化测试%' ORDER BY id DESC"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        if len(data) > 0:
            exampaper_name = data[0][0]
            paper_name_index = exampaper_name[5:]
            return int(paper_name_index)
        else:
            return 0

    """根据关联的教材版本获取章节信息"""
    def get_chapter_info_by_class(self,school_id,subject_type,grade_year):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = " SELECT id,name,book_id FROM `tb_book_point` AS tbp WHERE tbp.parent_id IS NULL AND book_id IN" \
              "(SELECT tb.id FROM `tb_book` AS tb,`tb_book_sort` AS tbs " \
                "WHERE tbs.tb_book_id = tb.id AND tbs.school_id = "+str(school_id)+\
                    " AND tbs.subject_type="+str(subject_type)+" AND tbs.grade_year="+str(grade_year)+")"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    """获取人教a的章节信息"""
    def get_chapter_info_from_rja(self):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = " SELECT id,name,book_id FROM `tb_book_point` AS tbp WHERE tbp.parent_id IS NULL AND book_id IN" \
              "(SELECT tb.id FROM `tb_book` AS tb WHERE TYPE ='math_rja')"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_week_test_work_id(self,week_test_name):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tbt_weektest_work` WHERE exampaper_name = '"+week_test_name+"' ORDER BY id DESC"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_week_test_exam_paper_id(self, week_test_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT exampaper_id FROM `tbt_weektest_work` WHERE id = "+str(week_test_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_week_test_work_class_id(self, week_test_id, class_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tbt_weektest_work_class` WHERE tbt_weektest_work_id="+str(week_test_id)+" AND class_id="+str(class_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_week_test_problem_list(self, teacher_week_test_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT problem_id FROM `tbt_weektest_work_problem` WHERE tbt_weektest_work_id="+str(teacher_week_test_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    # ============ tb_video_zhenduan ==================
    def get_all_jiexi_video(self):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT tv.problem_id,tv.url,tv.aliyun_oss_key FROM `tb_problem` AS tp,`tb_video_zhenduan` AS tv WHERE tv.problem_id=tp.id AND tv.dr=0 AND tv.flag=1 AND tv.source=0"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_problem_video_info(self, problem_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id,url,aliyun_oss_key FROM `tb_video_zhenduan` where problem_id="+\
              str(problem_id)+" AND dr=0 AND flag=1"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        if len(data) > 0:
            return data
        else:
            return 0

    # ============ tb_problem_model_prom ==================
    def get_problem_model_prom_problem_ids(self):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT DISTINCT(problem_id) FROM `tb_problem_model_prom` "
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    # ============ tb_problem_model_prom ==================
    def get_tb_book_sort_id(self, school_id, grade_year, tb_book_id, subject_type):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tb_book_sort` WHERE school_id ="+str(school_id)+" AND grade_year = "+str(grade_year)+" AND tb_book_id="+str(tb_book_id)+" AND subject_type="+str(subject_type)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0][0]

    def get_tb_book_sort_list(self, school_id, grade_year, subject_type):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `tb_book_sort` WHERE school_id ="+str(school_id)+" AND grade_year = "+str(grade_year)+" AND subject_type="+str(subject_type)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    # ============ tb_homework_consolidate_problem ==================
    def get_student_consolidate_problems(self, student_homework_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id,problem_id FROM `tb_homework_consolidate_problem` WHERE homework_id=`"+str(student_homework_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    # ============ tbt_teacher_consolidate_problem ==================
    def get_teacher_consolidate_problems(self, teacher_homework_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id,problem_id,consolidate_id FROM `tbt_teacher_consolidate_problem` WHERE teacher_homework_id="+str(teacher_homework_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    # ============ tb_homework_recommend_problem ==================
    def get_homework_recommend_problems(self, homework_id, problem_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT * FROM `tb_homework_recommend_problem` WHERE homework_id="+str(homework_id)+" AND source_id="+str(problem_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    # ============ tb_homework ==================
    def get_student_homework_info(self, teacher_homework_id, student_id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id,name FROM `tb_homework` WHERE teacher_homework_id="+str(teacher_homework_id)+" AND student_id="+str(student_id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data[0]


    # ============ tb_point_domain ==================
    def get_all_point_domain_info(self):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id,name,parent_id FROM `tb_point_domain` WHERE type=2"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    def get_point_domain(self, id):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect(self.cur_env, self.root_dir+"/config/stiku_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT name,parent_id FROM `tb_point_domain` WHERE id="+str(id)
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        return data

    @staticmethod
    def get_rand_wrong_answer(right_answer, answers=None):
        answers = answers or (1, 10, 100, 1000, 0)
        wrong_answers = [answer for answer in answers if answer != right_answer]
        return wrong_answers[random.randint(0,len(wrong_answers)-1)]

    @staticmethod
    def get_answer_str(answer):
        answer_str = ""
        if answer == 1:
            answer_str = "A"
        elif answer == 10:
            answer_str = "B"
        elif answer == 100:
            answer_str = "C"
        elif answer == 1000:
            answer_str = "D"
        else:
            answer_str = "E"
        return answer_str