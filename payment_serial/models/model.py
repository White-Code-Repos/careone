# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_online_payment = fields.Boolean(string="Is Online Payment")

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_number = fields.Integer(string="Payment Number")
    is_online_payment = fields.Boolean(string="Is Online Payment")

    @api.onchange('journal_id')
    def auto_is_online_payment(self):

        if self.journal_id:

            self.is_online_payment = self.journal_id.is_online_payment

