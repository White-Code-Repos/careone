# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2020-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################

import pytz
from datetime import datetime, date, timedelta, time
from dateutil.relativedelta import relativedelta
from odoo import models, fields, tools, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY, \
    make_aware, datetime_to_string, string_to_datetime

DATETIME_FORMAT = "%D-%m-%Y %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


class batches_attendance_(models.Model):
    _name = 'hr.attendance.run'
    _inherit = 'attendance.sheet'

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('attendance_sheet', 'Attendance Sheet'),
        ('payslip', 'Payslip'),
        ('done', 'Done'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    name = fields.Char(required=True, readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date(string='Date From', required=True, readonly=True,
                             states={'draft': [('readonly', False)]},
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_end = fields.Date(string='Date To', required=True, readonly=True,
                           states={'draft': [('readonly', False)]},
                           default=lambda self: fields.Date.to_string(
                               (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    att_count = fields.Integer(compute='_compute_att_count')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True,
                                 default=lambda self: self.env.company)

    def _compute_att_count(self):
        for attendance_run in self:
            atteandance = self.env['attendance.sheet'].search([('batattempid', '=', self.id)]).ids
            attendance_run.att_count = len(atteandance)

    def generatepayslip(self):
        atteandance = self.env['attendance.sheet'].search([('batattempid', '=', self.id)])
        for value in atteandance:
            value.action_confirm()
            value.action_approve()
        self.write({'state': 'payslip'})

    def confirmpayslip(self):
        atteandance = self.env['attendance.sheet'].search([('batattempid', '=', self.id)])
        for value in atteandance:
            value.payslip_id.compute_sheet()
            value.payslip_id.action_payslip_open()
        self.write({'state': 'done'})

    def action_open_attpay(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "attendance.sheet",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.env['attendance.sheet'].search([('batattempid', '=', self.id)]).ids]],
            "name": "Attendance Sheets",
        }
