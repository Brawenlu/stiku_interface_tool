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
import urllib.parse


class VideoMatch:
    def __init__(self):
        self.root_dir = FileUtil.get_app_root_dir()
        self.cur_env = FileUtil.get_cur_env()
        self.problem_service = ProblemService()
        self.http_util = HttpConnectMgr.get_http_connect()
        self.jy_host = DomainMgr.get_domain("jy_host")
        self.video_host = DomainMgr.get_domain("video_host")
        self.student_service = StudentService()
        self.problem_service = ProblemService()

    def vertify_get_aliyun_video_url_by_vu(self, interface, response, vertify_param):
        aliyun_oss_key = vertify_param["aliyun_oss_key"]
        vu = vertify_param["vu"]
        response_json = json.loads(response)
        if response_json["TYPE_SUCCESS"] != "success":
            return False
        if response_json["message"] == "该视频无阿里云路径":
            if response_json["attribute"]["vu"] != vu:
                return False
        else:
            res_aliyun_oss_key = response_json["attribute"]["aliyunOssKey"]
            param_aliyun_oss_key_parse = urllib.parse.quote(aliyun_oss_key)
            db_aliyun_oss_key = "http://"+self.video_host + param_aliyun_oss_key_parse
            if res_aliyun_oss_key.split("?")[0] != db_aliyun_oss_key:
                logger.error("vu=%s,db_oss_key=%s",vu,db_aliyun_oss_key)
                return False
        return True

    def test_problem_video_url(self):
        all_problem_ids = self.problem_service.get_all_jiexi_video()
        logger.debug("题目共%s个", len(all_problem_ids))
        err_video_problems = list()
        for problem_line in all_problem_ids:
            problem_id = problem_line[0]
            vu = problem_line[1]
            aliyun_oss_key = problem_line[2]
            if aliyun_oss_key is None:
                aliyun_oss_key = ""
            get_aliyun_video_url_by_vu = InterfaceMgr.get_interface("web_jy", "get_aliyun_video_url_by_vu")
            get_aliyun_video_url_by_vu_param = dict()
            get_aliyun_video_url_by_vu_param["vu"] = vu
            if not CommonFun.test_interface(self.jy_host, get_aliyun_video_url_by_vu,
                                            "get", get_aliyun_video_url_by_vu_param,
                                            self.vertify_get_aliyun_video_url_by_vu,
                                            {"aliyun_oss_key":aliyun_oss_key,"vu":vu}):
                err_video_problems.append(problem_id)
            logger.debug("已处理 %s", problem_id)
        logger.info("视频出错题目数：%s", len(err_video_problems))

if __name__ == "__main__":
    video_match = VideoMatch()
    video_match.test_problem_video_url()