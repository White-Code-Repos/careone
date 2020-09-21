from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval


class CouponProgramInherit(models.Model):
    _inherit = 'sale.coupon.program'
    generation_type = fields.Selection([
        ('nbr_coupon', 'Number of Coupons'),
        ('nbr_customer', 'Number of Selected Customers'),
        ('nbr_vehicles', 'Number of selected vehicles')
    ], default='nbr_coupon')
    nbr_coupons = fields.Integer(string="Number of Coupons", help="Number of coupons", default=1)
    partners_domain = fields.Char(string="Customer", default='[]')
    vehicles_domain = fields.Char(string="Vehicle", default='[]')

    def generate_coupon(self):
        program = self
        vals = {'program_id': program.id}

        if self.generation_type == 'nbr_coupon' and self.nbr_coupons > 0:
            for count in range(0, self.nbr_coupons):
                self.env['sale.coupon'].create(vals)

        if self.generation_type == 'nbr_customer' and self.partners_domain:
            for count in range(0, self.nbr_coupons):
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
            for count in range(0, self.nbr_coupons):
                for vehicle in self.env['partner.vehicle'].search(safe_eval(self.vehicles_domain)):
                    vals.update({'vehicle_id': vehicle.id})
                    self.env['sale.coupon'].create(vals)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    coupon_id = fields.Many2one(comodel_name="sale.coupon.program", string="Coupon Program", required=False,
                                domain="[('program_type','=', 'coupon_program')]")
    is_generate_coupon = fields.Boolean(string="",  )
    def generate_coupon(self):
        program = self.coupon_id
        vals = {'program_id': program.id}
        if self.coupon_id.generation_type == 'nbr_coupon' and self.coupon_id.nbr_coupons > 0:
            for count in range(0, self.coupon_id.nbr_coupons):
                self.env['sale.coupon'].create(vals)

        if self.coupon_id.generation_type == 'nbr_customer':
            vals.update({'partner_id': self.partner_id.id})
            for count in range(0, self.coupon_id.nbr_coupons):
                coupon = self.env['sale.coupon'].create(vals)
                subject = '%s, a coupon has been generated for you' % (self.partner_id.name)
                template = self.env.ref('sale_coupon.mail_template_sale_coupon', raise_if_not_found=False)
                if template:
                    template.send_mail(coupon.id,
                                       email_values={'email_to': self.partner_id.email,
                                                     'email_from': self.env.user.email or '',
                                                     'subject': subject, })
        if self.coupon_id.generation_type == 'nbr_vehicles':
            vals.update({'vehicle_id': self.vehicle_id.id})
            for count in range(0, self.coupon_id.nbr_coupons):
                self.env['sale.coupon'].create(vals)
        self.is_generate_coupon=True

