from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    category_ids = fields.Many2many(related='vehicle_id.category_ids')
    external_coupon = fields.Char('External Coupon')
    count_vehicle_part = fields.Char(compute='_count_vehicle_parts', type='integer', string="Vehicle Parts")
    sale_vehicle_parts_ids = fields.One2many('sale.vehicle.parts', 'order_id', string='Vehicle Parts')

    def _count_vehicle_parts(self):
        for vehicle_parts in self:
            vehicle_parts.count_vehicle_part = self.env['sale.vehicle.parts'].search_count([('order_id', '=', self.id)])


class SaleVehicleParts(models.Model):
    _name = 'sale.vehicle.parts'
    _description = 'Vehicle Parts'
    _rec_name = 'order_id'

    order_id = fields.Many2one('sale.order', 'Sale Order')
    image = fields.Binary('Vehicle Part')
