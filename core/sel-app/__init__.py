#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging


def _create_logger(log_name, log_file):
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log = logging.getLogger(log_name)
    log.setLevel(logging.INFO)

    fh = logging.FileHandler(log_file)
    fh.setFormatter(fmt)
    fh.setLevel(logging.INFO)
    log.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    sh.setLevel(logging.WARNING)
    log.addHandler(sh)

    return log

log = _create_logger('sel', 'sel.log')

from .sel import *  # noqa
