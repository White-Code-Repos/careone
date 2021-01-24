# -*- coding: utf-8 -*-
from odoo import models, _, fields
from odoo.tools import safe_eval
from datetime import datetime , date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class SaleCoupon(models.Model):
    _inherit = 'sale.coupon'

    from_subscription = fields.Boolean()
    expiration_date_2 = fields.Date('Expiration Date')

    sub_id = fields.Many2one('sale.subscription')


    # def _compute_expiration_date(self):
    #     for this in self:
    #         this.expiration_date = 0
    #         for coupon in this.filtered(lambda x: x.program_id.validity_duration > 0):
    #             coupon.expiration_date = coupon.expiration_date_2

    def _compute_expiration_date(self):
        for this in self:
            this.expiration_date = this.expiration_date_2
            for coupon in this.filtered(lambda x: x.program_id.validity_duration > 0):
                coupon.expiration_date = coupon.expiration_date_2
            for coupon in this.filtered(lambda y: y.program_id.validity_duration == 0):
                if not coupon.create_date < date.now():
                    coupon.expiration_date = 0

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
        program = self
        vals = {'program_id': program.id,'expiration_date_2': datetime.now().date()+timedelta(days=program.validity_duration)}

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
