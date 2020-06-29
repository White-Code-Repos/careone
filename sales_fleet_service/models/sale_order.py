from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    category_ids = fields.Many2many(related='vehicle_id.category_ids')
    external_coupon = fields.Char('External Coupon')

