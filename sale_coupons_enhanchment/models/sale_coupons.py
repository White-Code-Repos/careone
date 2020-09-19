# -*- coding: utf-8 -*-
from odoo import models, _, fields
from odoo.tools import safe_eval
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
    from_subscription = fields.Boolean()
    expiration_date_2 = fields.Date('Expiration Date')
    
    sub_id = fields.Many2one('sale.subscription')


    def _check_coupon_code(self, order):
        if self.vehicle_id and self.vehicle_id.name != order.vehicle_id.license_plate:
            return  {'error': _('Invalid Vehicle.')}

        return super(SaleCoupon, self)._check_coupon_code(order)


    def _compute_expiration_date(self):
        self.expiration_date = 0

        for coupon in self.filtered(lambda x: x.program_id.validity_duration > 0):
            if not coupon.from_subscription or not coupon.expiration_date_2  : 
                coupon.expiration_date = (coupon.create_date + relativedelta(days=coupon.program_id.validity_duration)).date()
                coupon.expiration_date_2 = (coupon.create_date + relativedelta(days=coupon.program_id.validity_duration)).date()
            else:
                coupon.expiration_date = coupon.expiration_date_2


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

        if self._context.get('active_model') == 'sale.subscription' :
            subscription = self.env['sale.subscription'].browse(self.env.context.get('active_id'))
            program = subscription.coupon_program

            vals = {'program_id': program.id ,'from_subscription' : True ,'sub_id': subscription.id}


            # Change date for expiration date

            coupon2 = self.env['sale.coupon'].search([('program_id','=',program.id),('from_subscription','=',True),('sub_id','=',subscription.id)])

            if coupon2 : 
                program2 = coupon2[0]

                for obj in coupon2:
                    if obj.id > program2.id:
                        program2 = obj

                if program2 and program2.expiration_date_2 :
                    vals = {'program_id': program.id ,'from_subscription' : True ,'sub_id': subscription.id ,  'expiration_date_2' : datetime.strptime(str(program2.expiration_date_2), '%Y-%m-%d')+relativedelta(days =+ 1)}
        
        if self.generation_type == 'nbr_coupon' and self.nbr_coupons > 0:
            for count in range(0, self.nbr_coupons):
                coupon = self.env['sale.coupon'].create(vals)
                date = coupon.expiration_date_2 if coupon.expiration_date_2 else coupon.expiration_date
                vals = {'program_id': program.id ,'from_subscription' : True ,'sub_id': subscription.id ,  'expiration_date_2' : datetime.strptime(str(date), '%Y-%m-%d')+relativedelta(days =+ 1)}



        if self.generation_type == 'nbr_customer' and self.partners_domain:
            date = None
            for partner in self.env['res.partner'].search(safe_eval(self.partners_domain)):
                vals.update({'partner_id': partner.id})
                if date :
                    vals['expiration_date_2'] = datetime.strptime(str(date), '%Y-%m-%d')+relativedelta(days =+ 1)
                coupon = self.env['sale.coupon'].create(vals)
                date = coupon.expiration_date_2
                subject = '%s, a coupon has been generated for you' % (partner.name)
                template = self.env.ref('sale_coupon.mail_template_sale_coupon', raise_if_not_found=False)
                if template:
                    template.send_mail(coupon.id,
                                       email_values={'email_to': partner.email, 'email_from': self.env.user.email or '',
                                                     'subject': subject, })

        if self.generation_type == 'nbr_vehicles' and self.vehicles_domain:
            date = None
            for vehicle in self.env['partner.vehicle'].search(safe_eval(self.vehicles_domain)):
                vals.update({'vehicle_id': vehicle.id})
                if date :
                    vals['expiration_date_2'] = datetime.strptime(str(date), '%Y-%m-%d')+relativedelta(days =+ 1)
                coupon = self.env['sale.coupon'].create(vals)
                date = coupon.expiration_date_2