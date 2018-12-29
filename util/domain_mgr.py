#!/usr/bin/env python
# -*- coding:utf-8 -*-

from util.file_util import *


class DomainMgr:
    def __init__(self):
        pass

    @staticmethod
    def get_domain(domain_name):
        cur_env = FileUtil.get_cur_env()
        app_root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(app_root_dir+'/config/domain.ini')
        domain = ini_util.get_item_attr(cur_env,domain_name)
        return domain
