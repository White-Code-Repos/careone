# -*- coding: utf-8 -*-
from odoo import models, _, fields
from odoo.tools import safe_eval


class SaleCouponReward(models.Model):
    _inherit = 'sale.coupon.reward'
    _description = "Sales Coupon Reward"

    reward_type = fields.Selection(selection_add=[('product_discount', 'Product Discount')])

    def name_get(self):
        result = []
        reward_names = super(SaleCouponReward, self).name_get()
        free_shipping_reward_ids = self.filtered(lambda reward: reward.reward_type == 'product_discount').ids
        for res in reward_names:
            result.append((res[0], res[0] in free_shipping_reward_ids and _("product discount") or res[1]))
        return result


class SaleCoupon(models.Model):
    _inherit = 'sale.coupon'

    vehicle_id = fields.Many2one(comodel_name='partner.vehicle', string='For Vehicle')


class SaleCouponProgram(models.Model):
    _inherit = 'sale.coupon.program'

    sale_price = fields.Float(string='Sale Price')
    purchase_start_date = fields.Date(string='Purchase Start Date')
    purchase_end_date = fields.Date(string='Purchase End Date')


class SaleCouponGenerate(models.TransientModel):
    _inherit = 'sale.coupon.generate'

    generation_type = fields.Selection(selection_add=[('nbr_vehicles', 'Number of selected vehicles')])
    vehicles_domain = fields.Char(string="Customer", default='[]')

    def generate_coupon(self):
        program = self.env['sale.coupon.program'].browse(self.env.context.get('active_id'))

        vals = {'program_id': program.id}

        if self.generation_type == 'nbr_coupon' and self.nbr_coupons > 0:
            for count in range(0, self.nbr_coupons):
                self.env['sale.coupon'].create(vals)

        if self.generation_type == 'nbr_customer' and self.partners_domain:
            for partner in self.env['res.partner'].search(safe_eval(self.partners_domain)):
                vals.update({'partner_id': partner.id})
                coupon = self.env['sale.coupon'].create(vals)
                subject = '%s, a coupon has been generated for you' % (partner.name)
                template = self.env.ref('sale_coupon.mail_template_sale_coupon', raise_if_not_found=False)
                if template:
                    template.send_mail(coupon.id,
                                       email_values={'email_to': partner.email, 'email_from': self.env.user.email or '',
                                                     'subject': subject, })

        if self.generation_type == 'nbr_vehicles' and self.vehicles_domain:
            for vehicle in self.env['partner.vehicle'].search(safe_eval(self.vehicles_domain)):
                vals.update({'vehicle_id': vehicle.id})
                self.env['sale.coupon'].create(vals)
