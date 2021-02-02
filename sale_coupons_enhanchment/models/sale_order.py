# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class InvoiceUsedCoupon(models.Model):
    _name = "invoice.used.coupon"

    name = fields.Many2one('sale.coupon', string="Used Coupon")
    invoice_id = fields.Many2one('account.move')

class AccountMove(models.Model):
    _inherit = "account.move"

    used_coupon = fields.One2many('invoice.used.coupon', 'invoice_id', string="Used Coupon", compute='_compute_used_coupon')

    def _compute_used_coupon(self):
        for this in self:
            sale = this.env['sale.order'].search([('name', '=', this.invoice_origin)])
            lines = this.env['sale.order.line'].search([('order_id', '=', sale.id)])
            used_coupon = []
            for line in lines:
                used_coupon.append((0, 0, {
                    'name': line.used_coupon.id,
                    'invoice_id': this.id,
                }))
            raise ValidationError(used_coupon)
            if used_coupon:
                self.used_coupon = used_coupon
            else:
                self.used_coupon = False

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_reward_line_values(self, program):
        self.ensure_one()
        self = self.with_context(lang=self.partner_id.lang)
        program = program.with_context(lang=self.partner_id.lang)
        if program.reward_type == 'discount':
            return self._get_reward_values_discount(program)
        elif program.reward_type == 'product':
            return [self._get_reward_values_product(program)]

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    used_coupon = fields.Many2one('sale.coupon', string="Used Coupon")

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