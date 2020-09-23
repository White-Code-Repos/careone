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
    # hisham edition
    @api.onchange('partner_id')
    def partner_onchange(self):
        if self.partner_id:
            fleet_vehicle_id = self.env['fleet.vehicle'].search([('driver_id', '=', self.partner_id.id)],order='id desc', limit=1)
            if fleet_vehicle_id:
                self.vehicle_id = fleet_vehicle_id.id
                partner_vehicle_id = self.env['partner.vehicle'].search([('vehicle_in_partner', '=', self.partner_id.id), ('fleet_model', '=', fleet_vehicle_id.model_id.id)], order='id desc', limit=1)
                if partner_vehicle_id:
                    self.customer_vehicle_id = partner_vehicle_id.id
