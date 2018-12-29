#!/usr/bin/env python
# coding:utf-8

import logging
import time

logger = logging.getLogger("")
logger.setLevel(logging.INFO) # 改这里


ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

log_name = time.strftime("%Y_%m_%d_%H_%M_%S") + "_log.html"
fh = logging.FileHandler(log_name)
fh.setLevel(logging.INFO)

formatter = logging.Formatter("[%(levelname)s][%(asctime)s][%(funcName)s][line=%(lineno)d]  %(message)s")
ch.setFormatter(formatter)
fh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)