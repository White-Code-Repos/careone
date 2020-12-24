# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning ,ValidationError

class PromotionProgramInherit(models.Model):
    _inherit = 'sale.coupon.program'

    def action_view_sales_orders(self):
        self.ensure_one()
        orders = self.env['sale.order.line'].search([('product_id', '=', self.discount_line_product_id.id)]).mapped('order_id')
        return {
            'name': _('Sales Orders'),
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', orders.ids)],
            'context': dict(self._context, create=False)
        }

    rule_date_from = fields.Date(string="Start Date", help="Coupon program start date")
    rule_date_to = fields.Date(string="End Date", help="Coupon program end date")
    start_hour_use_promotion = fields.Float(string="From", required=False, )
    end_hour_use_promotion = fields.Float(string="To", required=False, )
    is_str_promotion = fields.Boolean(string="Saturday", )
    is_sun_promotion = fields.Boolean(string="Sunday", )
    is_mon_promotion = fields.Boolean(string="Monday", )
    is_tus_promotion = fields.Boolean(string="Tuesday", )
    is_wen_promotion = fields.Boolean(string="Wednesday", )
    is_thur_promotion = fields.Boolean(string="Thursday", )
    is_fri_promotion = fields.Boolean(string="Friday", )
    coupon_program_id = fields.Many2one(comodel_name="sale.coupon.program", string="", required=False, domain=[('program_type', '!=', 'promotion_program')])
    def _check_promo_code(self, order, coupon_code):
        message = {}
        applicable_programs = order._get_applicable_programs()
        today = datetime.today() + timedelta(hours=2)
        real_time = datetime.now() + timedelta(hours=2)
        current_time = real_time.time()
        today_week_day = today.strftime("%A")
        is_applicable_programs_today = False
        for this in self:
            if today_week_day == 'Saturday' and this.is_str_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Sunday' and this.is_sun_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Monday' and this.is_mon_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Tuesday' and this.is_tus_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Wednesday' and this.is_wen_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Thursday' and this.is_thur_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Friday' and this.is_fri_promotion == True:
                is_applicable_programs_today = True
            if is_applicable_programs_today == False:
                raise ValidationError(_('Sorry There Is No Available Today.'))
        if self.end_hour_use_promotion < (
                current_time.hour + current_time.minute / 60) or self.start_hour_use_promotion > (
                current_time.hour + current_time.minute / 60) or self.rule_date_from > today.date() or self.rule_date_to < today.date() or is_applicable_programs_today != True:
            message = {'error': _("The Promo Code isn't Available Now !")}
        elif self.maximum_use_number != 0 and self.order_count >= self.maximum_use_number:
            message = {'error': _('Promo code %s has been expired.') % (coupon_code)}
        elif not self._filter_on_mimimum_amount(order):
            message = {'error': _('A minimum of %s %s should be purchased to get the reward') % (
                self.rule_minimum_amount, self.currency_id.name)}
        elif self.promo_code and self.promo_code == order.promo_code:
            message = {'error': _('The promo code is already applied on this order')}
        elif not self.promo_code and self in order.no_code_promo_program_ids:
            message = {'error': _('The promotional offer is already applied on this order')}
        elif not self.active:
            message = {'error': _('Promo code is invalid')}
        elif self.rule_date_from and self.rule_date_from > order.date_order.date() or self.rule_date_to and order.date_order.date() > self.rule_date_to:
            message = {'error': _('Promo code is expired')}
        elif order.promo_code and self.promo_code_usage == 'code_needed':
            message = {'error': _('Promotionals codes are not cumulative.')}
        elif self._is_global_discount_program() and order._is_global_discount_already_applied():
            message = {'error': _('Global discounts are not cumulative.')}
        elif self.promo_applicability == 'on_current_order' and self.reward_type == 'product' and not order._is_reward_in_order_lines(
                self):
            message = {'error': _('The reward products should be in the sales order lines to apply the discount.')}
        elif not self._is_valid_partner(order.partner_id):
            message = {'error': _("The customer doesn't have access to this reward.")}
        elif not self._filter_programs_on_products(order):
            message = {'error': _(
                "You don't have the required product quantities on your sales order. If the reward is same product quantity, please make sure that all the products are recorded on the sales order (Example: You need to have 3 T-shirts on your sales order if the promotion is 'Buy 2, Get 1 Free'.")}
        else:
            if self not in applicable_programs and self.promo_applicability == 'on_current_order':
                message = {'error': _('At least one of the required conditions is not met to get the reward!')}
        return message

    @api.model
    def _filter_on_validity_dates(self, order):
        return self.filtered(lambda program:
                             program.rule_date_from and program.rule_date_to and
                             program.rule_date_from <= order.date_order.date() and program.rule_date_to >= order.date_order.date() or
                             not program.rule_date_from or not program.rule_date_to)


