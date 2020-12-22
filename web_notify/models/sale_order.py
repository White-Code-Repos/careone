from odoo import _, api, exceptions, fields, models



class SaleSub(models.Model):
    _inherit = 'sale.subscription'

    def name_get(self):
        res = []
        for this in self:
            res.append((this.id, '%s - %s' % (this.code,this.template_id.name)))
        return res
    def write(self, values):
        res = super(SaleSub, self).write(values)
        stop_save = False
        for line in self.subs_products_ids:
            if not line.vehicle_id:
                stop_save = True
                break
        if stop_save:
            raise exceptions.UserError(_('You should add vehicle to each line of subscription products'))
class SubProducts(models.Model):
    _inherit = 'subscription.product'

    def name_get(self):
        res = []
        for this in self:
            res.append((this.id, '%s - %s' % (this.vehicle_id.display_name,this.product_id.display_name)))
        return res

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

    vehicles_subscreptions_id = fields.Many2many('subscription.product','sale_subscription_lines_ids','sale_product','subscription_product', string="Vehicles", domain="[('partner_id','=',partner_id),('subs_id','=',subscription_id)]")

    @api.onchange('vehicles_subscreptions_id')
    def onchange_method(self):
        if self.subscription_id and len(self.vehicles_subscreptions_id.ids)>0:
            print(self.id)
            records = []
            sub = self.env['sale.subscription'].search([('id', '=', self.subscription_id.id)])
            if self.order_line:
                for record in self.order_line:
                    if record.price_unit == 0:
                        self.write({'order_line': [(2, record.id)]})
            for rec in self.vehicles_subscreptions_id:
                if not self.customer_vehicle_id:
                    self.order_line |= self.env['sale.order.line'].new({
                        'product_id': rec.product_id.id,
                        'name': self.env['sale.order.line'].get_sale_order_line_multiline_description_sale(
                            rec.product_id),
                        'product_uom_qty': 1,
                        'price_unit': 0,
                        'display_type': self.env['sale.order.line'].default_get(['display_type'])['display_type'],
                        'product_uom': rec.product_id.uom_id.id,
                    })
                elif rec.vehicle_id == self.customer_vehicle_id:
                    self.order_line |= self.env['sale.order.line'].new({
                        'product_id': rec.product_id.id,
                        'name': self.env['sale.order.line'].get_sale_order_line_multiline_description_sale(
                            rec.product_id),
                        'product_uom_qty': 1,
                        'price_unit': 0,
                        'display_type': self.env['sale.order.line'].default_get(['display_type'])['display_type'],
                        'product_uom': rec.product_id.uom_id.id,
                    })
