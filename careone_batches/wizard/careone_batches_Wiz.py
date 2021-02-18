# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from datetime import datetime, date, time
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrAttendanceEmployees(models.TransientModel):
    _name = 'hr.attendance.employees'

    field1 = fields.Many2one('hr.department',string='Department')
    field2 = fields.Many2one('hr.employee.category',string='Tags')
    field3 = fields.Many2one('res.company',string='Company_id')

    def _get_available_contracts_domain(self):
        return [('contract_ids.state', 'in', ('open', 'close'))]
        # , ('company_id', '=', self.env.company.id)

    def _get_employees(self):
        # YTI check dates too
        return self.env['hr.employee'].search(self._get_available_contracts_domain())

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rell', 'payslip_idd', 'employee_idd', 'Employeess',
                                    default=lambda self: self._get_employees(), required=True )
    structure_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')

    @api.onchange('field1' ,'field2','field3')
    def onchange_supplier(self):
        selected_lines = []
        if self.field1 :
            for rec in self:
                selected_lines = rec.env['hr.employee'].search([('department_id', '=', rec.field1.id)])
                self.employee_ids=[(6,0,selected_lines.ids)]
        if self.field2:
            for rec in self:
                selected_lines = rec.env['hr.employee'].search([('category_ids', '=', rec.field2.id)])
                self.employee_ids=[(6,0,selected_lines.ids)]
        if self.field3:
            for rec in self:
                selected_lines = rec.env['hr.employee'].search([('company_id', '=', rec.field3.id)])
                self.employee_ids=[(6,0,selected_lines.ids)]





    def _check_undefined_slots(self, work_entries, payslip_run):
        """
        Check if a time slot in the contract's calendar is not covered by a work entry
        """
        work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])
        for work_entry in work_entries:
            work_entries_by_contract[work_entry.contract_id] |= work_entry

        for contract, work_entries in work_entries_by_contract.items():
            calendar_start = pytz.utc.localize(datetime.combine(max(contract.date_start, payslip_run.date_start), time.min))
            calendar_end = pytz.utc.localize(datetime.combine(min(contract.date_end or date.max, payslip_run.date_end), time.max))
            outside = contract.resource_calendar_id._attendance_intervals_batch(calendar_start, calendar_end)[False] - work_entries._to_intervals()
            if outside:
                raise UserError(_("Some part of %s's calendar is not covered by any work entry. Please complete the schedule.") % contract.employee_id.name)

    def compute_sheet(self):
        active_id = self.env.context.get('active_id')
        attendance_sheet_run = self.env['hr.attendance.run'].browse(active_id)
        for value in self.employee_ids:
            contract = self.env['hr.contract'].search([('employee_id','=',value.id),('state','=','open')])
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
class Batchchatt(models.Model):
    _inherit="attendance.sheet"
    batattempid=fields.Many2one('hr.attendance.run')
