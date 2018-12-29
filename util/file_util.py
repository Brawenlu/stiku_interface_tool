#!/usr/bin/env python
# -*- coding:utf-8 -*-
import codecs
import configparser
import os
import sys
import platform
import csv

__author__ = 'jianghao'


class FileUtil:
    def __init__(self):
        pass

    @staticmethod
    def create_file(file_name, content):
        file_obj = codecs.open(file_name, "w", encoding="utf-8")
       # content = content.encode('utf-8')
        file_obj.write(content)
        file_obj.close()

    @staticmethod
    def get_cur_dir():
        #获取脚本路径
        path = os.getcwd()
        return path

    @staticmethod
    def get_app_root_dir():
        app_name = "stiku_interface_tool"
        curr_dir = FileUtil.get_cur_dir()
        app_name_index = curr_dir.rfind(app_name)
        root_dir = curr_dir[0:app_name_index]
        app_root_dir = root_dir+app_name
        return app_root_dir

    @staticmethod
    def get_cur_env():
        root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(root_dir+"/config/curr_env.ini")
        cur_env = ini_util.get_item_attr("env", "curr_env")
        return cur_env


class IniUtil:
    def __init__(self, file_name):
        self.cf = configparser.ConfigParser()
        self.cf.read(file_name, encoding='utf-8')

    def get_cf(self):
        return self.cf

    def get_item_attr(self, section, item_name):
        return self.cf.get(section, item_name)
