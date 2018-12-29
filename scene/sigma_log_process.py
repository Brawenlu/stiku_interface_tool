#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import time
import datetime
from elasticsearch import Elasticsearch
from util.common_fun import CommonFun
from service.zentao_service import ZentaoService
from util.log import logger
import csv
import smtplib
from email.mime.text import MIMEText
from email.header import Header

class SigmaLogProcess:
    def __init__(self):
        self.es = Elasticsearch("http://120.27.45.89:9201")

    def get_log_record_count(self, query_index):
        query_body = {"query":{"bool":{"must":[{"query_string":{"default_field":"_all","query":"ERROR"}},
                                               {"query_string":{"default_field":"_all","query":"at com.yisi.stiku"}}
                                               ]}},
                      "size":0}
        res = self.es.search(index=query_index, body=query_body)
        return res["hits"]["total"]

    def get_hit_list(self, query_index):
        hit_count = self.get_log_record_count(query_index)
        query_body = {"query":{"bool":{"must":[{"query_string":{"default_field":"_all","query":"ERROR"}},
                                               {"query_string":{"default_field":"_all","query":"at com.yisi.stiku"}}
                                               ]}},
                      "size":hit_count}
        res = self.es.search(index=query_index, body=query_body)
        return res["hits"]["hits"]

    def analysis_err(self, hit_list):
        key_word_list = list()
        err_message_detail_list = list()
        repeat_dict = dict()
        start_find_key = "com.yisi.stiku."
        end_find_key1 = "\n"
        end_find_key2 = " "
        for hit in hit_list:
            err_message = hit["_source"]["message"]
            start_index = err_message.find(start_find_key)
            end_index = err_message.find(end_find_key1)
            key = err_message[start_index+len(start_find_key):end_index]
            if end_index > 150:
                end_index = key.find(end_find_key2)
                key = key[0:end_index]
            if key not in key_word_list:
                key_word_list.append(key)
                repeat_dict[key] = 1
                err_message_detail = dict()
                err_message_detail["timestamp"] = hit["_source"]["@timestamp"]
                err_message_detail["message"] = err_message
                err_message_detail_list.append(err_message_detail)
            else:
                repeat_dict[key] += 1

        return key_word_list,err_message_detail_list,repeat_dict

    def record_err(self, log_name, key_word_list, err_message_detail_list):
        with open(log_name+".csv",mode="w",newline='') as csv_file:
            writer = csv.writer(csv_file,)
            for index in range(len(key_word_list)):
                key_word = key_word_list[index]
                err_detail = err_message_detail_list[index]
                row = list()
                row.append(key_word)

                utc_time_str = err_detail["timestamp"]
                local_time_str = CommonFun.get_utc_to_local_time(utc_time_str)
                row.append(local_time_str)
                row.append(err_detail["message"])
                writer.writerow(row)

    def get_bug_content_in_zentao(self,utc_time,message):
        local_time = CommonFun.get_utc_to_local_time(utc_time)
        content = "<pre>time:%s<br/>%s</pre>" % (local_time, message)
        return content

    def save_in_zentao(self, module_id, key_word_list, err_message_detail_list):
        zentao_service = ZentaoService()
        update_count = 0
        new_insert_id_list = list()
        exist_id_list = list()
        for index in range(len(key_word_list)):
            key_word = key_word_list[index]
            err_detail = err_message_detail_list[index]
            exist_id = zentao_service.check_bug_exist(key_word)
            if exist_id != 0:
                bug_detail = dict()
                bug_detail["id"] = exist_id
                bug_detail["title"] = key_word
                exist_id_list.append(bug_detail)
                logger.debug("%s 已经存在", key_word)
                zentao_service.update_bug(exist_id, self.get_bug_content_in_zentao(err_detail["timestamp"], err_detail["message"]))
            else:
                logger.debug("ready_update:%s",key_word)
                bug_info = dict()
                bug_info["product_id"] = 2
                bug_info["module_id"] = module_id
                bug_info["project_id"] = 0
                bug_info["story_version"] = 1
                bug_info["title"] = key_word
                bug_info["severity"] = 1
                bug_info["pri"] = 1
                bug_info["type"] = "codeerror"
                bug_info["steps"] = self.get_bug_content_in_zentao(err_detail["timestamp"], err_detail["message"])
                bug_info["openedBy"] = "robot"
                bug_info["openedDate"] = time.strftime("%Y-%m-%d %H:%M:%S")
                bug_info["openedBuild"] = 7 #环境
                bug_info["assignedTo"] = "huangchen" # 指派给

                insert_id = zentao_service.insert_bug(bug_info)
                update_count += 1
                bug_detail = dict()
                bug_detail["id"] = insert_id
                bug_detail["title"] = key_word
                new_insert_id_list.append(bug_detail)
        return update_count,new_insert_id_list,exist_id_list

    def send_mail(self, target_date, sigma_insert_list, rpc_insert_list,
                  sigma_exist_list,rpc_exist_list,sigma_repeat_dict,rpc_repeat_dict):
        sender = 'hao.jiang@17daxue.com'
        to_receivers = ['hao.jiang@17daxue.com']
        cc_receivers = ['hao.jiang@17daxue.com']
        subject = '服务器西格玛报错跟踪记录_'+target_date
        smtpserver = 'smtp.17daxue.com'
        username = 'hao.jiang@17daxue.com'
        password = 'Jianghao1111'

        mail_content = "<html><body><h2>一、sigma</h2><table border=1px style='border-collapse:collapse'>"
        if len(sigma_insert_list) > 0:
            mail_content += "<tr><th>bug编号</th><th>标题</th></tr>"
            for sigma_insert_info in sigma_insert_list:
                mail_content += "<tr><td>%s（新增）</td><td>%s</td></tr>" % (str(sigma_insert_info["id"]),sigma_insert_info["title"])

        if len(sigma_exist_list) > 0:
            mail_content += "<tr><th>bug编号</th><th>标题</th></tr>"
            for sigma_exist_info in sigma_exist_list:
                mail_content += "<tr><td>%s（%s次）</td><td>%s</td></tr>" % \
                                (sigma_exist_info["id"],sigma_repeat_dict[sigma_exist_info["title"]],sigma_exist_info["title"])
        mail_content += "</table>"

        mail_content += "<html><body><h2>二、student_rpc</h2><table border=1px style='border-collapse:collapse'>"
        if len(rpc_insert_list) > 0:
            mail_content += "<tr><th>bug编号</th><th>标题</th></tr>"
            for rpc_insert_info in rpc_insert_list:
                mail_content += "<tr><td>%s（新增）</td><td>%s</td></tr>" % (str(rpc_insert_info["id"]),rpc_insert_info["title"])

        if len(rpc_exist_list) > 0:
            mail_content += "<tr><th>bug编号</th><th>标题</th></tr>"
            for rpc_exist_info in rpc_exist_list:
                mail_content += "<tr><td>%s（%s次）</td><td>%s</td></tr>" % \
                                (rpc_exist_info["id"],rpc_repeat_dict[rpc_exist_info["title"]],rpc_exist_info["title"])

        mail_content += "</table></body></html>"

        msg = MIMEText(mail_content,'html','utf-8')
        msg['From'] = Header(sender, 'utf-8')
        msg['To'] = Header(";".join(to_receivers), 'utf-8')
        msg['Cc'] = Header(";".join(cc_receivers), 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')

        smtp = smtplib.SMTP()
        smtp.connect('smtp.qq.com')
        smtp.login(username, password)
        smtp.sendmail(sender, to_receivers+cc_receivers, msg.as_string())
        smtp.quit()


if __name__ == "__main__":
    sigma_log = SigmaLogProcess()
    for i in range(-1, 0):
        target_date = CommonFun.get_next_n_day_date("%Y%m%d", i)
        # web_sigma
        web_sigma_index = "web-sigma_"+target_date
        web_sigma_hit_list = sigma_log.get_hit_list(web_sigma_index)
        key_word_list,err_message_detail_list,sigma_repeat_dict = sigma_log.analysis_err(web_sigma_hit_list)
        web_sigma_log_name = "web_sigma_log_"+str(len(key_word_list))+"个_"+target_date
        sigma_log.record_err(web_sigma_log_name, key_word_list, err_message_detail_list)
        update_count,sigma_insert_list,sigma_exist_list = sigma_log.save_in_zentao(234, key_word_list,
                                                                                   err_message_detail_list)
        logger.info("%s总命中%d", web_sigma_index, len(web_sigma_hit_list))
        logger.info("%s错误关键字%d个", web_sigma_index, len(key_word_list))
        logger.info("%s,本次更新%s个",web_sigma_index,update_count)

        # student_rpc
        student_rpc_index = "web-rpc-student_"+target_date
        student_rpc_hit_list = sigma_log.get_hit_list(student_rpc_index)
        key_word_list,err_message_detail_list,rpc_repeat_dict = sigma_log.analysis_err(student_rpc_hit_list)
        logger.info("%s总命中%d", web_sigma_index, len(student_rpc_hit_list))
        logger.info("%s错误关键字%d个", web_sigma_index, len(key_word_list))
        student_rpc_log_name ="student_rpc_log_"+str(len(key_word_list))+"个_"+target_date
        sigma_log.record_err(student_rpc_log_name, key_word_list, err_message_detail_list)
        update_count,rpc_insert_list,rpc_exist_list = sigma_log.save_in_zentao(235, key_word_list,
                                                                               err_message_detail_list)
        logger.info("%s,本次更新%s个",student_rpc_index,update_count)

        sigma_log.send_mail(target_date,sigma_insert_list,rpc_insert_list,sigma_exist_list,rpc_exist_list,
                            sigma_repeat_dict,rpc_repeat_dict)
    input("press to exit")
