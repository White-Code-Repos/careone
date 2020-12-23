from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class CouponProgramInherit(models.Model):
    _inherit = 'sale.coupon.program'
    generation_type = fields.Selection([
        ('nbr_coupon', 'Number of Coupons'),
        ('nbr_customer', 'Number of Selected Customers'),
        ('nbr_vehicles', 'Number of selected vehicles')
    ], default='nbr_coupon')
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    nbr_coupons = fields.Integer(string="Number of Coupons", help="Number of coupons", default=1)
    partners_domain = fields.Char(string="Customer", default='[]')
    vehicles_domain = fields.Char(string="Vehicle", default='[]')
    start_hour_generate = fields.Float(string="From", required=False, )
    end_hour_generate = fields.Float(string="To", required=False, )
    start_date_generate = fields.Date(string="From", required=False, )
    end_date_generate = fields.Date(string="To", required=False, )
    start_hour_use = fields.Float(string="From", required=False, )
    end_hour_use = fields.Float(string="To", required=False, )
    start_date_use = fields.Date(string="From", required=False, )
    end_date_use = fields.Date(string="To", required=False, )
    is_free_order = fields.Boolean(string="Allow Free Order", )
    is_str = fields.Boolean(string="Saturday", )
    is_sun = fields.Boolean(string="Sunday", )
    is_mon = fields.Boolean(string="Monday", )
    is_tus = fields.Boolean(string="Tuesday", )
    is_wen = fields.Boolean(string="Wednesday", )
    is_thur = fields.Boolean(string="Thursday", )
    is_fri = fields.Boolean(string="Friday", )

    def generate_coupon(self):
        program = self
        vals = {'program_id': program.id, 'is_free_order': program.is_free_order,
                'start_date_use': program.start_date_use, 'end_date_use': program.end_date_use,
                'start_hour_use': program.start_hour_use, 'end_hour_use': program.end_hour_use}

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

    @api.model
    def coupon_program_onchange(self):
        today = datetime.today() + timedelta(hours=2)
        real_time = datetime.now() + timedelta(hours=2)
        current_time = real_time.time()
        return [('start_date_generate', '<=', today.date()),
                ('end_date_generate', '>=', today.date()),
                ('start_hour_generate', '<=', (current_time.hour + current_time.minute / 60)),
                ('end_hour_generate', '>=', (current_time.hour + current_time.minute / 60))]
# domain=coupon_program_onchange
    coupon_id = fields.Many2one(comodel_name="sale.coupon.program", string="Coupon Program", required=False,
                                )
    is_generate_coupon = fields.Boolean(string="", )
    coupon_count = fields.Integer(string="", required=False, compute='get_coupons_count')
    size = fields.Selection(selection=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], string='Size',
                            related='vehicle_id.size')
    is_allow_generate_coupon = fields.Boolean(string="")
                                              #, compute='allow_generate_coupon')

    def write(self, vals):
        """Update the Vehicle Driver when existing Customer are updated."""
        super(SaleOrder, self).write(vals)
        if self.partner_id != self.vehicle_id.driver_id:
            self.vehicle_id.driver_id = self.partner_id
        return True

    def action_cancel(self):
        for coupon in self.env['sale.coupon'].search([('sale_order_id', '=', self.id)]):
            coupon.unlink()
        super(SaleOrder, self).action_cancel()

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
        vals = {'program_id': program.id, 'sale_order_id': self.id, 'customer_source_id': self.partner_id.id,
                'is_free_order': program.is_free_order,
                'start_date_use': program.start_date_use, 'end_date_use': program.end_date_use,
                'start_hour_use': program.start_hour_use, 'end_hour_use': program.end_hour_use}
        order_products = []
        program_products = []
        is_product_ability = False
        for rec in self.order_line:
            order_products.append(rec.product_id)
        for product in self.env['product.product'].search(safe_eval(self.coupon_id.rule_products_domain)):
            program_products.append(product)
        for product in order_products:
            if product in program_products:
                is_product_ability = True
        if is_product_ability == True:
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
        else:
            raise ValidationError("Your Program Doesn't Contain your any product in that order !")

