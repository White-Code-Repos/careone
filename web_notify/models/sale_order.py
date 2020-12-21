from odoo import _, api, exceptions, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def notify_user_subscreptions(self):
        if self.partner_id:
            already_member = False
            subscription = self.env['sale.subscription'].search([('partner_id','=',self.partner_id.id)])
            if len(subscription) > 0:
                already_member = True
            if already_member:
                self.env.user.notify_success(message='Have Subscription')
