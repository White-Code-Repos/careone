from odoo import models, fields


class SaleCouponProgram(models.Model):
    _inherit = 'sale.coupon.program'

    number_of_days = fields.Integer(string="Before Expire Reminder")
    notification_type = fields.Selection([('email', 'Email'), ('whatsapp', 'Whatsapp'), ('sms', 'SMS Text Message')],
                                         string='Reminder Type',
                                         default='email')

    def coupon_expiry_reminder(self):
        today_date = fields.Date.today()
        coupon_expiration_template = self.env.ref('coupon_expire_reminder.email_template_coupon_expire')
        coupon_sms_expiration_template = self.env.ref('coupon_expire_reminder.sms_template_data_coupon_expire_reminder')
        coupon_program_rec = self.env['sale.coupon.program'].search([])
        for coupon_program in coupon_program_rec:
            for coupon in coupon_program.coupon_ids:
                if coupon.partner_id and coupon.expiration_date:
                    days_before_expiration = (coupon.expiration_date - today_date).days
                    if days_before_expiration == coupon_program.number_of_days:
                        if coupon_program.notification_type == 'email':
                            email_values = {
                                'email_to': '%s,' % (coupon.partner_id.email),
                            }
                            coupon_expiration_template.send_mail(coupon.id, force_send=True, email_values=email_values)
                        elif coupon_program.notification_type == 'sms':
                            sms_composer = self.env['sms.sms'].create({'partner_id':coupon.partner_id.id,
                                                                       'number':coupon.partner_id.mobile,
                                                                       'body':"Dear " + coupon.partner_id.name +", Your Coupon Code "+ coupon.code + " is Going to Expire on " + str(coupon.expiration_date) + ". Please Redeem it Before the Expiry Date"})
                            sms_composer.send()
                        else:
                            whatsapp_composer = self.env['send.whatsapp.partner'].create({'partner_id': coupon.partner_id.id,
                                                                                          'mobile': coupon.partner_id.mobile,
                                                                                          'message': "Dear " + coupon.partner_id.name + ", Your Coupon Code " + coupon.code + " is Going to Expire on " + str(
                                                                                             coupon.expiration_date) + ". Please Redeem it Before the Expiry Date"})
                            whatsapp_composer.send_whatsapp()