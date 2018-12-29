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
from service.sigma_service import SigmaService
from service.common_service import CommonService
from config.common_config import *
import re
import random
import time
import json
from util.log import logger


SEQUENCE_COUNT = 10

class ManualMakePaper():
    def __init__(self):
        root_dir = FileUtil.get_app_root_dir()
        cur_env = FileUtil.get_cur_env()
        self.http_util = HttpConnectMgr.get_http_connect()
        self.jy_host = DomainMgr.get_domain("jy_host")
        self.student_service = StudentService()
        self.problem_service = ProblemService()
        self.teacher_week_test_id = 0
        self.cur_problem_index = 0
        self.problem_id_list = list()
        self.err_problem_list = list()

    def login(self, account, password):
        login_param = dict()
        login_param['loginName'] = account
        login_param['password'] = password
        login_res, login_code = AccountMgr.login(login_param)
        if re.search("错误报告", login_res):
            logger.error("(%s)login fail,please check you card and password" % account)
            return False
        return True

    def vertify_do_test(self, interface, response, vertify_param):
        if re.search("错误报告", response):
            logger.error("book:%s,出错题号列表：%s", vertify_param["book_version"],vertify_param["problem_ids"])
            self.err_problem_list.append(vertify_param["problem_ids"])
            return False
        response_json = json.loads(response)
        if response_json["success"] is False:
            logger.error("book:%s,出错题号列表：%s", vertify_param["book_version"],vertify_param["problem_ids"])
            self.err_problem_list.append(vertify_param["problem_ids"])
            return False
        return True

    def get_all_problem_list(self):
        self.problem_id_list = list()
        problem_ids = self.problem_service.get_problem_model_prom_problem_ids()
        for problem in problem_ids:
            self.problem_id_list.append(problem[0])
        """self.problem_id_list=[26304,26305,26306,26307,26308,26309,26310,26311,26312,26314,
26529,26531,26532,26533,26534,26535,26536,26537,26538,26539,
26815,26816,26817,26818,26819,26820,26822,26823,26824,26825,
26826,26828,26829,26830,26831,26832,26833,26834,26835,26836,
26859,26860,26861,26862,26863,26864,26865,26866,26868,26869,
26871,26873,26874,26875,26876,26877,26878,26879,26880,26881,
27114,27116,27117,27118,27119,27120,27121,27123,27124,27125,
27126,27127,27128,27130,27131,27132,27133,27134,27135,27137,
27159,27160,27161,27162,27163,27164,27165,27166,27167,27168,
27180,27181,27182,27183,27184,27185,27186,27187,27188,27189,
27255,27256,27257,27258,27259,27260,27262,27263,27264,27265,
27446,27447,27448,27449,27450,27451,27452,27453,27454,27455,
27578,27581,27582,27583,27584,27585,27586,27587,27588,27589,
27600,27601,27602,27603,27604,27605,27606,27607,27608,27610,
28581,28582,28583,28584,28585,28586,28587,28588,28589,28590,
28591,28592,28593,28594,28595,28596,28600,28601,28602,28603,
28758,28759,28760,28761,28762,28763,28764,28765,28766,28768,
28780,28781,28782,28783,28784,32023,32024,32026,32031,32032,]"""

    def get_select_problem_ids(self):
        problem_count = 0
        select_problem_list = ""
        for problem_id in self.problem_id_list[self.cur_problem_index:]:
            select_problem_list += str(problem_id)
            problem_count += 1
            if problem_count == SEQUENCE_COUNT:
                self.cur_problem_index += SEQUENCE_COUNT
                break
            else:
                select_problem_list += ","
        return select_problem_list

    def do_test(self, book_version):
        self.get_all_problem_list()
        id_count = len(self.problem_id_list)
        logger.info("题目数量=%d", id_count)
        if id_count%SEQUENCE_COUNT == 0:
            loop_count = int(id_count/SEQUENCE_COUNT)
        else:
            loop_count = int(id_count/SEQUENCE_COUNT + 1)
        logger.info("loop_count=%d", loop_count)
        for index in range(loop_count):
            select_problem_list = self.get_select_problem_ids()
            logger.debug("curr_index=%d,problem_list=%s",index,str(select_problem_list))
            do_test = InterfaceMgr.get_interface("web_jy", "do_test")
            do_test_param = dict()
            do_test_param["problemIds"] = select_problem_list
            do_test_param["bookVersions"] = book_version
            if not CommonFun.test_interface(self.jy_host, do_test, "post", do_test_param, self.vertify_do_test,
                                            {"problem_ids":select_problem_list, "book_version":book_version}):
                pass
            time.sleep(0.1)
        return True

if __name__ == "__main__":
    make_paper = ManualMakePaper()
    if not make_paper.login("xjy_jh","123456"):
        exit("")
    logger.info("人教a标准版开始")
    if not make_paper.do_test("RENJIAOSTANDARD"):
        exit("")
    logger.info("人教a版开始")
    if not make_paper.do_test("RENJIAO"):
        exit("")
    logger.info(str(make_paper.err_problem_list))

