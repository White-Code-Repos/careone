from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

# class FleetVehicle(models.Model):
#     _inherit = 'fleet.vehicle'
#
#     def write(self, values):
#         res = super(FleetVehicle, self).write(values)
#         _logger.info(res)
#         _logger.info(self._context)
#         if res:
#             _logger.info(self._context.get('order_under_popup'))
#             if self._context.get('order_under_popup'):
#                 order_under_popup = self._context.get('order_under_popup')
#                 sale_order = self.env['sale.order'].browse(order_under_popup)
#                 _logger.info(sale_order)
#                 if sale_order:
#                     _logger.info(self.driver_id.name)
#                     _logger.info(sale_order.partner_id.name)
#                     sale_order.write({'partner_id':self.driver_id.id})
#                     _logger.info(sale_order.partner_id.name)
#
#         return res



class SaleOrder(models.Model):
    _inherit = 'sale.order'
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', )
    category_ids = fields.Many2many(related='vehicle_id.category_ids')
    external_coupon = fields.Char('External Coupon')
    count_vehicle_part = fields.Char(compute='_count_vehicle_parts', type='integer', string="Vehicle Parts")
    sale_vehicle_parts_ids = fields.One2many('sale.vehicle.parts', 'order_id', string='Vehicle Parts')

    color_id = fields.Many2one('fleet.color', string='Vehicle color')
    model_id = fields.Many2one('fleet.model', string='Model year')

    def _count_vehicle_parts(self):
        for vehicle_parts in self:
            vehicle_parts.count_vehicle_part = self.env['sale.vehicle.parts'].search_count([('order_id', '=', self.id)])

    @api.onchange('vehicle_id')
    def onchange_color_model(self):
        if self.vehicle_id:
            self.color_id = self.vehicle_id.color.id
            self.model_id = self.vehicle_id.model_year.id


class SaleVehicleParts(models.Model):
    _name = 'sale.vehicle.parts'
    _description = 'Vehicle Parts'
    _rec_name = 'order_id'

    order_id = fields.Many2one('sale.order', 'Sale Order')
    image1 = fields.Binary('Vehicle Part')
    image2 = fields.Binary()
    image3 = fields.Binary()
    image4 = fields.Binary()

    note = fields.Text()
