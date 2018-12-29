#!/usr/bin/env python
# -*- coding:utf-8 -*-

from util.file_util import FileUtil
from util.mysql_util import MysqlUtil
from util.log import logger

class ZentaoService:
    def __init__(self):
        self.root_dir = FileUtil.get_app_root_dir()
        self.cur_env = FileUtil.get_cur_env()

    def update_bug(self, id, bug_content):
        mysql_util = MysqlUtil()
        conn = mysql_util.connect_ignore_env("zentao", self.root_dir+"/config/zentao_db_config.ini")
        cursor = conn.cursor()
        cursor.execute("update `zt_bug` set steps=%s where id=%s", (bug_content, id))
        cursor.close()
        mysql_util.close()

    def check_bug_exist(self, bug_title):
        bug_id = 0
        mysql_util = MysqlUtil()
        conn = mysql_util.connect_ignore_env("zentao", self.root_dir+"/config/zentao_db_config.ini")
        cursor = conn.cursor()
        sql = "SELECT id FROM `zt_bug` WHERE title = '"+str(bug_title)+"'"
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()
        mysql_util.close()
        if len(data) > 0:
            bug_id = data[0][0]
        return bug_id

    """insert into `zt_bug`(id,product,module,storyVersion,title,severity,pri,type,steps,openedBy,openedDate,openedBuild,assignedTo)
            values("1138","2","235","1","jianghao","1","1","codeerror","jianghao","jianghao","2016-11-25 12:28:14","7","jianghao")
    """
    def insert_bug(self, bug_info):
        product_id = bug_info["product_id"]
        module_id = bug_info["module_id"]
        project_id = bug_info["project_id"]
        story_version = bug_info["story_version"] or 1
        bug_title = bug_info["title"]
        severity = bug_info["severity"] or 1
        pri = bug_info["pri"] or 1
        type = bug_info["type"] or "codeerror"
        steps = bug_info["steps"]
        opened_by = bug_info["openedBy"]
        opened_date = bug_info["openedDate"]
        opened_build = bug_info["openedBuild"]
        assigned_to = bug_info["assignedTo"]

        mysql_util = MysqlUtil()
        conn = mysql_util.connect_ignore_env("zentao", self.root_dir+"/config/zentao_db_config.ini")
        cursor = conn.cursor()
        """sql = "insert into `zt_bug`(`product`,`module`,`project`,`storyVersion`,`title`," \
              "`keywords`,`severity`,`pri`,`type`,`hardware`," \
              "`steps`,`activatedCount`,`openedBy`,`openedDate`,`openedBuild`," \
              "`assignedTo`,`assignedDate`,`resolvedDate`,`closedDate`,`duplicateBug`," \
              "`linkBug`,`case`,`result`,`testtask`,`lastEditedDate`) " \
              "values('%s','%s','%s','%s','%s'," \
              "'%s','%s','%s','%s','%s'," \
              "%s,'%s','%s','%s','%s'," \
            "'%s','%s','%s','%s','%s'," \
            "'%s','%s','%s','%s','%s')" % \
              (product_id,module_id,project_id,story_version,bug_title,
               "",severity,pri,type,"",
               '"'+steps+'"',0,opened_by,opened_date,opened_build,
               assigned_to,opened_date,"0000-00-00 00:00:00","0000-00-00 00:00:00",0,
               "",0,0,0,"0000-00-00 00:00:00")
        cursor.execute(sql)"""
        default_date_time = "0000-00-00 00:00:00"
        cursor.execute("insert into `zt_bug`(`product`,`module`,`project`,`storyVersion`,`title`," \
              "`keywords`,`severity`,`pri`,`type`,`hardware`," \
              "`steps`,`activatedCount`,`openedBy`,`openedDate`,`openedBuild`," \
              "`assignedTo`,`assignedDate`,`resolvedDate`,`closedDate`,`duplicateBug`," \
              "`linkBug`,`case`,`result`,`testtask`,`lastEditedDate`) " \
              "values(%s,%s,%s,%s,%s," \
              "%s,%s,%s,%s,%s," \
              "%s,%s,%s,%s,%s," \
            "%s,%s,%s,%s,%s," \
            "%s,%s,%s,%s,%s)",(product_id,module_id,project_id,story_version,bug_title,
               "",severity,pri,type,"",
               steps,0,opened_by,opened_date,opened_build,
               assigned_to,opened_date,default_date_time,default_date_time,0,
               "",0,0,0,default_date_time))
        insert_id = conn.insert_id()

        action_info = dict()
        action_info["object_type"] = "bug"
        action_info["object_id"] = insert_id
        action_info["product"] = product_id
        action_info["project"] = project_id
        action_info["actor"] = opened_by
        action_info["action"] = "opened"
        action_info["date"] = opened_date

        sql = "insert into `zt_action`(`objectType`,`objectId`,`product`,`project`,`actor`,`action`,`date`,`comment`,`extra`,`read`) " \
              "values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % \
              ("bug",insert_id,product_id,project_id,opened_by,"opened",opened_date,"","",0)
        cursor.execute(sql)

        insert_id2 = conn.insert_id()
        cursor.close()
        mysql_util.close()
        return insert_id

    """insert into `zt_action`(objectType,objectId,product,project,actor,action,date)
        values("bug","1138",",0,","0","jianghao","opened","2016-11-25 12:28:14")"""
    def insert_action(self, action_info):
        object_type = action_info["object_type"]
        object_id = action_info["object_id"]
        product = action_info["product"]
        project = action_info["project"]
        actor = action_info["actor"]
        action = action_info["action"]
        date = action_info["date"]

        mysql_util = MysqlUtil()
        conn = mysql_util.connect("zentao", self.root_dir+"/config/zentao_db_config.ini")
        cursor = conn.cursor()
        sql = "insert into `zt_action`(objectType,objectId,product,project,actor,action,date) " \
              "values('%s','%s','%s','%s','%s','%s','%s')" % (object_type,object_id,product,project,actor,action,date)
        cursor.execute(sql)
        cursor.close()
        mysql_util.close()