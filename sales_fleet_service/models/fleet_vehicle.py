from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'


    category_ids = fields.Many2many('product.category', string='Categories')