class SalesOrderInherit(models.Model):
    _inherit = 'sale.order'

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
            coupon.write({'state': 'reserved'})
            self.generated_coupon_ids |= coupon
            return coupon
        else:
            program_x = program.coupon_program_id
            vals = {'program_id': program_x.id, 'order_id': self.id, 'sale_order_id': self.id, 'customer_source_id': self.partner_id.id,
                    'is_free_order': program_x.is_free_order,
                    'start_date_use': program_x.start_date_use, 'end_date_use': program_x.end_date_use,
                    'start_hour_use': program_x.start_hour_use, 'end_hour_use': program_x.end_hour_use,
                    'is_str':program_x.is_str,'is_sun':program_x.is_sun,'is_mon':program_x.is_mon,
                    'is_tus':program_x.is_tus,'is_wen':program_x.is_wen,'is_thur':program_x.is_thur,
                    'is_fri':program_x.is_fri,}
            if program_x.generation_type == 'nbr_coupon' and program_x.nbr_coupons > 0:
                for count in range(0, program_x.nbr_coupons):
                    self.env['sale.coupon'].create(vals)

            elif program_x.generation_type == 'nbr_customer':
                vals.update({'partner_id': self.partner_id.id})
                for count in range(0, program_x.nbr_coupons):
                    coupon = self.env['sale.coupon'].create(vals)
                    subject = '%s, a coupon has been generated for you' % (self.partner_id.name)
                    template = self.env.ref('sale_coupon.mail_template_sale_coupon', raise_if_not_found=False)
                    if template:
                        template.send_mail(coupon.id,
                                           email_values={'email_to': self.partner_id.email,
                                                         'email_from': self.env.user.email or '',
                                                         'subject': subject, })
            elif program_x.generation_type == 'nbr_vehicles':
                vals.update({'vehicle_id': self.vehicle_id.id})
                for count in range(0, program_x.nbr_coupons):
                    self.env['sale.coupon'].create(vals)
            else:
                coupon = self.env['sale.coupon'].create({
                    'program_id': program.id,
                    'state': 'reserved',
                    'partner_id': self.partner_id.id,
                    'start_hour_use': program.coupon_program_id.start_hour_use,
                    'end_hour_use': program.coupon_program_id.end_hour_use,
                    'start_date_use': program.coupon_program_id.start_date_use,
                    'end_date_use': program.coupon_program_id.end_date_use,
                    'discount_line_product_id': program.discount_line_product_id.id,
                    'order_id': self.id,
                    'sale_order_id': self.id
                })
            self.is_generate_coupon = True
    def _create_new_no_code_promo_reward_lines(self):
        '''Apply new programs that are applicable'''
        self.ensure_one()
        order = self
        programs = order._get_applicable_no_code_promo_program()


        programs = programs._keep_only_most_interesting_auto_applied_global_discount_program()



        for program in programs:
            if not program:
                raise ValidationError(_('Sorry There Is No Available Programms.'))
            today = datetime.today() + timedelta(hours=2)
            real_time = datetime.now() + timedelta(hours=2)
            current_time = real_time.time()
            today_week_day = today.strftime("%A")
            is_applicable_programs_today=False
            for pro in program:
                if today_week_day == 'Saturday' and pro.is_str_promotion == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Sunday' and pro.is_sun_promotion == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Monday' and pro.is_mon_promotion == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Tuesday' and pro.is_tus_promotion == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Wednesday' and pro.is_wen_promotion == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Thursday' and pro.is_thur_promotion == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Friday' and pro.is_fri_promotion == True:
                    is_applicable_programs_today = True
                if is_applicable_programs_today == False:
                    raise ValidationError(_('Sorry There Is No Available Today.'))
            # VFE REF in master _get_applicable_no_code_programs already filters programs
            # why do we need to reapply this bunch of checks in _check_promo_code ????
            # We should only apply a little part of the checks in _check_promo_code...
            error_status = program._check_promo_code(order, False)
            if not error_status.get('error'):
                if program.promo_applicability == 'on_next_order':
                    order._create_reward_coupon(program)
                elif program.discount_line_product_id.id not in self.order_line.mapped('product_id').ids:
                    self.write({'order_line': [(0, False, value) for value in self._get_reward_line_values(program)]})
                order.no_code_promo_program_ids |= program

    def _get_applicable_no_code_promo_program(self):
        self.ensure_one()
        programs = self.env['sale.coupon.program'].with_context(
            no_outdated_coupons=True,
            applicable_coupon=True,
        ).search([
            ('promo_code_usage', '=', 'no_code_needed'),
            '|', ('rule_date_from', '=', False), ('rule_date_from', '<=', self.date_order),
            '|', ('rule_date_to', '=', False), ('rule_date_to', '>=', self.date_order),
            '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False),
        ])
        today = datetime.today() + timedelta(hours=2)
        today_week_day = today.strftime("%A")
        is_applicable_programs_today=False
        for pros in programs:
            if today_week_day == 'Saturday' and pros.is_str_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Sunday' and pros.is_sun_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Monday' and pros.is_mon_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Tuesday' and pros.is_tus_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Wednesday' and pros.is_wen_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Thursday' and pros.is_thur_promotion == True:
                is_applicable_programs_today = True
            elif today_week_day == 'Friday' and pros.is_fri_promotion == True:
                is_applicable_programs_today = True
            if is_applicable_programs_today == False:
                raise ValidationError(_('Sorry There Is No Available Today.'))
        return programs
