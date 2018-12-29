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
from util.log import logger

DOWNLOAD_PAPER_WAIT_TIME = 60

class WeekTestProcess:
    def __init__(self):
        root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(root_dir + "/config/teacher_account.ini")
        cur_env = FileUtil.get_cur_env()
        self.http_util = HttpConnectMgr.get_http_connect()
        self.teacher_host = DomainMgr.get_domain("teacher_host")
        self.sigma_student_host = DomainMgr.get_domain("sigma_student_host")
        self.student_service = StudentService()
        self.problem_service = ProblemService()
        self.teacher_account = ini_util.get_item_attr(cur_env, "user")
        self.teacher_password = ini_util.get_item_attr(cur_env, "password")
        self.week_test_work_class_id = 0
        self.teacher_id = 0
        self.student_account = ""
        self.student_password = ""
        self.student_id = 0
        self.student_name = ""
        self.teacher_week_test_id = 0
        self.stu_task_id = 0
        self.student_score = 0
        self.school_id = 0
        self.class_id = 0
        self.grade_year = 0
        self.token = ""
        self.paper_name = ""
        self.rand_problem_id = 0

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

    @staticmethod
    def reset_password(account):
        account_info = AccountMgr.get_admin_account()
        login_res = AccountMgr.login(account_info)
        if re.search("错误报告", login_res):
            logger.warning("登录失败，请检查配置的用户名和密码,"+account_info[0])
            return False
        host = DomainMgr.get_domain("ms_host")
        http_util = HttpConnectMgr.get_http_connect()
        student_service = StudentService()
        user_id = student_service.get_user_id(account)
        reset_res = http_util.post(host, "/web-ms/auth/user/resetPasswd",
                                   {'userId': user_id, 'password': '123456'})
        if re.search("操作成功", reset_res):
            logger.info("[%s]已将密码重置为[123456]", account)
            AccountMgr.logout()
            return True
        else:
            logger.warning("[%s]重置密码失败,检查配置账号或者配置的管理员是否有权限" % (account))
            AccountMgr.logout()
            return False

    def app_login(self, account):
        login_param = dict()
        login_param['loginName'] = account
        login_param['password'] = "123456"  # 使用了默认的密码 @warning
        login_res, login_code = AccountMgr.app_login(login_param)
        if re.search("错误报告", login_res):
            logger.error("(%s)login fail,please check you card and password" % account)
            return False
        login_res_json = json.loads(login_res)
        if login_res_json["type"] == "failure":
            logger.info("登录失败，原因：%s", login_res_json["message"])
            if not self.reset_password(account):
                return False
            else:
                return self.app_login(account)
        self.token = login_res_json["userdata"]["token"]
        self.student_id = login_res_json["userdata"]["serverStudentId"]
        return True

    # 从人教A获取随机章节
    def get_rand_chapter_id(self, teacher_account):
        common_service = CommonService()
        self.teacher_id = common_service.get_teacher_id_by_account(teacher_account)
        self.school_id = common_service.get_school_id_by_teacher_id(self.teacher_id)
        class_info = common_service.get_teacher_teaching_classes(self.teacher_id)
        self.class_id = class_info[0][0]
        self.grade_year = common_service.get_grade_year_by_class_id(self.class_id)
        problem_service = ProblemService()
        chapter_infos = problem_service.get_chapter_info_from_rja()
        rand_num = random.randint(0, len(chapter_infos)-1)
        return chapter_infos[rand_num][0]

    def get_random_student(self, school_id, class_id):
        student_list = self.student_service.get_student_list(school_id, class_id)
        rand_num = random.randint(0,len(student_list)-1)
        student_info = student_list[rand_num]
        self.student_id = student_info[0]
        self.student_account = student_info[1]
        self.student_name = student_info[2]
        logger.info("%s,%s是被选召的孩子",self.student_account, self.student_name)

    def do_all_problems(self, week_test_id, teacher_week_test_id, student_id):
        update_problem_data = InterfaceMgr.get_interface("sigma_student", "update_problem_data")
        choose_problem = InterfaceMgr.get_interface("sigma_student", "choose_problem")
        student_info = self.student_service.get_student_profile_info_by_id(student_id)
        if student_info[6] is None:
            student_level = 3
        else:
            student_level = student_info[6]+1
        problem_count = self.problem_service.get_week_test_count(week_test_id)
        strategy_answer_list = WeekTestUtil.get_strategy_answer_list(week_test_id, student_level, problem_count)
        host = DomainMgr.get_domain("sigma_student_host")
        root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(root_dir + "/student/feedback_strategy.ini")
        level = "level_"+str(student_level)
        jd_high_score_rate = float(ini_util.get_item_attr(level, "jd_high_score_rate"))
        jd_low_score_rate = float(ini_util.get_item_attr(level, "jd_low_score_rate"))

        week_test_info = self.problem_service.get_week_test_info(week_test_id)
        class_id = week_test_info[6]

        choose_list = list()
        temp_choose_list = list()
        index_pointer = 0
        for problem_index in range(problem_count):
            all_list = list()
            week_test_problem_id, paper_problem_id, index_no, score, is_grasp, grasp_score, student_grasp_score,first_index,all_count,choose_count,student_choose = self.problem_service.get_week_test_problem_info(week_test_id,problem_index+1)
            week_test_status = self.problem_service.get_week_test_status(teacher_week_test_id, class_id)
            if first_index != -1:
                for xz_problem_index in range(first_index,first_index+all_count):
                    all_list.append(xz_problem_index)
            if week_test_status == 2 or week_test_status ==1:   # 已收卷
                if (problem_index+1) in all_list:
                    if student_choose == 1:
                        choose_list.append(index_no)
                        strategy_answer_list[problem_index] = grasp_score
                    else:
                        strategy_answer_list[problem_index] = 0
                else:
                    strategy_answer_list[problem_index] = grasp_score
            else:
                if is_grasp != -1:
                    if (problem_index+1) in all_list:
                        if student_choose == 1:
                            choose_list.append(index_no)
                            strategy_answer_list[problem_index] = grasp_score
                        else:
                            strategy_answer_list[problem_index] = 0
                    else:
                        strategy_answer_list[problem_index] = grasp_score
                else:
                    if first_index != -1 and problem_index >= index_pointer:
                        temp_choose_list = CommonFun.get_rand_n_value(all_list, choose_count)
                        for value in temp_choose_list:
                            choose_list.append(value)
                        index_pointer = problem_index + all_count
                    if (problem_index+1) in temp_choose_list:   #选做题
                        xz_params = dict()
                        xz_params["pkId"] = week_test_problem_id
                        xz_params["problemId"] = paper_problem_id
                        xz_params["chooseType"] = 1 # chooseType : 1代表已选中，0代表未选中
                        self.http_util.post(host, choose_problem, xz_params)
                        pass
                    if problem_index >= index_pointer:
                        temp_choose_list.clear()

                    problem_type = self.problem_service.get_problem_type_by_id(paper_problem_id)
                    strategy_answer = strategy_answer_list[problem_index]
                    params_data = dict()
                    params = dict()
                    params_data['pkId'] = week_test_problem_id
                    params_data['problemId'] = paper_problem_id
                    params_data['time'] = random.randint(10, 300)
                    params_data['isChoosed'] = 0
                    if problem_type == 0:   # 选择
                        params_data["answerPath"] = ""
                        right_answer = self.problem_service.get_right_answer_by_id(paper_problem_id)
                        right_answer_str = self.problem_service.get_answer_str(right_answer)
                        rand_wrong_answer = self.problem_service.get_rand_wrong_answer(right_answer, ("A","B","C","D","E"))
                        if strategy_answer == 1:
                            params_data['selectAnswer'] = right_answer_str
                            params_data["score"] = score
                            params_data["isGrasp"] = 1
                            if (problem_index+1) in all_list:
                                if (problem_index+1) in choose_list:   # 选做题
                                    strategy_answer_list[problem_index] = score
                                else:
                                    strategy_answer_list[problem_index] = 0
                            else:
                                strategy_answer_list[problem_index] = score
                        else:
                            params_data['selectAnswer'] = rand_wrong_answer
                            params_data["score"] = 0
                            params_data["isGrasp"] = 0
                            strategy_answer_list[problem_index] = 0
                    elif problem_type == 1:  # 填空
                        params_data["answerPath"] = "pre_pic0__1474961004930.jpg"
                        params_data['selectAnswer'] = "1"
                        if strategy_answer == 1:
                            params_data["score"] = score
                            params_data["isGrasp"] = 1
                            if (problem_index+1) in all_list:
                                if (problem_index+1) in choose_list:   # 选做题
                                    strategy_answer_list[problem_index] = score
                                else:
                                    strategy_answer_list[problem_index] = 0
                            else:
                                strategy_answer_list[problem_index] = score
                        else:
                            params_data["score"] = 0
                            params_data["isGrasp"] = 0
                            strategy_answer_list[problem_index] = 0
                    else:   # 解答
                        params_data["answerPath"] = "pre_pic0__1474961004930.jpg"# WeekTestUtil.get_answer_picture()
                        if strategy_answer == 1:
                            student_score = random.randint(int(score * jd_high_score_rate), int(score))
                            params_data['selectAnswer'] = "1"
                            params_data["score"] = student_score
                            params_data["isGrasp"] = 1
                        else:
                            student_score = random.randint(1, int(score * jd_low_score_rate))
                            params_data['selectAnswer'] = "1"
                            params_data["score"] = student_score
                            params_data["isGrasp"] = 0
                        if (problem_index+1) in all_list:
                            if (problem_index+1) in choose_list:   #选做题
                                strategy_answer_list[problem_index] = student_score
                            else:
                                strategy_answer_list[problem_index] = 0
                        else:
                            strategy_answer_list[problem_index] = student_score
                    param_data_list = list()
                    param_data_list.append(params_data)
                    params["studentId"] = student_id
                    params["data"] = param_data_list
                    params["_token_"] = self.token
                    res = self.http_util.post(host, update_problem_data, params)
                    if not re.search("一周速测提交问题成功！", str(res)):
                        logger.error("stu_id=[%s],week_test_id=[%s],index=[%d]week_test_error" % (student_id, week_test_id, problem_index))
                        return False
                    time.sleep(0.5)
        self.interface_ok(update_problem_data)
        return True

    def vertify_get_basket_info(self, get_basket_info, basket_info_res, vertify_param):
        basket_problem_res_json = json.loads(basket_info_res)
        jd_problem_count = basket_problem_res_json["jdProblemClassify"]["problemCount"]
        tk_problem_count = basket_problem_res_json["tkProblemClassify"]["problemCount"]
        xz_problem_count = basket_problem_res_json["xzProblemClassify"]["problemCount"]
        if jd_problem_count+tk_problem_count+xz_problem_count <= 0:
            logger.error("%s没推出题目", get_basket_info)
            return False
        return True

    def vertify_check_paper_name(self, check_paper_name, check_paper_name_res, vertify_param):
        if check_paper_name_res == 1:
            logger.error("%s 重名 %s", check_paper_name, self.paper_name)
            return False
        return True

    def vertify_do_week_test_num(self, do_week_test_num, do_week_test_num_res, vertify_param):
        do_week_test_num_res_json = json.loads(do_week_test_num_res)
        if do_week_test_num_res_json["doNum"] <= 0:
            logger.error("%s还未有学生作答", do_week_test_num)
            return False
        return True

    def vertify_create_week_test_report(self, create_week_test_report, create_week_test_report_res, vertify_param):
        if int(create_week_test_report_res) != 1:
            logger.error("%s收卷报错,week_test_id=%d", create_week_test_report, self.teacher_week_test_id)
            return False
        return True

    def vertify_complete_class_paper(self, complete_class_paper, complete_class_paper_res, vertify_param):
        complete_class_paper_json = json.loads(complete_class_paper_res)
        if complete_class_paper_json["success"] is False:
            self.page_load_error(complete_class_paper)
            return False
        return True

    def vertify_save_content(self, save_content, save_content_res, vertify_param):
        if save_content_res != "true":
            self.page_load_error(save_content)
            return False
        return True

    def vertify_show_students_list(self, show_students_list, show_students_list_res, vertify_param):
        show_students_list_json = json.loads(show_students_list_res)
        if show_students_list_json["success"] is False or len(show_students_list_json["studentsList"]) <= 0:
            self.page_load_error(show_students_list)
            return False
        return True

    def vertify_get_problem_list(self, get_problem_list, get_problem_list_res, vertify_param):
        get_problem_list_json = json.loads(get_problem_list_res)
        if get_problem_list_json["success"] is False or len(get_problem_list_json["problemsList"]) <= 0:
            self.page_load_error(get_problem_list)
            return False
        return True

    def vertify_show_segment_problem_compare(self, show_segment_problem_compare, show_segment_problem_compare_res, vertify_param):
        show_segment_problem_compare_json = json.loads(show_segment_problem_compare_res)
        if len(show_segment_problem_compare_json["problemNoList"]) <= 0:
            self.page_load_error(show_segment_problem_compare)
            return False
        return True

    def vertify_student_reposrt(self, student_reposrt, student_reposrt_res, vertify_param):
        student_reposrt_json = json.loads(student_reposrt_res)
        for feedback_info in student_reposrt_json:
            if int(feedback_info["problemId"]) == self.rand_problem_id:
                if int(feedback_info["explainNum"]) != 1:
                    return False
        return True

    def vertify_get_download_path(self, get_download_path, get_download_path_res, vertify_param):
        get_download_path_json = json.loads(get_download_path_res)
        if get_download_path_json["success"] is False:
            return False
        return True

    def vertify_get_task_list(self, interface, res, vertify_param):
        # "获取学习任务包任务列表成功！"
        res_json = json.loads(res)
        if res_json["type"] != "success":
            return False
        task_list_data = res_json["data"]
        change = False
        for task_data in task_list_data:
            if task_data["paperType"] == 1:# 周测
                vertify_paper_name = "周测卷："+self.paper_name
            else:
                vertify_paper_name = "章测卷："+vertify_param["paper_name"]
            if task_data["name"] == vertify_paper_name:
                self.stu_task_id = task_data["taskId"]
                change = True
                break
        return change

    def vertify_get_book_list(self, interface, res, vertify_param):
        res_json = json.loads(res)
        book_list = res_json["bookList"]
        if len(book_list) > 0:
            return True
        return False

    def vertify_get_chapter_list(self, interface, res, vertify_param):
        res_json = json.loads(res)
        chapter_and_paper_list = res_json["chapterAndPaperList"]
        rand_chapter_index = random.randint(0, len(chapter_and_paper_list)-1)
        if len(chapter_and_paper_list[rand_chapter_index]["examPaperId"]) > 0:
            return True
        return False

    def teacher_save_week_test(self):
        # 布置任务
        layer_task_index = InterfaceMgr.get_interface("web_teacher", "layer_task_index")
        if not CommonFun.test_interface(self.teacher_host, layer_task_index, "get", None, "布置任务"):
            return False

        # 自主组卷
        independent_volume = InterfaceMgr.get_interface("web_teacher", "independent_volume")
        if not CommonFun.test_interface(self.teacher_host, independent_volume, "get", None, "您可以使用自主组卷功能进行个性化组卷，试卷可用于一周速测"):
            return False

        # 智能组卷
        intelligent_arrange = InterfaceMgr.get_interface("web_teacher", "intelligent_arrange")
        if not CommonFun.test_interface(self.teacher_host, intelligent_arrange, "get", None, "智能组卷"):
            return False

        # 预创建
        chapter_point_id = self.get_rand_chapter_id(self.teacher_account)
        zn_week_test = InterfaceMgr.get_interface("web_teacher", "zn_week_test")
        zn_week_test_param = dict()
        zn_week_test_param["size"] = 1
        zn_week_test_param["type"] = 1
        zn_week_test_param["pointId"] = chapter_point_id
        if not CommonFun.test_interface(self.teacher_host, zn_week_test, "get", zn_week_test_param, None):
            return False

        homework_id = self.problem_service.get_cur_max_homework_id()

        # 智能组卷预览
        assign_problem_preview = InterfaceMgr.get_interface("web_teacher", "assign_problem_preview")
        preview_params = dict()
        preview_params["paperType"] = 0
        preview_params["homeworkId"] = homework_id
        preview_params["type"] = 1
        preview_params["size"] = 1
        preview_params["pointId"] = chapter_point_id
        if not CommonFun.test_interface(self.teacher_host, assign_problem_preview, "get", preview_params, "保存/发布"):
            return False

        # 试题篮
        get_basket_info = InterfaceMgr.get_interface("web_teacher", "get_basket_info")
        basket_info_param = dict()
        basket_info_param["homeworkId"] = homework_id
        if not CommonFun.test_interface(self.teacher_host, get_basket_info, "post", basket_info_param, self.vertify_get_basket_info):
            return False

        # 检查试卷重名
        autotest_paper_name_index = self.problem_service.get_max_autotest_week_test_name_index()
        self.paper_name = "自动化测试" + str(int(autotest_paper_name_index+1))

        check_paper_name = InterfaceMgr.get_interface("web_teacher", "check_paper_name")
        check_paper_name_param = dict()
        check_paper_name_param["paperName"] = self.paper_name
        if not CommonFun.test_interface(self.teacher_host, check_paper_name, "post", check_paper_name_param, self.vertify_check_paper_name):
            return False

        # 保存试卷
        assign_week_test = InterfaceMgr.get_interface("web_teacher", "assign_week_test")
        assign_week_test_param = dict()
        assign_week_test_param["homeworkId"] = homework_id
        assign_week_test_param["xzScore"] = 6
        assign_week_test_param["tkScore"] = 6
        assign_week_test_param["jdScore"] = "12,12,12,12"
        assign_week_test_param["paperName"] = self.paper_name
        assign_week_test_param["countScore"] = 120
        assign_week_test_param["paperType"] = 4
        if not CommonFun.test_interface(self.teacher_host, assign_week_test, "get", assign_week_test_param, None):
            return False

        self.teacher_week_test_id = self.problem_service.get_week_test_work_id(self.paper_name)

        # 修改试卷
        assign_problem_preview2 = InterfaceMgr.get_interface("web_teacher", "assign_problem_preview2")
        assign_problem_preview2_param = dict()
        assign_problem_preview2_param["paperType"] = 1
        assign_problem_preview2_param["weekTestWorkId"] = self.teacher_week_test_id
        if not CommonFun.test_interface(self.teacher_host, assign_problem_preview2, "get", assign_problem_preview2_param, "保存/发布"):
            return False
        return True

    # 老师布置一周速测
    def teacher_assign_week_test(self):
        # 布置试卷
        do_week_class = InterfaceMgr.get_interface("web_teacher", "do_week_class")
        do_week_class_param = dict()
        do_week_class_param["weekTestId"] = self.teacher_week_test_id
        do_week_class_param["checkClassId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, do_week_class, "get", do_week_class_param, None):
            return False

        logger.info("已成功布置自主卷"+self.paper_name)
        return True

    def student_do_week_test(self):
        get_date_list = InterfaceMgr.get_interface("sigma_student", "get_date_list")
        get_date_list_param = dict()
        get_date_list_param["studentId"] = self.student_id
        get_date_list_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_date_list,
                                        "post", get_date_list_param, "获取时间列表成功！"):
            return False
        # 获取任务列表
        get_task_list = InterfaceMgr.get_interface("sigma_student", "get_task_list")
        get_task_param = dict()
        get_task_param["studentId"] = self.student_id
        get_task_param["date"] = int(time.time()*1000)
        get_task_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_task_list, "post", get_task_param, self.vertify_get_task_list):
            return False

        # 获取任务题目
        #self.stu_task_id = self.problem_service.get_stu_week_test_task_id(self.student_id, self.teacher_week_test_id)
        get_stu_week_test_problem = InterfaceMgr.get_interface("sigma_student", "get_stu_week_test_problem")
        get_week_test_problem_param = dict()
        get_week_test_problem_param["studentId"] = self.student_id
        get_week_test_problem_param["taskId"] = self.stu_task_id
        get_week_test_problem_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_stu_week_test_problem, "post", get_week_test_problem_param, "一周速测  获取题目数据成功！"):
            return False

        # 作答
        if not self.do_all_problems(self.stu_task_id, self.teacher_week_test_id, self.student_id):
            return False

        # 提交
        hand_in = InterfaceMgr.get_interface("sigma_student", "hand_in")
        hand_in_param = dict()
        hand_in_param["studentId"] = self.student_id
        hand_in_param["taskId"] = self.stu_task_id
        hand_in_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, hand_in, "post", hand_in_param, "一周速测 交卷成功！"):
            return False
        return True

    def check_paper(self):
        get_week_test_problem = InterfaceMgr.get_interface("web_teacher", "get_week_test_problem")
        get_week_test_problem_param = dict()
        get_week_test_problem_param["weektestWorkId"] = self.teacher_week_test_id
        if not CommonFun.test_interface(self.teacher_host, get_week_test_problem, "get", get_week_test_problem_param, self.paper_name):
            return False
        return True

    def download_paper(self):
        get_download_path = InterfaceMgr.get_interface("web_teacher", "get_download_path")
        exampaper_id = self.problem_service.get_week_test_exam_paper_id(self.teacher_week_test_id)
        get_download_path_param = dict()
        get_download_path_param["weekTestWorkId"] = self.teacher_week_test_id
        get_download_path_param["examId"] = exampaper_id
        if not CommonFun.test_interface(self.teacher_host, get_download_path, "get", get_download_path_param, self.vertify_get_download_path):
            return False
        return True

    def teacher_collect_paper(self):
        # 我的任务
        my_week_test = InterfaceMgr.get_interface("web_teacher", "my_week_test")
        my_week_test_param = dict()
        my_week_test_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, my_week_test, "get", my_week_test_param, "我的任务"):
            return False

        # 作答人数
        do_week_test_num = InterfaceMgr.get_interface("web_teacher", "do_week_test_num")
        do_week_test_num_param = dict()
        do_week_test_num_param["weekTestId"] = self.teacher_week_test_id
        do_week_test_num_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, do_week_test_num, "post", do_week_test_num_param, self.vertify_do_week_test_num):
            return False

        # 收卷
        create_week_test_report = InterfaceMgr.get_interface("web_teacher", "create_week_test_report")
        create_week_test_report_param = dict()
        self.week_test_work_class_id = self.problem_service.get_week_test_work_class_id(self.teacher_week_test_id,self.class_id)
        create_week_test_report_param["weekTestId"] = self.week_test_work_class_id
        create_week_test_report_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, create_week_test_report, "post", create_week_test_report_param, self.vertify_create_week_test_report):
            return False
        return True

    def teacher_revoke_week_test(self):
        # 已收卷撤销
        revoke_week_test2 = InterfaceMgr.get_interface("web_teacher", "revoke_week_test2")
        revoke_week_test2_param = dict()
        revoke_week_test2_param["weekTestClassId"] = self.week_test_work_class_id
        if not CommonFun.test_interface(self.teacher_host, revoke_week_test2, "post", revoke_week_test2_param, "true"):
            return False

        revoke_week_test = InterfaceMgr.get_interface("web_teacher", "revoke_week_test")
        revoke_week_test_param = dict()
        revoke_week_test_param["weekTestClassId"] = self.week_test_work_class_id
        if not CommonFun.test_interface(self.teacher_host, revoke_week_test, "post", revoke_week_test_param, "true"):
            return False

        return True

    def teacher_review_paper(self):
        # 分层
        layer_detail = InterfaceMgr.get_interface("web_teacher", "layer_detail")
        layer_detail_param = dict()
        layer_detail_param["weektestId"] = self.teacher_week_test_id
        layer_detail_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, layer_detail, "get", layer_detail_param, "分层详情"):
            return False

        # 阅卷
        check_paper_detail = InterfaceMgr.get_interface("web_teacher", "check_paper_detail")
        check_paper_detail_param = dict()
        check_paper_detail_param["weektestId"] = self.teacher_week_test_id
        check_paper_detail_param["classId"] = self.class_id
        check_paper_detail_param["studentId"] = self.student_id
        if not CommonFun.test_interface(self.teacher_host, check_paper_detail, "get", check_paper_detail_param, "批改完成"):
            return False
        return True

    def teacher_generate_report(self):
        # 生成报告
        complete_class_paper = InterfaceMgr.get_interface("web_teacher", "complete_class_paper")
        complete_class_paper_param = dict()
        complete_class_paper_param["weektestId"] = self.teacher_week_test_id
        complete_class_paper_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, complete_class_paper, "get", complete_class_paper_param, self.vertify_complete_class_paper):
            return False
        return True

    def teacher_send_check_reports(self):
        # 班级报告
        get_week_test_teacher_report = InterfaceMgr.get_interface("web_teacher", "get_week_test_teacher_report")
        get_week_test_teacher_report_param = dict()
        get_week_test_teacher_report_param["weekTestId"] = self.teacher_week_test_id
        get_week_test_teacher_report_param["classId"] = self.class_id
        get_week_test_teacher_report_param["fasongbaogao"] = 1
        if not CommonFun.test_interface(self.teacher_host, get_week_test_teacher_report, "get", get_week_test_teacher_report_param, "查看班级答题详情"):
            return False

        # 发送评语
        save_content = InterfaceMgr.get_interface("web_teacher", "save_content")
        save_content_param = dict()
        save_content_param["weekTestId"] = self.teacher_week_test_id
        save_content_param["classId"] = self.class_id
        save_content_param["content"] = self.paper_name+"评语"
        if not CommonFun.test_interface(self.teacher_host, save_content,"post", save_content_param, self.vertify_save_content):
            return False

        # 班级答题详情
        get_week_test_class = InterfaceMgr.get_interface("web_teacher", "get_week_test_class")
        get_week_test_class_param = dict()
        get_week_test_class_param["weektestWorkId"] = self.teacher_week_test_id
        get_week_test_class_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, get_week_test_class, "get", get_week_test_class_param, "答题详情"):
            return False

        week_test_problem_list = self.problem_service.get_week_test_problem_list(self.teacher_week_test_id)
        self.rand_problem_id = week_test_problem_list[random.randint(0,len(week_test_problem_list)-1)][0]

        # 同类提
        one_three_problem_list = InterfaceMgr.get_interface("web_teacher", "one_three_problem_list")
        one_three_problem_list_param = dict()
        one_three_problem_list_param["problemId"] = self.rand_problem_id
        if not CommonFun.test_interface(self.teacher_host, one_three_problem_list,"get",one_three_problem_list_param,"试题分析模型题目"):
            return False

        # 学生报告列表
        teacher_report = InterfaceMgr.get_interface("web_teacher", "teacher_report")
        teacher_report_param = dict()
        teacher_report_param["weekTestId"] = self.teacher_week_test_id
        teacher_report_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, teacher_report, "get", teacher_report_param, "点击学生名字可查看报告及试卷"):
            return False

        # 学生个人报告
        chapter_week_test_presentation = InterfaceMgr.get_interface("web_teacher", "chapter_week_test_presentation")
        chapter_week_test_presentation_param = dict()
        chapter_week_test_presentation_param["weekTestId"] = self.teacher_week_test_id
        chapter_week_test_presentation_param["studengId"] = self.student_id
        chapter_week_test_presentation_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, chapter_week_test_presentation, "get", chapter_week_test_presentation_param, "本次测验分数"):
            return False

        # 获取个人分数
        stu_week_test_id = self.problem_service.get_stu_week_test_task_id(self.student_id, self.teacher_week_test_id)
        self.student_score = self.problem_service.get_stu_week_test_score(stu_week_test_id)

        # 年级报告
        show_single_report = InterfaceMgr.get_interface("web_teacher", "show_single_report")
        show_single_report_param = dict()
        show_single_report_param["reportId"] = self.teacher_week_test_id
        if not CommonFun.test_interface(self.teacher_host, show_single_report, "get", show_single_report_param, "分层走班报告"):
            return False

        # 班级分班详情
        show_classify = InterfaceMgr.get_interface("web_teacher", "show_classify")
        show_classify_param = dict()
        show_classify_param["reportId"] = self.teacher_week_test_id
        show_classify_param["segment"] = -1
        show_classify_param["gradeYear"] = self.grade_year
        if not CommonFun.test_interface(self.teacher_host, show_classify, "get", show_classify_param, "分班建议"):
            return False

        # 分班详情-加载学生
        show_students_list = InterfaceMgr.get_interface("web_teacher", "show_students_list")
        show_students_list_param = dict()
        show_students_list_param["weektestId"] = self.teacher_week_test_id

        if self.student_score < 120*0.6:
            show_students_list_param["minScore"] = 0
            show_students_list_param["maxScore"] = 72
        elif self.student_score < 120*0.8:
            show_students_list_param["minScore"] = 72
            show_students_list_param["maxScore"] = 96
        else:
            show_students_list_param["minScore"] = 96
            show_students_list_param["maxScore"] = 120
        if not CommonFun.test_interface(self.teacher_host, show_students_list, "get", show_students_list_param, self.vertify_show_students_list):
            return False

        # 分班详情-加载题目数据
        get_problem_list = InterfaceMgr.get_interface("web_teacher", "get_problem_list")
        get_problem_list_param = dict()
        get_problem_list_param["weektestId"] = self.teacher_week_test_id
        get_problem_list_param["minScore"] = 0
        get_problem_list_param["maxScore"] = 72
        get_problem_list_param["segment"] = -1
        if not CommonFun.test_interface(self.teacher_host, get_problem_list, "get", get_problem_list_param, self.vertify_get_problem_list):
            return False

        # 分班详情
        show_segment_problem_compare = InterfaceMgr.get_interface("web_teacher", "show_segment_problem_compare")
        show_segment_problem_compare_param = dict()
        show_segment_problem_compare_param["segment"] = -1
        show_segment_problem_compare_param["weektestId"] = self.teacher_week_test_id
        if not CommonFun.test_interface(self.teacher_host, show_segment_problem_compare, "get", show_segment_problem_compare_param, self.vertify_show_segment_problem_compare):
            return False
        return True

    def student_check_report(self):
        # 查看报告
        get_test_report = InterfaceMgr.get_interface("sigma_student", "get_test_report")
        get_test_report_param = dict()
        get_test_report_param["studentId"] = self.student_id
        get_test_report_param["paperType"] = 1
        get_test_report_param["taskId"] = self.stu_task_id
        get_test_report_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_test_report, "post", get_test_report_param, "获取一周速测的报告数据成功！"):
            return False

        stu_week_test_problem_id = self.problem_service.get_stu_week_test_problem_id(self.stu_task_id,self.rand_problem_id)
        # 反馈错题
        choose_explain = InterfaceMgr.get_interface("sigma_student", "choose_explain")
        choose_explain_param = dict()
        choose_explain_param["studentId"] = self.student_id
        data = dict()
        data["taskId"] = self.stu_task_id
        data["pkIds"] = [stu_week_test_problem_id]
        choose_explain_param["data"] = data
        choose_explain_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, choose_explain, "get", choose_explain_param, "反馈题目数据成功！"):
            return False

        return True

    def week_test_increase_score_plan(self):
        # 举一反三
        get_recommend_problem = InterfaceMgr.get_interface("sigma_student", "get_recommend_problem")
        get_recommend_problem_param = dict()
        get_recommend_problem_param["studentId"] = self.student_id
        get_recommend_problem_param["taskId"] = self.stu_task_id
        get_recommend_problem_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_recommend_problem,
                                        "post", get_recommend_problem_param, "获取举一反三 题目数据成功！"):
            return False

        # 分层作业
        get_layer_problem = InterfaceMgr.get_interface("sigma_student", "get_layer_problem")
        get_layer_problem_param = dict()
        get_layer_problem_param["studentId"] = self.student_id
        get_layer_problem_param["taskId"] = self.stu_task_id
        get_layer_problem_param["_token_"] = self.token
        if not CommonFun.test_interface(self.sigma_student_host, get_layer_problem,
                                        "post", get_layer_problem_param, "获取分层作业题目数据成功！"):
            return False

        return True

    def down_task(self):
        down_task = InterfaceMgr.get_interface("sigma_student", "down_task")
        return True

    def check_feedback(self):
        student_report = InterfaceMgr.get_interface("web_teacher", "student_report")
        student_report_param = dict()
        student_report_param["weekTestId"] = self.teacher_week_test_id
        student_report_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, student_report, "post", student_report_param, self.vertify_student_reposrt):
            return False
        return True

    def teacher_check_homework(self):
        go_check_homework = InterfaceMgr.get_interface("web_teacher", "go_check_homework")
        go_check_homework_param = dict()
        go_check_homework_param["weekTestId"] = self.teacher_week_test_id
        go_check_homework_param["classId"] = self.class_id
        if not CommonFun.test_interface(self.teacher_host, go_check_homework, "get", go_check_homework_param, "试卷名 : "+self.paper_name):
            return False
        return True

    def check_standard_paper(self):
        # 书本
        get_book_list = InterfaceMgr.get_interface("web_teacher", "get_book_list")
        get_book_list_param = dict()
        get_book_list_param["sType"] = 2
        get_book_list_param["pageType"] = "standardBookPage"
        get_book_list_param["mergeg"] = "2standardBookPage"
        if not CommonFun.test_interface(self.teacher_host, get_book_list, "get", get_book_list_param, self.vertify_get_book_list):
            return False

        # 理科必修2-基础
        get_chapter_list_index = InterfaceMgr.get_interface("web_teacher", "get_chapter_list_index")
        get_chapter_list_index_param = dict()
        get_chapter_list_index_param["artType"] = 2
        get_chapter_list_index_param["bookSortId"] = 13058
        get_chapter_list_index_param["pageType"] = "standardBookPage"
        if not CommonFun.test_interface(self.teacher_host, get_chapter_list_index, "get", get_chapter_list_index_param, "当前：必修2（理科）"):
            return False

        get_chapter_list = InterfaceMgr.get_interface("web_teacher", "get_chapter_list")
        get_chapter_list_param = dict()
        get_chapter_list_param["artType"] = 2
        get_chapter_list_param["bookSortId"] = 13058
        get_chapter_list_param["pageType"] = "standardBookPage"
        get_chapter_list_param["exampaperLevel"] = 0
        if not CommonFun.test_interface(self.teacher_host, get_chapter_list, "get", get_chapter_list_param, self.vertify_get_chapter_list):
            return False

        # 理科必修2-提高
        get_chapter_list = InterfaceMgr.get_interface("web_teacher", "get_chapter_list")
        get_chapter_list_param = dict()
        get_chapter_list_param["artType"] = 2
        get_chapter_list_param["bookSortId"] = 13058
        get_chapter_list_param["pageType"] = "standardBookPage"
        get_chapter_list_param["exampaperLevel"] = 1
        if not CommonFun.test_interface(self.teacher_host, get_chapter_list, "get", get_chapter_list_param, self.vertify_get_chapter_list):
            return False

        # 书本
        get_book_list = InterfaceMgr.get_interface("web_teacher", "get_book_list")
        get_book_list_param = dict()
        get_book_list_param["sType"] = 2
        get_book_list_param["pageType"] = "reviewBookPage"
        get_book_list_param["mergeg"] = "2reviewBookPage"
        if not CommonFun.test_interface(self.teacher_host, get_book_list, "get", get_book_list_param, self.vertify_get_book_list):
            return False

        # 理科高考一轮-基础
        get_chapter_list = InterfaceMgr.get_interface("web_teacher", "get_chapter_list")
        get_chapter_list_param = dict()
        get_chapter_list_param["artType"] = 2
        get_chapter_list_param["bookSortId"] = 91
        get_chapter_list_param["pageType"] = "reviewBookPage"
        get_chapter_list_param["exampaperLevel"] = 0
        if not CommonFun.test_interface(self.teacher_host, get_chapter_list, "get", get_chapter_list_param, self.vertify_get_chapter_list):
            return False

        # 理科高考一轮-提高
        get_chapter_list = InterfaceMgr.get_interface("web_teacher", "get_chapter_list")
        get_chapter_list_param = dict()
        get_chapter_list_param["artType"] = 2
        get_chapter_list_param["bookSortId"] = 91
        get_chapter_list_param["pageType"] = "reviewBookPage"
        get_chapter_list_param["exampaperLevel"] = 1
        if not CommonFun.test_interface(self.teacher_host, get_chapter_list, "get", get_chapter_list_param, self.vertify_get_chapter_list):
            return False

        return True

