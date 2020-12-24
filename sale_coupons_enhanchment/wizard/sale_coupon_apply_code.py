# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta, datetime


class SaleCouponApplyCode(models.TransientModel):
    _inherit = 'sale.coupon.apply.code'
    code_type = fields.Selection(string="Code Type", selection=[('promo', 'Promotion'), ('coupon', 'Coupon'), ],
                                 required=True, default='coupon')
    promo_code = fields.Char(string="Promo Code", required=False, )
    coupon_code = fields.Many2one('sale.coupon', string="Coupon Code", required=False)
    is_free_order_readonly_x = fields.Boolean(string="", )

    # hisham edition
    @api.onchange('coupon_code')
    def coupon_code_onchange(self):
        if self.coupon_code:
            if self.coupon_code.is_free_order == True:
                self.is_free_order = True
                self.is_free_order_readonly_x = True
        today = datetime.today().date()
        today_x = datetime.today() + timedelta(hours=2)
        real_time = datetime.now() + timedelta(hours=2)
        current_time = real_time.time()
        sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
        return {'domain': {
            'coupon_code': [('start_date_use', '<=', today_x.date()),
                            ('end_date_use', '>=', today_x.date()),
                            ('start_hour_use', '<=', (current_time.hour + current_time.minute / 60)),
                            ('end_hour_use', '>=', (current_time.hour + current_time.minute / 60)),
                            ('expiration_date', '>', today.strftime("%Y-%m-%d")),
                            # ('program_id', '=', sales_order.coupon_id.id),
                            ('state', '=', 'new'), '|', ('partner_id', '=', sales_order.partner_id.id),
                            ('partner_id', '=', False),
                            '|', ('vehicle_id', '=', sales_order.customer_vehicle_id.id),
                            ('vehicle_id', '=', False)]}}

    # hisham edition
    is_free_order = fields.Boolean(string="Free Order", store=True)

    def process_coupon(self):
        """
        Apply the entered coupon code if valid, raise an UserError otherwise.

        """
        if self.code_type == 'coupon':
            coupon = self.env['sale.coupon'].browse(self.coupon_code)
            today = datetime.today() + timedelta(hours=2)
            real_time = datetime.now() + timedelta(hours=2)
            current_time = real_time.time()
            today_week_day = today.strftime("%A")
            is_applicable_programs_today=False
            if today_week_day == 'Saturday' and coupon.programe_id.is_str == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Sunday' and coupon.programe_id.is_sun == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Monday' and coupon.programe_id.is_mon == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Tuesday' and coupon.programe_id.is_tus == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Wednesday' and coupon.programe_id.is_wen == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Thursday' and coupon.programe_id.is_thur == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Friday' and coupon.programe_id.is_fri == True:
                is_applicable_programs_today = True
            if is_applicable_programs_today == False:
                raise ValidationError(_('Sorry There Is No Available Today.'))

        if self.code_type == 'promo':
            sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
            error_status = self.apply_promo(sales_order, self.promo_code)
            if error_status.get('error', False):
                raise UserError(error_status.get('error', False))
            if error_status.get('not_found', False):
                raise UserError(error_status.get('not_found', False))

        else:
            if self.is_free_order == True:
                sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
                my_domain_products = self.env['product.product'].search(
                    safe_eval(self.coupon_code.program_id.rule_products_domain))
                x = 0
                for rec in my_domain_products:
                    x = rec.id
                    break
                my_domain_product = self.env['product.product'].search([('id', '=', x)])
                my_free_product = self.coupon_code.program_id.reward_product_id
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
                    error_status = self.apply_coupon(sales_order, self.coupon_code.code)
                    self.env['sale.order.line'].search([('id', '=', base_records_ids[0])]).unlink()
                    if error_status.get('error', False):
                        raise UserError(error_status.get('error', False))
                    if error_status.get('not_found', False):
                        raise UserError(error_status.get('not_found', False))
                else:
                    raise UserError("You Can't Use Free Order With That Program !")
            else:
                sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
                error_status = self.apply_coupon(sales_order, self.coupon_code.code)
                if error_status.get('error', False):
                    raise UserError(error_status.get('error', False))
                if error_status.get('not_found', False):
                    raise UserError(error_status.get('not_found', False))

    def apply_promo(self, order, coupon_code):
        if self.code_type == 'coupon':
            # coupon = self.env['sale.coupon'].browse(coupon_code)
            today = datetime.today() + timedelta(hours=2)
            real_time = datetime.now() + timedelta(hours=2)
            current_time = real_time.time()
            today_week_day = today.strftime("%A")
            is_applicable_programs_today=False
            if today_week_day == 'Saturday' and coupon_code.is_str_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Sunday' and coupon_code.is_sun_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Monday' and coupon_code.is_mon_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Tuesday' and coupon_code.is_tus_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Wednesday' and coupon_code.is_wen_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Thursday' and coupon_code.is_thur_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Friday' and coupon_code.is_fri_promotion == True:
                is_applicable_programs_today = True
            if is_applicable_programs_today == False:
                raise ValidationError(_('Sorry There Is No Available Today.'))
        error_status = {}
        program = self.env['sale.coupon.program'].search([('promo_code', '=', coupon_code)])
        if program:
            error_status = program._check_promo_code(order, coupon_code)
            if not error_status:
                if program.promo_applicability == 'on_next_order':
                    # Avoid creating the coupon if it already exist
                    if program.discount_line_product_id.id not in order.generated_coupon_ids.filtered(
                            lambda coupon: coupon.state in ['new', 'reserved']).mapped('discount_line_product_id').ids:
                        order._create_reward_coupon(program)
                else:  # The program is applied on this order
                    order._create_reward_line(program)
                    order.code_promo_program_id = program
        else:
            error_status = {'not_found': _('The code %s is invalid') % (coupon_code)}
        return error_status
