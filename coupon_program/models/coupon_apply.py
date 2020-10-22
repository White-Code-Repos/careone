from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta


class CouponApply(models.TransientModel):
    _name = 'coupon.apply'
    partner_id = fields.Many2one(comodel_name="res.partner", string="", required=False, )
    coupon_id = fields.Many2one(comodel_name="sale.coupon", string="Coupon", required=False, )

    @api.onchange('coupon_id')
    def coupon_code_onchange(self):
        today = datetime.today() + timedelta(hours=2)
        real_time = datetime.now() + timedelta(hours=2)
        current_time = real_time.time()
        return {'domain': {'coupon_id': ['|', ('partner_id', '=', False),
                                         ('partner_id', '=', self.partner_id.id),
                                         ('customer_source_id', '=', self.partner_id.id),
                                         ('state', '=', 'new'),
                                         ('program_id', '!=', False), ('start_date_use', '<=', today.date()),
                                         ('end_date_use', '>=', today.date()),
                                         ('start_hour_use', '<=', (current_time.hour + current_time.minute / 60)),
                                         ('end_hour_use', '>=', (current_time.hour + current_time.minute / 60))
                                         ]}}

    def apply_action(self):
        fleet_vehicle_id = self.env['fleet.vehicle'].search([('driver_id', '=', self.partner_id.id)], order='id desc',
                                                            limit=1)
        sales_order = self.env['sale.order'].create({'partner_id': self.partner_id.id,
                                                     'coupon_id': self.coupon_id.program_id.id,
                                                     'vehicle_id': fleet_vehicle_id.id
                                                     })
        my_domain_products = self.env['product.product'].search(
            safe_eval(sales_order.coupon_id.rule_products_domain))
        x = 0
        for rec in my_domain_products:
            x = rec.id
            break
        my_domain_product = self.env['product.product'].search([('id', '=', x)])
        my_free_product = sales_order.coupon_id.reward_product_id
        if my_free_product:
            order_obj_id = self.env['sale.order.line']
            my_domain_product_line = {
                'product_id': my_domain_product.id,
                'order_id': sales_order.id
            }
            my_free_product_line = {
                'product_id': my_free_product.id,
                'order_id': sales_order.id
            }
            order_obj_id.create(my_domain_product_line)
            order_obj_id.create(my_free_product_line)
            base_records_ids = []
            for rec in sales_order.order_line:
                base_records_ids.append(rec.id)
            error_status = self.env['sale.coupon.apply.code'].apply_coupon(sales_order, self.coupon_id.code)
            self.env['sale.order.line'].search([('id', '=', base_records_ids[0])]).unlink()
            if error_status.get('error', False):
                raise UserError(error_status.get('error', False))
            if error_status.get('not_found', False):
                raise UserError(error_status.get('not_found', False))
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': sales_order.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
