from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    vehicle_part_id = fields.Many2one('vehicle.part', string='Vehicle Part')
