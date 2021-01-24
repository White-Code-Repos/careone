# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    fixed_discount = fields.Float(string="Fixed Discount")

    @api.onchange('fixed_discount' , 'discount')
    def action_calculate_discount(self):
        if self.fixed_discount or self.discount:
            self.fixed_discount = (self.discount / 100) * self.price_unit
            self.discount = (self.fixed_discount / self.price_unit) * 100
        else:
            self.fixed_discount = 0
            self.discount = 0