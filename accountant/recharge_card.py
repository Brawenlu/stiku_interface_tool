#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
from util.mysql_util import MysqlUtil
from util.file_util import FileUtil
from util.account_mgr import AccountMgr
from util.http_util import HttpConnectMgr
from util.domain_mgr import DomainMgr
import time
import re


def get_recharge_card_pass(card_count):
    """获取激活卡密码"""
    card_pass_list = []
    root_dir = FileUtil.get_app_root_dir()
    cur_env = FileUtil.get_cur_env()
    mysql_util = MysqlUtil()
    conn = mysql_util.connect(cur_env, root_dir+"/config/wallet_db_config.ini")
    cursor = conn.cursor()
    sql = "select act_code,TYPE from `recharge_card` as rc,`rechargecard_batch` as rb where rc.batch_id = rb.id and rc.state = 0 and rb.NAME like '测试%' AND TYPE=500 limit " + str(card_count)
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    mysql_util.close()
    for card_info in data:
        card_pass_list.append(card_info)
    return card_pass_list


def get_recharge_person_list():
    root_dir = FileUtil.get_app_root_dir()
    person_list = AccountMgr.get_account_list(root_dir+"/accountant/charge_list.csv")
    return person_list


def generate_new_rechage_card():
    print("lack charge code,now generating new charge code ...")
    account_info = AccountMgr.get_accountant_account()
    AccountMgr.login(account_info)
    host = DomainMgr.get_domain("ms_host")
    http_util = HttpConnectMgr.get_http_connect()
    batch_name = "测试_" + time.strftime("%Y%m%d_%H%M%S", time.localtime())
    response,res_code = http_util.post(host, "/web-ms/wallet/rechargecard/addRechargeCardBatch",
                    {'Name':batch_name, 'CardType':'500', 'TypeAttr':'12', 'TotalNum':'50'})
    if re.search("插入卡批成功",response):
        print("generated 50 cards,every card has 500 magic beans")
    else:
        print("fail to generate charge card")
    AccountMgr.logout()


def rechage_card(card_code):
    http_util = HttpConnectMgr.get_http_connect()
    host = DomainMgr.get_domain("passport_host")
    params = dict()
    params["actCode"] = card_code
    response,res_code = http_util.post(host, "/web-passport/account/rechargeCard", params)
    if re.search("操作成功!", response):
        return True
    else:
        return False

if __name__ == '__main__':
    person_list = get_recharge_person_list()
    pass_list = get_recharge_card_pass(len(person_list))

    if len(pass_list) < len(person_list):
        generate_new_rechage_card()

    pass_list = get_recharge_card_pass(len(person_list))
    for index, person_info in enumerate(person_list):
        account_info = dict()
        account_info['loginName'] = person_info[0]
        account_info['password'] = person_info[1]
        #login
        login_res,res_code = AccountMgr.login(account_info)
        print(login_res)
        if re.search("错误报告", login_res):
            print("[%s] login fail,please check you card and password" % person_info[0])
            continue
        if rechage_card(pass_list[index][0]):
            print("loginName="+person_info[0]+";code="+str(pass_list[index][0])+",charge succeed"+str(pass_list[index][1]))
        else:
            print("loginName="+person_info[0]+";code="+str(pass_list[index][0])+",charge fail")
        AccountMgr.logout()
    input("press enter to exit")