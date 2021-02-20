from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        user = self.env['res.users'].search([('id','=' , self.env.uid)])
        print(user)
        if self.journal_id not in user.allowed_journal:
            raise UserError('You have not access on this journal\n')
        # return [
        #         ('type', 'in', ('bank', 'cash')), ('id', 'in', user.allowed_journal.ids)
        #     ]
    # allowed_journal = fields.Many2many('account.journal',)
    # user_id = fields.Many2one('res.users',default=lambda self: self.env.uid)
    # journal_id = fields.Many2one('account.journal',
    #                              string='Journal',
    #                              required=True, readonly=True,
    #                              states={'draft': [('readonly', False)]},
    #                              tracking=True,
    #                              domain=_compute_domain,
    #
    #                              )
    #
    # def _compute_allowed_journal(self):
    #     for rec in self:
    #         user = rec.env['res.users'].search([('id', '=', rec.env.uid)])
    #         rec.allowed_journal = user.allowed_journal.ids
    #         print('')
    #
    # allowed_journal = fields.Many2many('account.journal',
    #                                    'user_journal_rel_allow_edit',
    #                                    'user_id',
    #                                    'journal_id',
    #                                    compute='_compute_allowed_journal'
    #                                    )
    #
    #
    # journal_id = fields.Many2one('account.journal', string='Journal',
    #                              required=True, readonly=True,
    #                              states={'draft': [('readonly', False)]},
    #                              tracking=True,
    #                              # domain="[('type', 'in', ('bank', 'cash')),('id', 'in', allowed_journal), ('company_id', '=', company_id)]"
    #                              )
    #




class AttPayslipRun(models.Model):
    _name = 'hr.attendance.run'

    name = fields.Char(required=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('attendance_sheet', 'Attendance Sheet'),
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
            value.action_approve()
        self.write({'state': 'payslip'})

    def confirmpayslip(self):
        atteandance = self.env['attendance.sheet'].search([('batattempid', '=', self.id)])
        for value in atteandance:
            value.payslip_id.compute_sheet()
            value.payslip_id.action_payslip_done()
        self.write({'state': 'done'})

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