#
    def allow_generate_coupon(self):
        for order in self:
            order.is_allow_generate_coupon = False
            if order.coupon_id and order.state == 'sale':
                today = datetime.today() + timedelta(hours=2)
                real_time = datetime.now() + timedelta(hours=2)
                current_time = real_time.time()
                if order.coupon_id.start_date_generate and order.coupon_id.end_date_generate:
                    if order.coupon_id.start_date_generate <= today.date() <= order.coupon_id.end_date_generate:
                        if order.coupon_id.start_hour_generate <= (
                                current_time.hour + current_time.minute / 60) <= order.coupon_id.end_hour_generate:
                            order.is_allow_generate_coupon = True


class CouponInherit(models.Model):
    _inherit = 'sale.coupon'
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    start_hour_use = fields.Float(string="From", required=False, )
    end_hour_use = fields.Float(string="To", required=False, )
    start_date_use = fields.Date(string="From", required=False, )
    end_date_use = fields.Date(string="To", required=False, )
    is_free_order = fields.Boolean(string="Allow Free Order", )
    state = fields.Selection([
        ('reserved', 'Reserved'),
        ('new', 'Valid'),
        ('used', 'Consumed'),
        ('expired', 'Expired'),
        ('cancel', 'Canceled')
    ], required=True, default='new')
    sale_order_id = fields.Many2one(comodel_name="sale.order", string="Sale Order Ref", required=False, )
    customer_source_id = fields.Many2one(comodel_name="res.partner", string="Customer Source", required=False, )
    is_canceled = fields.Boolean(string="", )
    is_expiration_date_changed = fields.Boolean(string="Change Expiration Date", )
    expiration_date_edit = fields.Date(string="New Expiration Date", required=False, )
    is_have_permission = fields.Boolean(string="", compute='get_user_permission')

    @api.onchange('vehicle_id', 'partner_id')
    def vehicle_onchange(self):
        if self.partner_id:
            return {'domain': {'vehicle_id': [('customer_id', '=', self.partner_id.id), ]}}
        else:
            return {'domain': {'vehicle_id': []}}

    def get_user_permission(self):
        for coupon in self:
            users = []
            current_login = self.env.user
            group_security_id = self.env['res.groups'].search([('category_id.name', '=', 'Coupon Edition')],
                                                              order='id desc',
                                                              limit=1)

            for user in group_security_id.users:
                users.append(user)
            if current_login in users:
                coupon.is_have_permission = True
            else:
                coupon.is_have_permission = False

    def _compute_expiration_date(self):
        self.expiration_date = 0
        for coupon in self:
            if coupon.expiration_date_edit:
                coupon.expiration_date = coupon.expiration_date_edit
            elif coupon.end_date_use:
                coupon.expiration_date = coupon.end_date_use
            else:
                coupon.expiration_date = (
                        coupon.create_date + relativedelta(days=coupon.program_id.validity_duration)).date()

    def edit_date(self):
        return {
            'name': 'Expiration Date Edition',
            'view_mode': 'form',
            'res_model': 'date.edit',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {
                'default_coupon_id': self.id,
            }}

    def vehicle_state_default_get(self):
        if self.program_id.validity_duration > 0:
            return (self.create_date + relativedelta(days=self.program_id.validity_duration)).date()
        else:
            return 0

    def cancel_coupon(self):
        self.is_canceled = True
        self.state = 'cancel'


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
                 ('program_id', '!=', False), ('customer_source_id', '=', rec.id),
                 # ('customer_source_id', '=', False)
                 ])

            rec.coupons_ids = coupons


class fleet_vehicle_inherit(models.Model):
    _inherit = 'fleet.vehicle'
    sale_order_count = fields.Integer(string="", compute='get_sales_count', required=False, )

    def get_sales_count(self):
        for vehicle in self:
            sale_ids = self.env['sale.order'].search([('vehicle_id', '=', vehicle.id)])
            vehicle.sale_order_count = len(sale_ids)

    def action_view_sales(self):
        return {
            'name': 'Sales Order',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'domain': [('vehicle_id', '=', self.id)]}
