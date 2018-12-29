#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
from util.file_util import FileUtil
from util.account_mgr import AccountMgr
from util.file_util import IniUtil
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
from util.interface_mgr import InterfaceMgr
from util.week_test_util import WeekTestUtil
from util.common_fun import CommonFun
from service.student_service import StudentService
from service.problem_service import ProblemService
from service.common_service import CommonService
import re
import random
import time
import json
import copy
from util.log import logger

PROBLEM_NUM = 10
TARGET = "自动化测试寄语"

class SelfStudyProcess:
    def __init__(self):
        root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(root_dir + "/config/teacher_account.ini")
        cur_env = FileUtil.get_cur_env()
        self.http_util = HttpConnectMgr.get_http_connect()
        self.teacher_host = DomainMgr.get_domain("teacher_host")
        self.student_host = DomainMgr.get_domain("student_host")
        self.sigma_student_host = DomainMgr.get_domain("sigma_student_host")
        self.student_service = StudentService()
        self.problem_service = ProblemService()
        self.teacher_account = ini_util.get_item_attr(cur_env, "user")
        self.teacher_password = ini_util.get_item_attr(cur_env, "password")
        self.teacher_id = 0
        self.student_account = ""
        self.student_password = "123456"
        self.student_id = 0
        self.student_name = ""
        self.select_book_sort_id = 0
        self.stu_task_id = 0
        self.student_score = 0
        self.school_id = 0
        self.class_id = 0
        self.subject_type = 0
        self.class_name = 0
        self.grade_year = 0
        self.token = ""
        self.paper_name = ""
        self.homework_problem_count = 0
        self.consolidate_problem_count = 0
        self.teacher_homework_id = 0
        self.student_homework_id = 0
        self.student_homework_name = ""
        self.chapter_list = []
        self.problem_list_data = []
        self.select_problem_id = 0
        self.teacher_consolidate_id = 0
        self.select_tb_book_section_id = 0
        self.select_tb_book_id = 0
        self.select_tb_book_point_id = 0

    @staticmethod
    def interface_ok(interface):
        logger.info("%s接口正常", interface)

    @staticmethod
    def http_code_error(interface, code):
        logger.error("%s返回码%s", interface, code)

    @staticmethod
    def page_load_error(interface):
        logger.error("%s页面加载错误", interface)

    def login(self, account, password):
        login_param = dict()
        login_param['loginName'] = account
        login_param['password'] = password
        login_res, login_code = AccountMgr.login(login_param)
        if re.search("错误报告", login_res):
            logger.error("(%s)login fail,please check you card and password" % account)
            return False
        return True

    def vertify_get_chapter_info(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["success"] is False:
            return False
        self.chapter_list = response_json["chapaterList"]
        return True

    def vertify_get_problem_info(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["success"] is False:
            return False
        self.problem_list_data = response_json["problemListData"]
        return True

    def vertify_get_basket_info(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if len(response_json["homeworkTitleList"]) > 0:
            return True
        return False

    def vertify_common(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["success"] is True:
            return True
        return False

    def vertify_answer_consolidate(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if response_json["code"] != 1:
            return False
        return True

    def vertify_student_answer_situation(self, interface, response, vertify_param):
        response_json = json.loads(response)
        if len(response_json["data"]) > 0:
            return True
        return False

    def get_class_info(self, teacher_account):
        common_service = CommonService()
        self.teacher_id = common_service.get_teacher_id_by_account(teacher_account)
        self.school_id = common_service.get_school_id_by_teacher_id(self.teacher_id)
        tbt_class_info = common_service.get_teacher_teaching_classes(self.teacher_id)
        self.class_id = tbt_class_info[0][0]
        class_info = self.student_service.get_class_info(self.class_id)
        self.grade_year = class_info[0][0]
        self.subject_type = class_info[0][1]
        self.class_name = class_info[0][2]

    def get_homework_xz_count(self, problem_count):
        xz_count = 0
        for problem_index in range(problem_count):
            paper_problem_id = self.problem_service.get_homework_problem_id(self.student_homework_id,problem_index+1)
            problem_type = self.problem_service.get_problem_type_by_id(paper_problem_id)
            if problem_type == 0:
                xz_count += 1
        return xz_count

    def do_all_problem(self, homework_id, problem_count):
        """做一套自习课任务的所有题目
        """
        strategy_answer = 0
        for problem_index in range(problem_count):
            problem_id = self.problem_service.get_homework_problem_id(homework_id, problem_index+1)
            problem_type = self.problem_service.get_problem_type_by_id(problem_id)

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
                right_answer = self.problem_service.get_right_answer_by_id(problem_id)
                right_answer_str = self.problem_service.get_answer_str(right_answer)
                rand_wrong_answer_str = self.problem_service.get_answer_str(self.problem_service.get_rand_wrong_answer(right_answer))
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
            do_homework_problem = InterfaceMgr.get_interface("web_student", "do_homework_problem")
            if not CommonFun.test_interface(self.student_host, do_homework_problem, "get", params, "做题界面"):
                return False
            time.sleep(0.2)
        return True

    def do_all_consolidate(self, homework_id):
        consolidate_problems = self.problem_service.get_student_consolidate_problems(homework_id)
        problem_count = len(consolidate_problems)
        for problem_index in range(problem_count):
            consolidate_problem = consolidate_problems[problem_index]
            consolidate_id = consolidate_problem[0]
            problem_id = consolidate_problem[1]
            problem_type = self.problem_service.get_problem_type_by_id(problem_id)
            strategy_answer = random.randint(0,1)
            params = dict()
            params["homeworkId"] = homework_id
            params["cpId"] = consolidate_id
            params["startTime"] = time.strftime("%Y-%m-%d %H:%M:%S.00")
            if problem_type == 0:
                right_answer = self.problem_service.get_right_answer_by_id(problem_id)
                rand_wrong_answer = self.problem_service.get_rand_wrong_answer(right_answer,(1, 10, 100, 1000, 2))
                if strategy_answer == 1:
                    params['sAnswer'] = right_answer    # 1:正确 0:错误
                else:
                    params['sAnswer'] = rand_wrong_answer
            else:
                if strategy_answer == 1:
                    params['sAnswer'] = 1    # 1:正确 0:错误
                else:
                    params['sAnswer'] = 0
            answer_consolidate = InterfaceMgr.get_interface("web_student", "answer_consolidate")
            if not CommonFun.test_interface(self.student_host, answer_consolidate, "post", params, self.vertify_answer_consolidate):
                return False
            time.sleep(0.2)
        return True


    def get_assign_param(self):
        class_list_param = dict()
        class_list_param["classId"] = self.class_id
        class_list_param["className"] = self.class_name
        class_list = [class_list_param]
        jsonDataParam = dict()
        jsonDataParam["gradeYear"] = self.grade_year
        jsonDataParam["subjectType"] = self.subject_type
        jsonDataParam["type"] = 1
        jsonDataParam["classList"] = class_list
        assign_param = dict()
        assign_param["jsonData"] = jsonDataParam
        return assign_param

    def get_add_problem_param(self, problem_data, node_type):
        add_problem_param = dict()
        problem_param = dict()
        problem_param["homeworkId"] = self.teacher_homework_id
        problem_param["problemId"] = problem_data["problemId"]
        problem_param["scoreSegmentArray"] = []
        problem_param["problemData"] = {}
        problem_param["type"] = 1
        problem_param["nodeType"] = node_type # 按章节：1/按考点：2
        problem_param["newHomeworkSelectTreeType"] = 1
        problem_param["firstNodeId"] = problem_data["tbBookId"]
        problem_param["secondNodeId"] = problem_data["tbBookPointId"]
        problem_param["threeNodeId"] = problem_data["4153"]

        add_problem_param["dataObjStr"] = problem_param
        return add_problem_param

    def get_rand_book_sort_id(self):
        book_sort_list_info = self.problem_service.get_tb_book_sort_list(self.school_id, self.grade_year, self.subject_type)
        rand_num = random.randint(0, len(book_sort_list_info)-1)
        return book_sort_list_info[rand_num][0]

    def get_random_student(self, school_id, class_id):
        student_list = self.student_service.get_student_list(school_id, class_id)
        rand_num = random.randint(0,len(student_list)-1)
        student_info = student_list[rand_num]
        self.student_id = student_info[0]
        self.student_account = student_info[1]
        self.student_name = student_info[2]
        logger.info("%s,%s是被选召的孩子",self.student_account, self.student_name)

    def pre_assign(self):
        # index
        newhomework_index = InterfaceMgr.get_interface("web_teacher", "newhomework_index")
        if not CommonFun.test_interface(self.teacher_host, newhomework_index, "get", None, "请选择年级、班级和出题类型"):
            return False

        # check_book_sort
        homework_check_is_exit_tbbooksort = InterfaceMgr.get_interface("web_teacher", "homework_check_is_exit_tbbooksort")
        homework_check_is_exit_tbbooksort_param = self.get_assign_param()
        if not CommonFun.test_interface(self.teacher_host, homework_check_is_exit_tbbooksort, "post",
                                    homework_check_is_exit_tbbooksort_param, "-1"):
            return False

        # assign_temp
        assignment_temp = InterfaceMgr.get_interface("web_teacher", "assignment_temp")
        assignment_temp_param = self.get_assign_param()
        if not CommonFun.test_interface(self.teacher_host, assignment_temp, "post",
                                        assignment_temp_param, "统一自主出题（试题篮）"):
            return False

        self.teacher_homework_id = self.problem_service.get_cur_max_homework_id()

        get_selected_problem = InterfaceMgr.get_interface("web_teacher", "get_selected_problem")
        get_selected_problem_param = dict()
        get_selected_problem_param["homeworkId"] = self.teacher_homework_id
        get_selected_problem_param["noteType"] = 1
        if not CommonFun.test_interface(self.teacher_host, get_selected_problem, "get",
                                        get_selected_problem_param, self.vertify_common):
            return False
        return True

    def unified_autonomy_choose_problem_by_point(self):
        get_newhomework_by_note_type = InterfaceMgr.get_interface("web_teacher", "get_newhomework_by_note_type")
        get_newhomework_by_note_type_param = dict()
        get_newhomework_by_note_type_param["homeworkId"] = self.teacher_homework_id
        get_newhomework_by_note_type_param["nodeType"] = 2
        if not CommonFun.test_interface(self.teacher_host, get_newhomework_by_note_type, "get",
                                        get_newhomework_by_note_type_param, "按考点"):
            return False
        # 选考点
        all_point_domain_info = self.problem_service.get_all_point_domain_info()
        select_point_domain = all_point_domain_info[random.randint(0,len(all_point_domain_info)-1)]
        select_domain_third_id = select_point_domain[0]
        select_point_domain_name = select_point_domain[1]
        select_domain_second_id = select_point_domain[2]
        first_point_domain_info = self.problem_service.get_point_domain(select_domain_second_id)
        select_domain_first_id = first_point_domain_info[1]
        get_domain_problem_info = InterfaceMgr.get_interface("web_teacher", "get_domain_problem_info")
        get_domain_problem_info_param = dict()
        get_domain_problem_info_param["domainFirstId"] = select_domain_first_id
        get_domain_problem_info_param["domainSecondId"] = select_domain_second_id
        get_domain_problem_info_param["domainThreeId"] = select_domain_third_id
        get_domain_problem_info_param["subjectType"] = 2
        if not CommonFun.test_interface(self.teacher_host, get_domain_problem_info, "get", get_domain_problem_info_param,
                                        self.vertify_get_problem_info):
            return False
        #挑题
        select_problem_index_list = CommonFun.get_rand_n_num(self.problem_list_data,PROBLEM_NUM)

        add_problem = InterfaceMgr.get_interface("web_teacher", "add_problem")
        for select_problem_index in select_problem_index_list:
            # 挑题目
            add_problem_param = self.get_add_problem_param(self.problem_list_data[select_problem_index],1)
            if not CommonFun.test_interface(self.teacher_host, add_problem, "post", add_problem_param):
                return False
        return True

    def unified_autonomy_choose_problem_by_chapter(self):
        # 选课本
        self.select_book_sort_id = self.get_rand_book_sort_id()
        get_chapter_info = InterfaceMgr.get_interface("web_teacher", "get_chapter_info")
        get_chapter_info_param = dict()
        get_chapter_info_param["tbBookSortId"] = self.select_book_sort_id
        if not CommonFun.test_interface(self.teacher_host, get_chapter_info, "get", get_chapter_info_param,
                                        self.vertify_get_chapter_info):
            return False
        # 选章节
        rand_chapter_info = self.chapter_list[random.randint(0, len(self.chapter_list)-1)]
        book_section_list = rand_chapter_info["bookSectionList"]
        rand_book_section = book_section_list[random.randint(0, len(book_section_list)-1)]
        self.select_tb_book_section_id = rand_book_section["id"]
        self.select_tb_book_id = rand_book_section["tbBookId"]
        self.select_tb_book_point_id = rand_chapter_info["tbBookPointId"]

        get_problem_info = InterfaceMgr.get_interface("web_teacher", "get_problem_info")
        get_problem_info_param = dict()
        get_problem_info_param["tbBookId"] = self.select_tb_book_id
        get_problem_info_param["tbBookPointId"] = self.select_tb_book_point_id
        get_problem_info_param["tbBookSectionId"] = self.select_tb_book_section_id
        get_problem_info_param["subjectType"] = 1
        if not CommonFun.test_interface(self.teacher_host, get_problem_info, "get", get_problem_info_param,
                                        self.vertify_get_problem_info):
            return False
        select_problem_index_list = CommonFun.get_rand_n_num(self.problem_list_data,PROBLEM_NUM)

        add_problem = InterfaceMgr.get_interface("web_teacher", "add_problem")
        for select_problem_index in select_problem_index_list:
            # 挑题目
            add_problem_param = self.get_add_problem_param(self.problem_list_data[select_problem_index],1)
            if not CommonFun.test_interface(self.teacher_host, add_problem, "post", add_problem_param):
                return False
        return True

    def preview_and_assign_homework(self):
        # 预览
        assignment_problem_preview = InterfaceMgr.get_interface("web_teacher", "assignment_problem_preview")
        assignment_problem_preview_param = dict()
        assignment_problem_preview_param["homeworkId"] = self.teacher_homework_id
        if not CommonFun.test_interface(self.teacher_host, assignment_problem_preview, "get",
                                        assignment_problem_preview_param):
            return False

        get_basket_info = InterfaceMgr.get_interface("web_teacher", "get_basket_info")
        get_chapter_info_param = dict()
        get_chapter_info_param["homeworkId"] = self.teacher_homework_id
        if not CommonFun.test_interface(self.teacher_host, get_basket_info, "post", get_chapter_info_param,
                                        self.vertify_get_basket_info):
            return False

        # 布置任务
        newhomework_assignment = InterfaceMgr.get_interface("web_teacher", "newhomework_assignment")
        newhomework_assignment_param = dict()
        newhomework_assignment_param["homeworkId"] = self.teacher_homework_id
        newhomework_assignment_param["limitedType"] = 0  # 不限时
        newhomework_assignment_param["selectedOption"] = 0 # 限时多长时间
        newhomework_assignment_param["textVal"] = TARGET
        if not CommonFun.test_interface(self.teacher_host, newhomework_assignment, "post",
                                        newhomework_assignment_param, self.vertify_common):
            return False

        # 任务列表
        assignmentlist = InterfaceMgr.get_interface("web_teacher", "assignmentlist")
        assignmentlist_param = dict()
        assignmentlist_param["status"] = 2
        if not CommonFun.test_interface(self.teacher_host, assignmentlist, "get", assignmentlist_param, "任务列表"):
            return False

        # 查看任务
        look_homework_problem_content = InterfaceMgr.get_interface("web_teacher", "look_homework_problem_content")
        look_homework_problem_content_param = dict()
        look_homework_problem_content_param["homeworkId"] = self.teacher_homework_id
        if not CommonFun.test_interface(self.teacher_host, look_homework_problem_content, "get",
                                        look_homework_problem_content_param, "任务范围及其题目分布"):
            return False
        return True

    def student_do_homework(self):
        # 获取学生自习课任务列表
        show_teacher_homework = InterfaceMgr.get_interface("web_student", "show_teacher_homework")
        if not CommonFun.test_interface(self.student_host, show_teacher_homework, "get", None, "自习课任务"):
            return False

        student_homework_info = self.problem_service.get_student_homework_info(self.teacher_homework_id, self.student_id)
        self.student_homework_id = student_homework_info[0]
        self.student_homework_name = student_homework_info[1]

        # 任务目标
        show_homework_task_target = InterfaceMgr.get_interface("web_student", "show_homework_task_target")
        show_homework_task_target_param = dict()
        show_homework_task_target_param["homeworkId"] = self.student_homework_id
        if not CommonFun.test_interface(self.student_host, show_homework_task_target, "get",
                                        show_homework_task_target_param, TARGET):
            return False

        # 做题
        self.homework_problem_count = self.problem_service.get_homework_cout(self.student_homework_id)
        if not self.do_all_problem(self.student_homework_id, self.homework_problem_count):
            return False
        return True

    def student_check_report(self):
        # 查看报告
        view_homework_report = InterfaceMgr.get_interface("web_student", "view_homework_report")
        view_homework_report_param = dict()
        view_homework_report_param["pageNo"] = 1
        view_homework_report_param["homeworkId"] = self.student_homework_id
        if not CommonFun.test_interface(self.student_host, view_homework_report, "get", view_homework_report_param,"完成情况"):
            return False

        # 错题分析
        select_problem_index = random.randint(1,self.homework_problem_count)
        error_analysis = InterfaceMgr.get_interface("web_student", "error_analysis")
        error_analysis_param = dict()
        error_analysis_param["pageNo"] = 1
        error_analysis_param["p_name"] = "t_homework"
        error_analysis_param["homeworkId"] = self.student_homework_id
        error_analysis_param["indexNo"] = select_problem_index
        if not CommonFun.test_interface(self.student_host, error_analysis, "get", error_analysis_param,"错题分析"):
            return False

        # 举一反三
        view_homework_one2Three = InterfaceMgr.get_interface("web_student", "view_homework_one2Three")
        view_homework_one2Three_param = dict()
        view_homework_one2Three_param["homeworkId"] = self.student_homework_id
        view_homework_one2Three_param["hpNo"] = select_problem_index
        if not CommonFun.test_interface(self.student_host, view_homework_one2Three, "get", view_homework_one2Three_param,"举一反三"):
            self.select_problem_id = self.problem_service.get_homework_problem_id(self.student_homework_id, select_problem_index)
            recommend_problems = self.problem_service.get_homework_recommend_problems(self.student_homework_id, self.select_problem_id)
            if len(recommend_problems) <= 0:
                logger.warning("homework_id=%s,index=%s,problem_id=%s，没有推出题目",
                               self.student_homework_id, select_problem_index, self.select_problem_id)
            return False

        # 查看任务
        look_teacher_homework = InterfaceMgr.get_interface("web_student", "look_teacher_homework")
        look_teacher_homework_param = dict()
        look_teacher_homework_param["pageNo"] = 1
        look_teacher_homework_param["homeworkId"] = self.student_homework_id
        if not CommonFun.test_interface(self.student_host, look_teacher_homework, "get", look_teacher_homework_param,"自习课任务题目"):
            return False
        return True

    def teacher_check_report(self):
        # 检查是否有人完成了
        check_student_complete_situation = InterfaceMgr.get_interface("web_teacher", "check_student_complete_situation")
        check_student_complete_situation_param = dict()
        check_student_complete_situation_param["homeworkId"] = self.teacher_homework_id
        check_student_complete_situation_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, check_student_complete_situation, "post",
                                        check_student_complete_situation_param, self.vertify_common):
            return False

        # 查看报告
        new_report = InterfaceMgr.get_interface("web_teacher", "new_report")
        new_report_param = dict()
        new_report_param["homeworkId"] = self.teacher_homework_id
        new_report_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, new_report, "get", new_report_param, "查看报告"):
            return False

        # 查看完成情况
        new_complete_info = InterfaceMgr.get_interface("web_teacher", "new_complete_info")
        new_complete_info_param = dict()
        new_complete_info_param["homeworkId"] = self.teacher_homework_id
        new_complete_info_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, new_complete_info, "get", new_complete_info_param, "查看完成情况"):
            return False

        # 个人完成情况
        student_answer_situation_jsp = InterfaceMgr.get_interface("web_teacher", "student_answer_situation_jsp")
        student_answer_situation_jsp_param = dict()
        student_answer_situation_jsp_param["studentId"] = self.student_id
        student_answer_situation_jsp_param["homeworkId"] = self.teacher_homework_id
        student_answer_situation_jsp_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, student_answer_situation_jsp, "get",
                                        student_answer_situation_jsp_param, "查看详情"):
            return False

        student_answer_situation = InterfaceMgr.get_interface("web_teacher", "student_answer_situation")
        student_answer_situation_param = dict()
        student_answer_situation_param["studentId"] = self.student_id
        student_answer_situation_param["homeworkId"] = self.teacher_homework_id
        if not CommonFun.test_interface(self.teacher_host, student_answer_situation, "post",
                                        student_answer_situation_param, self.vertify_student_answer_situation):
            return False

        # 题目解析
        get_problem_detail = InterfaceMgr.get_interface("web_teacher", "get_problem_detail")
        get_problem_detail_param = dict()
        get_problem_detail_param["problemId"] = self.select_problem_id
        if not CommonFun.test_interface(self.teacher_host, get_problem_detail, "get", get_problem_detail_param, "题目详情"):
            return False

        # 答题详情
        show_unify_answer_detail = InterfaceMgr.get_interface("web_teacher", "show_unify_answer_detail")
        show_unify_answer_detail_param = dict()
        show_unify_answer_detail_param["classId"] = self.class_id
        show_unify_answer_detail_param["teacherHomeworkId"] = self.teacher_homework_id
        show_unify_answer_detail_param["groupSegment"] = -1
        show_unify_answer_detail_param["indexNo"] = 1
        if not CommonFun.test_interface(self.teacher_host, show_unify_answer_detail, "get",
                                        show_unify_answer_detail_param, "解答统计"):
            return False
        return True

    def intelligence_consolidation_exercise(self):
        # 智能巩固练习
        consolidate_problem = InterfaceMgr.get_interface("web_teacher", "consolidate_problem")
        consolidate_problem_param = dict()
        consolidate_problem_param["homeworkId"] = self.teacher_homework_id
        consolidate_problem_param["classId"] = self.class_id
        consolidate_problem_param["homeworkType"] = 1
        consolidate_problem_param["type"] = 1
        if not CommonFun.test_interface(self.teacher_host, consolidate_problem, "get",
                                        consolidate_problem_param, "统一自主巩固练习"):
            return False
        return True

    def autonomy_consolidation_exercise(self):
        # 自主巩固练习
        consolidate_problem = InterfaceMgr.get_interface("web_teacher", "consolidate_problem")
        consolidate_problem_param = dict()
        consolidate_problem_param["homeworkId"] = self.teacher_homework_id
        consolidate_problem_param["classId"] = self.class_id
        consolidate_problem_param["homeworkType"] = 1
        consolidate_problem_param["type"] = 2
        if not CommonFun.test_interface(self.teacher_host, consolidate_problem, "get",
                                        consolidate_problem_param, "统一自主巩固练习"):
            return False

        # 挑选
        consolidate_problems = self.problem_service.get_teacher_consolidate_problems(self.teacher_homework_id)
        self.teacher_consolidate_id = consolidate_problems[0][2]
        select_consolidate_problem_index_list = CommonFun.get_rand_n_num(consolidate_problems, PROBLEM_NUM)
        for select_consolidate_index in select_consolidate_problem_index_list:
            consolidate_problem_id = select_consolidate_problem_index_list[select_consolidate_index][0]
            problem_status = InterfaceMgr.get_interface("web_teacher", "problem_status")
            problem_status_param = dict()
            problem_status_param["id"] = consolidate_problem_id
            problem_status_param["status"] = 1
            if not CommonFun.test_interface(self.teacher_host, problem_status, "post",
                                            problem_status_param, self.vertify_common):
                return False

        # 布置
        empty_group_count = InterfaceMgr.get_interface("web_teacher", "empty_group_count")
        empty_group_count_param = dict()
        empty_group_count_param["consolidateId"] = self.teacher_consolidate_id
        if not CommonFun.test_interface(self.teacher_host, empty_group_count, "post",
                                        empty_group_count_param, None):
            return False
        consolidate_save = InterfaceMgr.get_interface("web_teacher", "consolidate_save")
        consolidate_save_param = dict()
        consolidate_save_param["consolidateId"] = self.teacher_consolidate_id
        consolidate_save_param["homeworkId"] = self.teacher_homework_id
        consolidate_save_param["consolidateType"] = 3
        if not CommonFun.test_interface(self.teacher_host, consolidate_save, "post",
                                        consolidate_save_param, self.vertify_common):
            return False
        return True

    def teacher_arrange_consolidation_exercise(self):
        # 巩固练习索引
        consolidate_index = InterfaceMgr.get_interface("web_teacher", "consolidate_index")
        consolidate_index_param = dict()
        consolidate_index_param["homeworkId"] = self.teacher_homework_id
        consolidate_index_param["classId"] = self.class_id
        consolidate_index_param["homeworkType"] = 1
        if not CommonFun.test_interface(self.teacher_host, consolidate_index, "get", consolidate_index_param,"布置巩固练习"):
            return False

        if random.randint(0,1) == 0:
            if not self.intelligence_consolidation_exercise():
                return False
        else:
            if not self.autonomy_consolidation_exercise():
                return False
        return True

    def teacher_check_consolidate(self):
        consolidate_list = InterfaceMgr.get_interface("web_teacher", "consolidate_list")
        if not CommonFun.test_interface(self.teacher_host, consolidate_list, "get", None, "巩固练习列表"):
            return False

        consolidate_group_segment = InterfaceMgr.get_interface("web_teacher", "consolidate_group_segment")
        consolidate_group_segment_param = dict()
        consolidate_group_segment_param["consolidateId"] = self.teacher_consolidate_id
        consolidate_group_segment_param["from"] = 2
        consolidate_group_segment_param["preview"] = 1
        if not CommonFun.test_interface(self.teacher_host, consolidate_group_segment, "get",
                                        consolidate_group_segment_param, "巩固练习"):
            return False
        return True

    def student_do_consolidate(self):
        # 查看巩固练习
        view_homework_consolidate = InterfaceMgr.get_interface("web_student", "view_homework_consolidate")
        view_homework_consolidate_param = dict()
        view_homework_consolidate_param["pageNo"] = 1
        view_homework_consolidate_param["homeworkId"] = self.student_homework_id
        if not CommonFun.test_interface(self.student_host, view_homework_consolidate, "get",
                                        view_homework_consolidate_param, "检索题号"):
            return False

        # 做巩固练习
        if not self.do_all_consolidate(self.student_homework_id):
            return False
        return True

if __name__ == "__main__":
    self_study_process = SelfStudyProcess()
    # 老师
    if not self_study_process.login(self_study_process.teacher_account, self_study_process.teacher_password):
        exit("")
    if not self_study_process.get_class_info(self_study_process.teacher_account):
        exit("")
    if not self_study_process.pre_assign():
        exit("")
    if not self_study_process.unified_autonomy_choose_problem_by_chapter():
        exit("")
    if not self_study_process.preview_and_assign_homework():
        exit("")

    self_study_process.get_random_student(self_study_process.school_id,self_study_process.class_id)
    # 学生
    if not self_study_process.login(self_study_process.student_account, self_study_process.student_password):
        exit("")
    if not self_study_process.student_do_homework():
        exit("")
    if not self_study_process.student_check_report():
        exit("")

    # 老师
    if not self_study_process.login(self_study_process.student_account, self_study_process.teacher_password):
        exit("")
    if not self_study_process.teacher_check_report():
        exit("")
    if not self_study_process.teacher_arrange_consolidation_exercise():
        exit("")
    if not self_study_process.teacher_check_consolidate():
        exit("")


    # 学生
    if not self_study_process.login(self_study_process.student_account, self_study_process.student_password):
        exit("")
    if not self_study_process.student_do_consolidate():
        exit("")








