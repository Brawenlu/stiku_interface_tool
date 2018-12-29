#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
import re
from util.file_util import FileUtil
from util.account_mgr import AccountMgr
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
from util.file_util import IniUtil
from service.student_service import StudentService
from service.problem_service import ProblemService
from service.sigma_service import SigmaService
import json
import random
import math
import types
from util.common_fun import CommonFun
from util.log import logger
import urllib.request
from util.interface_mgr import InterfaceMgr
import base64
import requests
import time
import datetime
from elasticsearch import Elasticsearch
from service.zentao_service import ZentaoService
import smtplib
from email.mime.text import MIMEText
from email.header import Header

def vertify_bug_browse(interface, res, vertify_param):
    logger.info(res)

def bug_view():
    zentao_host = DomainMgr.get_domain("zentao_host")
    bug_browse = InterfaceMgr.get_interface("zentao", "bug_view")
    if not CommonFun.test_interface(zentao_host,bug_browse,"get",None,vertify_bug_browse):
        return False
    return True

def zentao_login():
    zentao_host = DomainMgr.get_domain("zentao_host")
    zentao_login = InterfaceMgr.get_interface("zentao", "zentao_login")
    zentao_login_param = dict()
    zentao_login_param["account"] = "jianghao"
    zentao_login_param["password"] = "123456"
    zentao_login_param["referer"] = "http://bugfree.17daxue.com/zentao/dev-api-sso.html"
    if not CommonFun.test_interface(zentao_host,zentao_login,"post",zentao_login_param,None):
        return False
    return True


def save_bug_example():
    zentao_service = ZentaoService()

    bug_info = dict()
    bug_info["product_id"] = 2
    bug_info["module_id"] = 235
    bug_info["project_id"] = 0
    bug_info["story_version"] = 1
    bug_info["title"] = "robot"
    bug_info["severity"] = 1
    bug_info["pri"] = 1
    bug_info["type"] = "codeerror"
    bug_info["steps"] = "robot"
    bug_info["openedBy"] = "robot"
    bug_info["openedDate"] = time.strftime("%Y-%m-%d %H:%M:%S")
    bug_info["openedBuild"] = 7
    bug_info["assignedTo"] = "jianghao"
    zentao_service.insert_bug(bug_info)

def send_mail():
    sender = 'hao.jiang@17daxue.com'
    receivers = ['hao.jiang@17daxue.com',"1261218550@qq.com"]
    subject = 'python email test'
    smtpserver = 'smtp.17daxue.com'
    username = 'hao.jiang@17daxue.com'
    password = 'Jianghao1111'

    msg = MIMEText('<html><h1>你好</h1></html>','html','utf-8')
    msg['From'] = Header(sender, 'utf-8')
    msg['To'] = Header(";".join(receivers), 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    smtp = smtplib.SMTP()
    smtp.connect('smtp.qq.com')
    smtp.login(username, password)
    smtp.sendmail(sender, receivers, msg.as_string())
    smtp.quit()

# \((&nbsp;)*(\s)*\)
def test_problem_type():
    problem_service = ProblemService()
    xz_problems = problem_service.get_all_xz_problems()
    logger.info("xz_all_count = %s",len(xz_problems))
    count = 0
    not_xz_list = list()
    for xz_problem in xz_problems:
        sequence = xz_problem[1]
        content = xz_problem[2]
        if not re.search("\((\s)*(&nbsp;(\s)*)*(\s)*\)",content)\
                and not re.search("\（(\s)*(&nbsp;(\s)*)*(\s)*\）",content):
            count += 1
            not_xz_list.append(content);
    logger.info("xz_count=%s",count)
    print(not_xz_list[0])
    print(not_xz_list[3])

if __name__ == "__main__":
    test_problem_type()
    input("d")

