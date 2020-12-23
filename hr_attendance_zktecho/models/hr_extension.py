# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrAttendance(models.Model):
    
    _inherit = 'hr.attendance'
    
    name = fields.Datetime('Datetime')
    day = fields.Date("Day")
    is_missing = fields.Boolean('Missing', default=False)


class hrDraftAttendance(models.Model):

    _name = 'hr.draft.attendance'
    _inherit = ['mail.thread']
    _order = 'name desc'
    
    name = fields.Datetime('Datetime', required=False)
    date = fields.Date('Date', required=False)
    day_name = fields.Char('Day')
    attendance_status = fields.Selection([('sign_in', 'Sign In'), ('sign_out', 'Sign Out'), ('sign_none', 'None')], 'Attendance State', required=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    lock_attendance = fields.Boolean('Lock Attendance')
    biometric_attendance_id = fields.Integer(string='Biometric Attendance ID')
    is_missing = fields.Boolean('Missing', default=False)


class Employee(models.Model):
    
    _inherit = 'hr.employee'
    
    is_shift = fields.Boolean("Shifted Employee")
    attendance_devices = fields.One2many(comodel_name='employee.attendance.devices', inverse_name='name', string='Attendance')
    

class EmployeeAttendanceDevices(models.Model):
    
    _name = 'employee.attendance.devices'
    
    name = fields.Many2one(comodel_name='hr.employee', string='Employee')
    attendance_id = fields.Char("Attendance ID", required=True)
    device_id = fields.Many2one(comodel_name='biomteric.device.info', string='Biometric Device', required=True, ondelete='restrict')
    
    @api.one
    @api.constrains('attendance_id', 'device_id', 'name')
    def _check_unique_constraint(self):
        self.ensure_one()
        record = self.search([('attendance_id', '=', self.attendance_id), ('device_id', '=', self.device_id.id)])
        if len(record) > 1:
            raise ValidationError('Employee with Id ('+ str(self.attendance_id)+') exists on Device ('+ str(self.device_id.name)+') !')
        record = self.search([('name', '=', self.name.id), ('device_id', '=', self.device_id.id)])
        if len(record) > 1:
            raise ValidationError('Configuration for Device ('+ str(self.device_id.name)+') of Employee  ('+ str(self.name.name)+') already exists!')
