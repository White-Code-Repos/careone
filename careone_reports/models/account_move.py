from odoo import fields, models, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    total_discount = fields.Float(compute="compute_total_discount")

    def compute_total_discount(self):
        for item in self:
            item.total_discount = 0.0
            for line in item.invoice_line_ids:
                if line.discount:
                    item.total_discount += line.price_unit * (line.discount / 100)
