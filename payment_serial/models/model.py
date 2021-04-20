# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_online_payment = fields.Boolean(string="Is Online Payment")

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_number = fields.Char(string="Payment Number")
    is_online_payment = fields.Boolean(string="Is Online Payment")

    @api.onchange('journal_id')
    def auto_is_online_payment(self):

        if self.journal_id:

            self.is_online_payment = self.journal_id.is_online_payment



    @api.onchange('amount')
    def on_change_amount(self):
        allowed = self.env['res.user'].search([('id', '=', self.env.user_id)]).allowed_journals.ids

        journal_id_domain = [
            ('id', 'in', allowed)
        ]
        result = {
            'domain': {
                'journal_id': journal_id_domain,
            },
        }
        return result
    # journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True, domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]")
