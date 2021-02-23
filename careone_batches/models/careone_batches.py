from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class AttPayslipRun(models.Model):
    _name = 'hr.attendance.run'

    name = fields.Char(required=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('attendance_sheet', 'Attendance Sheet'),
        ('confirmed', 'Confirmed'),
        ('payslip', 'Payslip'),
        ('done', 'Done'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    date_start = fields.Date(string='Date From', required=True, readonly=True,
                             states={'draft': [('readonly', False)]},
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_end = fields.Date(string='Date To', required=True, readonly=True,
                           states={'draft': [('readonly', False)]},
                           default=lambda self: fields.Date.to_string(
                               (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    credit_note = fields.Boolean(string='Credit Note', readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 help="If its checked, indicates that all payslips generated from here are refund payslips.")
    att_count = fields.Integer(compute='_compute_att_count')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True,
                                 states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env.company)

    def _compute_att_count(self):
        for attendance_run in self:
            atteandance = self.env['attendance.sheet'].search([('batattempid', '=', self.id)]).ids
            attendance_run.att_count = len(atteandance)

    def generatepayslip(self):
        atteandance = self.env['attendance.sheet'].search([('batattempid', '=', self.id)])
        for value in atteandance:
            value.action_confirm()
            # value.action_approve()
        self.write({'state': 'confirmed'})

    def confirmpayslip(self):
        atteandance = self.env['attendance.sheet'].search([('batattempid', '=', self.id)])
        for value in atteandance:
            value.action_approve()
            value.payslip_id.compute_sheet()
            value.payslip_id.action_payslip_done()
        self.write({'state': 'done'})

    def action_draft(self):
        self.write({'state': 'attendance_sheet'})

    def action_open_attpay(self):
        self.ensure_one()
        attendance_sheet_ids = self.env['attendance.sheet'].search([('batattempid', '=', self.id)]).ids
        return {
            "type": "ir.actions.act_window",
            "res_model": "attendance.sheet",
            "view_mode": 'tree,form',
            "domain": [('id', 'in', attendance_sheet_ids)],
            "name": "Attendance Sheets",
        }
