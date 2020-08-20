# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleCouponApplyCode(models.TransientModel):
    _inherit = 'sale.coupon.apply.code'

    coupon_code = fields.Many2one('sale.coupon', string="Code", required=True)

    @api.onchange('coupon_code')
    def coupon_code_onchange(self):
        sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
        return {'domain': {'coupon_code': [('partner_id', '=', sales_order.partner_id.id), ('state', '=', 'new')]}}

    def process_coupon(self):
        """
        Apply the entered coupon code if valid, raise an UserError otherwise.
        """
        sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
        error_status = self.apply_coupon(sales_order, self.coupon_code.code)
        if error_status.get('error', False):
            raise UserError(error_status.get('error', False))
        if error_status.get('not_found', False):
            raise UserError(error_status.get('not_found', False))
