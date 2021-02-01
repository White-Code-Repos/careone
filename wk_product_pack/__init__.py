#  -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2019-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
from . import models
from . import wizard


def pre_init_check(cr):
	from odoo.service import common
	from odoo.exceptions import Warning
	version_info = common.exp_version()
	server_serie =version_info.get('server_serie')
	if server_serie!='13.0':raise Warning('Module support Odoo series 13.0 found {}.'.format(server_serie))
	return True