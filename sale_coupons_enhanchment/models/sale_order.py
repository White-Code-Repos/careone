# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # , compute = '_compute_used_coupon', store = True
    used_coupon = fields.Many2one('sale.coupon', string="Used Coupon")

    # @api.model
    # def _compute_used_coupon(self):
    #     for this in self:
    #         product = this.env['product.template'].search([('id', '=', this.product_tmpl_id)])
    #         invoice = this.env['account.move'].search([('id', '=', this.move_id)])
    #         if invoice:
    #             sale = this.env['sale.order'].search([('name', '=', invoice.invoice_origin)])
    #         else:
    #             this.used_coupon = False
    #
    #         if sale:
    #             sale_line = this.env['sale.order.line'].search([('order_id', '=', sale.id)])
    #         else:
    #             this.used_coupon = False
    #
    #         if sale_line:
    #             for line in sale_line:
    #                 if line.product_template_id.id == product.id:
    #                     this.used_coupon = line.used_coupon
    #         else:
    #             this.used_coupon = False

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

class CouponInherit(models.Model):
    _inherit = 'sale.coupon'

    def _create_reward_coupon(self, program):
        # if there is already a coupon that was set as expired, reactivate that one instead of creating a new one
        coupon = self.env['sale.coupon'].search([
            ('program_id', '=', program.id),
            ('state', '=', 'expired'),
            ('partner_id', '=', self.partner_id.id),
            ('order_id', '=', self.id),
            ('discount_line_product_id', '=', program.discount_line_product_id.id),
        ], limit=1)
        if coupon:
            raise ValidationError(program.validity_duration)
            coupon.write({'state': 'reserved'})
        else:
            raise ValidationError(program.validity_duration)
            coupon = self.env['sale.coupon'].sudo().create({
                'program_id': program.id,
                'state': 'reserved',
                'partner_id': self.partner_id.id,
                'order_id': self.id,
                'discount_line_product_id': program.discount_line_product_id.id,
                'validity_duration':program.validity_duration
            })
        self.generated_coupon_ids |= coupon
        return coupon