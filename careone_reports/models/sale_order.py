from odoo import fields, models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    total_discount = fields.Float(compute="compute_total_discount")

    def compute_total_discount(self):
        for item in self:
            item.total_discount = 0.0
            for line in item.order_line:
                if line.discount:
                    item.total_discount += line.price_unit * (line.discount / 100)
