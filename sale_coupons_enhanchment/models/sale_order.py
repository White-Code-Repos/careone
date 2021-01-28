# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = "account.move"

    used_coupon = fields.Many2one('sale.coupon', string="Used Coupon", compute='_compute_used_coupon')

    # @api.model
    def _compute_used_coupon(self):
        for this in self:
            sale_order = this.env['sale.order'].search([('name', '=', this.invoice_origin)])
            if sale_order and sale_order.used_coupon:
                this.used_coupon = sale_order.used_coupon.id
            else:
                this.used_coupon = False

class SaleOrder(models.Model):
    _inherit = "sale.order"

    used_coupon = fields.Many2one('sale.coupon', string="Used Coupon")

    def _get_reward_line_values(self, program):
        self.ensure_one()
        self = self.with_context(lang=self.partner_id.lang)
        program = program.with_context(lang=self.partner_id.lang)
        if program.reward_type == 'discount':
            return self._get_reward_values_discount(program)
        elif program.reward_type == 'product':
            return [self._get_reward_values_product(program)]
        # elif program.reward_type == 'product_discount':
        #     if program.reward_product_id:
        #         product = self.order_line.filtered(lambda line: program.reward_product_id == line.product_id)
        #         if product :
        #             return [self._get_reward_values_product(program)]
        #     if program.discount_percentage:
        #         return self._get_reward_values_discount(program)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            # if price > 0 else price
