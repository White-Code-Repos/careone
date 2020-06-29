from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_vehicle_id = fields.Many2one(comodel_name='partner.vehicle')

    @api.onchange('customer_vehicle_id')
    def vehicle_onchange(self):
        if self.customer_vehicle_id:
            return {'domain': {'partner_id': [('id', '=', self.customer_vehicle_id.customer_id.id)]}}
        else:
            return {'domain': {'partner_id': []}}

    @api.onchange('partner_id')
    def partner_onchange(self):
        if self.partner_id:
            return {'domain': {'customer_vehicle_id': [('customer_id', '=', self.partner_id.id)]}}
        else:
            return {'domain': {'customer_vehicle_id': []}}
