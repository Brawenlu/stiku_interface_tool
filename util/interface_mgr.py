#!/usr/bin/env python
# -*- coding:utf-8 -*-

from util.file_util import *


class InterfaceMgr:
    def __init__(self):
        pass

    @staticmethod
    def get_interface(terminal,interface_name):
        app_root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(app_root_dir+'/config/interfaces.ini')
        domain = ini_util.get_item_attr(terminal,interface_name)
        return domain