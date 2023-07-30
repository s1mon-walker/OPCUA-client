#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .opc_ua import Opc_Ua
from ..config import config

opc_ua = Opc_Ua(config.plc_ip)
