from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    related_invoice = fields.Many2one(comodel_name='account.move', compute='get_related_invoice')

    def get_related_invoice(self):
        for item in self:
            invoice = self.env['account.move'].search([('name', '=', item.communication)])
            item.related_invoice = invoice.id