if __name__ == "__main__":
    week_test_process = WeekTestProcess()
    # 老师
    if not week_test_process.login(week_test_process.teacher_account,week_test_process.teacher_password):
        exit("")
    #if not week_test_process.check_standard_paper():
     #   exit("")
    if not week_test_process.teacher_save_week_test():
        exit("")
    if not week_test_process.teacher_assign_week_test():
        exit("")
    deal_time1 = time.time()
    week_test_process.get_random_student(week_test_process.school_id,week_test_process.class_id)

    # 学生
    if not week_test_process.app_login(week_test_process.student_account):
        exit("")
    if not week_test_process.student_do_week_test():
        exit("")

    # 老师
    if not week_test_process.login(week_test_process.teacher_account, week_test_process.teacher_password):
        exit("")
    if not week_test_process.check_paper():
        exit("")
    if not week_test_process.teacher_collect_paper():
        exit("")
    if not week_test_process.teacher_review_paper():
        exit("")
    if not week_test_process.teacher_revoke_week_test():
        exit("")
    if not week_test_process.teacher_assign_week_test():
        exit("")

    # 学生
    if not week_test_process.app_login(week_test_process.student_account):
        exit("")
    if not week_test_process.student_do_week_test():
        exit("")

    # 老师
    if not week_test_process.login(week_test_process.teacher_account, week_test_process.teacher_password):
        exit("")
    if not week_test_process.teacher_collect_paper():
        exit("")
    if not week_test_process.teacher_review_paper():
        exit("")
    if not week_test_process.teacher_generate_report():
        exit("")
    if not week_test_process.teacher_send_check_reports():
        exit("")

    # 学生
    if not week_test_process.app_login(week_test_process.student_account):
        exit("")
    if not week_test_process.student_check_report():
        exit("")
    if not week_test_process.week_test_increase_score_plan():
        exit("")
    if not week_test_process.down_task():
        logger.warn("一周速测下载失败")

    # 老师
    if not week_test_process.login(week_test_process.teacher_account, week_test_process.teacher_password):
        exit("")
    if not week_test_process.check_feedback():
        exit("")
    deal_time2 = time.time()
    real_wait_time = DOWNLOAD_PAPER_WAIT_TIME
    if deal_time2 - deal_time1 < DOWNLOAD_PAPER_WAIT_TIME:
        left_time = DOWNLOAD_PAPER_WAIT_TIME - int(deal_time2-deal_time1)
        logger.info("%d秒后执行下载自主卷接口", left_time)
        time.sleep(left_time)
    else:
        real_wait_time = int(deal_time2 - deal_time1)
    if not week_test_process.download_paper():
        logger.error(week_test_process.paper_name+",布置任务%d秒后，仍无法获取下载地址", real_wait_time)
    if not week_test_process.teacher_check_homework():
        exit("")

    exit("一周速测流程测试通过")



