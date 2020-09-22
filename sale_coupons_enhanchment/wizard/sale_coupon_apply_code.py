# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class SaleCouponApplyCode(models.TransientModel):
    _inherit = 'sale.coupon.apply.code'

    coupon_code = fields.Many2one('sale.coupon', string="Code", required=True)

    # hisham edition
    @api.onchange('coupon_code')
    def coupon_code_onchange(self):
        today=datetime.today().date()
        print(today.strftime("%Y-%m-%d"))
        print(self.coupon_code.expiration_date)

        sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
        return {'domain': {'coupon_code': [('expiration_date', '>', today.strftime("%Y-%m-%d")),
                                           ('program_id', '=', sales_order.coupon_id.id),
                                           ('state', '=', 'new'), '|', ('partner_id', '=', sales_order.partner_id.id),
                                           ('partner_id', '=', False),
                                           '|', ('vehicle_id', '=', sales_order.customer_vehicle_id.id),
                                           ('vehicle_id', '=', False)]}}
    # hisham edition
    is_free_order = fields.Boolean(string="Free Order",  )
    def process_coupon(self):
        """
        Apply the entered coupon code if valid, raise an UserError otherwise.

        """
        if self.is_free_order == True:
            sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
            base_records_ids=[]
            for rec in sales_order.order_line:
                base_records_ids.append(rec.id)
            error_status = self.apply_coupon(sales_order, self.coupon_code.code)
            self.env['sale.order.line'].search([('id', '=', base_records_ids[0])]).unlink()
            if error_status.get('error', False):
                raise UserError(error_status.get('error', False))
            if error_status.get('not_found', False):
                raise UserError(error_status.get('not_found', False))
        else:
            sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
            error_status = self.apply_coupon(sales_order, self.coupon_code.code)
            if error_status.get('error', False):
                raise UserError(error_status.get('error', False))
            if error_status.get('not_found', False):
                raise UserError(error_status.get('not_found', False))
