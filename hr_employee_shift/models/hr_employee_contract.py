# -*- coding: utf-8 -*-
from odoo.exceptions import Warning
from odoo import models, fields, api, _


class HrEmployeeContract(models.Model):
    _inherit = 'hr.contract'

    shift_schedule = fields.One2many('hr.shift.schedule', 'rel_hr_schedule', string="Shift Schedule",
                                     help="Shift schedule", readonly=False)
    working_hours = fields.Many2one('resource.calendar', string='Working Schedule', help="Working hours")
    department_id = fields.Many2one('hr.department', string="Department", help="Department",
                                    required=True)

    @api.model
    def create(self, vals):
        res = super(HrEmployeeContract, self).create(vals)
        for line in self.shift_schedule:
            if line.id not in self.employee_id.shift_schedule.ids:
                self.employee_id.shift_schedule = [(6, 0, self.shift_schedule.ids)]
        return res

    def write(self, vals):
        res = super(HrEmployeeContract, self).write(vals)
        for line in self.shift_schedule:
            if line.id not in self.employee_id.shift_schedule.ids:
                self.employee_id.shift_schedule = [(6, 0, self.shift_schedule.ids)]
        return res


class HrSchedule(models.Model):
    _name = 'hr.shift.schedule'

    start_date = fields.Date(string="Date From", required=True, help="Starting date for the shift")
    end_date = fields.Date(string="Date To", required=True, help="Ending date for the shift")
    rel_hr_schedule = fields.Many2one('hr.contract')
    rel_hr_schedule1 = fields.Many2one('hr.employee')
    hr_shift = fields.Many2one('resource.calendar', string="Shift", required=True, help="Shift")
    company_id = fields.Many2one('res.company', string='Company', help="Company")

    # @api.onchange('start_date', 'end_date')
    # def get_department(self):
    #     """Adding domain to  the hr_shift field"""
    #     hr_department = None
    #     if self.start_date:
    #         hr_department = self.rel_hr_schedule.department_id.id
    #     return {
    #         'domain': {
    #             'hr_shift': [('hr_department', '=', hr_department)]
    #         }
    #     }

    def write(self, vals):
        self._check_overlap(vals)
        return super(HrSchedule, self).write(vals)

    @api.model
    def create(self, vals):
        self._check_overlap(vals)
        return super(HrSchedule, self).create(vals)

    def _check_overlap(self, vals):
        if vals.get('start_date', False) and vals.get('end_date', False):
            shifts = self.env['hr.shift.schedule'].search([('rel_hr_schedule', '=', vals.get('rel_hr_schedule'))])
            for each in shifts:
                if each != shifts[-1]:
                    if each.end_date >= vals.get('start_date') or each.start_date >= vals.get('start_date'):
                        raise Warning(_('The dates may not overlap with one another.'))
            if vals.get('start_date') > vals.get('end_date'):
                raise Warning(_('Start date should be less than end date.'))
        return True


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    shift_schedule = fields.One2many('hr.shift.schedule', 'rel_hr_schedule1', string="Shift Schedule")

    @api.model
    def create(self, vals):
        res = super(HrEmployee, self).create(vals)
        contract = self.env['hr.contract'].search([('employee_id.name', '=', res.name)], limit=1)
        if contract:
            contract.shift_schedule = [(6, 0, res.shift_schedule.ids)]
        return res

    def write(self, vals):
        res = super(HrEmployee, self).write(vals)
        for rec in self:
            contract = self.env['hr.contract'].search([('employee_id.name', '=', rec.name)], limit=1)
            if contract:
                contract.shift_schedule = [(6, 0, self.shift_schedule.ids)]
        return res
