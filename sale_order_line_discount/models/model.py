# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    fixed_discount = fields.Float(string="Fixed Discount")

    @api.depends('fixed_discount')
    def action_calculate_discount(self):
        self.discount = (self.fixed_discount / self.price_unit) * 100

    @api.depends('discount')
    def action_calculate_fixed_discount(self):
        self.fixed_discount = (self.discount / 100) * self.price_unit