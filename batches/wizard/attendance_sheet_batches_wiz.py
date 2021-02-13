# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from datetime import datetime, date, time
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _name = 'attendance.employees.payslip'

    def _get_employees(self):
        # YTI check dates too
        return self.env['hr.employee'].search(self._get_available_contracts_domain())

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rell', 'payslip_idd', 'employee_idd', 'Employeess',
                                    default=lambda self: self._get_employees(), required=True)

    def compute_sheet(self):
        active_id = self.env.context.get('active_id')
        attendance_sheet_run = self.env['hr.attendance.run'].browse(active_id)

        for value in self.employee_ids:

            contract = self.env['hr.contract'].search([('employee_id','=',value.id),('state','=','open')],limit=1)
            policy=contract.att_policy_id.id
            x=self.env['attendance.sheet'].create({
              'employee_id':value.id,
              'date_from':attendance_sheet_run.date_start,
              'date_to':attendance_sheet_run.date_end,
              'att_policy_id':policy,
              'batattempid':attendance_sheet_run.id
              })
            x.onchange_employee()
            x.get_attendances()
        attendance_sheet_run.state="attendance_sheet"

class Batchatt(models.Model):
    _inherit="attendance.sheet"
    batattempid=fields.Many2one('hr.attendance.run')




        # self.ensure_one()
