#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
from util.file_util import FileUtil
from util.account_mgr import AccountMgr
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
from util.interface_mgr import InterfaceMgr
from util.common_fun import CommonFun
from service.student_service import StudentService
from service.problem_service import ProblemService
import re
import time
from util.log import logger

class PreDownPaper:
    def __init__(self):
        root_dir = FileUtil.get_app_root_dir()
        cur_env = FileUtil.get_cur_env()
        self.http_util = HttpConnectMgr.get_http_connect()
        self.jy_host = DomainMgr.get_domain("jy_host")
        self.student_service = StudentService()
        self.problem_service = ProblemService()

    def get_need_down_test_papers(self):
        return self.problem_service.get_need_ajax_down_test_paper()

    def login(self, account, password):
        login_param = dict()
        login_param['loginName'] = account
        login_param['password'] = password
        login_res, login_code = AccountMgr.login(login_param)
        if re.search("错误报告", login_res):
            logger.error("(%s)login fail,please check you card and password" % account)
            return False
        return True

    def ajax_down_paper(self, need_no):
        test_papers = self.get_need_down_test_papers()
        logger.info("待执行 num=%d",len(test_papers))
        err_count = 0
        for test_paper in test_papers:
            ajax_down_exam_paper_pdf = InterfaceMgr.get_interface("web_jy", "ajax_down_exam_paper_pdf")
            ajax_down_exam_paper_pdf_param = dict()
            ajax_down_exam_paper_pdf_param["paperId"] = test_paper[0]
            ajax_down_exam_paper_pdf_param["isNeedNo"] = need_no
            if not CommonFun.test_interface(self.jy_host, ajax_down_exam_paper_pdf, "get",
                                            ajax_down_exam_paper_pdf_param,"0"):
                logger.error("paper_id=%s 下载失败",test_paper[0])
                err_count += 1
                return False
            else:
                logger.warning("paper_id=%s 下载成功",test_paper[0])
            time.sleep(0.5)
        logger.warning("下载失败 %d", err_count)
        return True

    def ajax_download_one(self, id, need_no):
        ajax_down_exam_paper_pdf = InterfaceMgr.get_interface("web_jy", "ajax_down_exam_paper_pdf")
        ajax_down_exam_paper_pdf_param = dict()
        ajax_down_exam_paper_pdf_param["paperId"] = id
        ajax_down_exam_paper_pdf_param["isNeedNo"] = need_no
        if not CommonFun.test_interface(self.jy_host, ajax_down_exam_paper_pdf, "get",
                                        ajax_down_exam_paper_pdf_param,"0"):
            logger.error("paper_id=%s 下载失败", id)
            return False
        return True

    # "http://17daxue-magazine.oss-cn-hangzhou.aliyuncs.com/2014年湖南省高考数学试卷（理科）_AT_LAST_1467686249430_20160705-103729-449.pdf"
    def check_date(self, url):
        paper_name = url.split("/")[3]
        paper_time_arr = paper_name.split("_")
        paper_time = paper_time_arr[len(paper_time_arr)-1]
        paper_date = paper_time.split("-")[0]
        if paper_date == "20161108":
            return True
        else:
            return False

    def check_result(self):
        test_papers = self.get_need_down_test_papers()
        no_answer_fail_count = 0
        with_answer_fail_count = 0
        for test_paper in test_papers:
            paper_id = test_paper[0]
            pdf_url_at_last = test_paper[1]
            pdf_url_no_answer = test_paper[2]
            if pdf_url_at_last is None or not self.check_date(pdf_url_at_last):
                with_answer_fail_count += 1
                logger.warning("paper_id=%s,pdf_url_at_last   验证失败", paper_id)
            if pdf_url_no_answer is None or not self.check_date(pdf_url_no_answer):
                no_answer_fail_count += 1
                logger.warning("paper_id=%s,pdf_url_no_answer 验证失败", paper_id)
        logger.debug("with_answer_fail_count = %d", with_answer_fail_count)
        logger.debug("no_answer_fail_count =  %d", no_answer_fail_count)

if __name__ == "__main__":
    pre_down_paper = PreDownPaper()
    if not pre_down_paper.login("xjy_jh", "123456"):
            exit("")
    """if not pre_down_paper.ajax_down_paper(False):
        exit("")
    if not pre_down_paper.ajax_down_paper(True):
        exit("")"""

    pre_down_paper.check_result()

    '''pre_down_paper.ajax_download_one(12246, True)
    pre_down_paper.ajax_download_one(12246, False)
    pre_down_paper.ajax_download_one(13101, True)
    pre_down_paper.ajax_download_one(13101, False)'''