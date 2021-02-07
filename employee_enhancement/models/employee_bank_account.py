# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrEmployee(models.AbstractModel):
    _inherit = "hr.employee.base"

    check_multiple_bank_account = fields.Boolean('Multiple Bank Account')
    banks_account_ids = fields.One2many(comodel_name='res.partner.bank', inverse_name='employee_bank_account_id')


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    amount_percentage = fields.Integer("Percentage / Amount")

    employee_bank_account_id = fields.Many2one(comodel_name='hr.employee')