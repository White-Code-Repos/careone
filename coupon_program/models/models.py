from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta, datetime


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
                                           email_values={'email_to': partner.email,
                                                         'email_from': self.env.user.email or '',
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
    is_generate_coupon = fields.Boolean(string="", )
    coupon_count = fields.Integer(string="", required=False, compute='get_coupons_count')
    size = fields.Selection(selection=[
        ('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], string='Size',related='vehicle_id.size' )
    def write(self, vals):
        """Update the Vehicle Driver when existing Customer are updated."""
        super(SaleOrder, self).write(vals)
        if self.partner_id != self.vehicle_id.driver_id:
            self.vehicle_id.driver_id=self.partner_id
        return True
    def get_coupons_count(self):
        for quotation in self:
            quotation.coupon_count = len(self.env['sale.coupon'].search([('sale_order_id', '=', quotation.id)]))
            print(quotation.coupon_count)

    def action_view_coupons(self):
        return {
            'name': 'Coupons',
            'view_mode': 'tree',
            'res_model': 'sale.coupon',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'domain': [('sale_order_id', '=', self.id)]}

    def generate_coupon(self):
        program = self.coupon_id
        vals = {'program_id': program.id,
                'sale_order_id': self.id
                }
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
        self.is_generate_coupon = True


class CouponInherit(models.Model):
    _inherit = 'sale.coupon'

    sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale Order Ref", required=False, )


class Partner_inherit(models.Model):
    _inherit = 'res.partner'
    coupons_ids = fields.One2many(comodel_name="sale.coupon", inverse_name="partner_id", string="", required=False,
                                  compute='get_coupons_lines')

    def apply_coupon_action(self):
        return {
            'name': 'Coupon Apply',
            'view_mode': 'form',
            'res_model': 'coupon.apply',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {
                'default_partner_id': self.id,
            }}

    def get_coupons_lines(self):
        for rec in self:
            coupons = self.env["sale.coupon"].search(
                ['|', ('partner_id', '=', False),
                 ('partner_id', '=', rec.id),
                 ('state', '=', 'new'),
                 ('program_id', '!=', False),
                 ])

            rec.coupons_ids = coupons
