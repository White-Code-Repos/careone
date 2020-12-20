
from odoo import models, fields, api, tools, _
import babel
import time
from datetime import datetime, timedelta



class HrOvertimeRule(models.Model):
    _inherit = 'hr.overtime.rule'

    active_after = fields.Float(string="Apply Limit",
                                help="After this time the overtime will be calculated")
    up_to_3h_rate = fields.Float(string='Up to 3h Rate')
    over_3h_rate = fields.Float(string=' After 3h Rate')
