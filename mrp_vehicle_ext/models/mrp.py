from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MRP_inherit_EXT(models.Model):
    _inherit = 'mrp.workorder'

    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle", compute="_compute_vehicle")
    def _compute_vehicle(self):
        if self.production_id:
            if self.production_id.vehicle_id_sale:
                self.vehicle_id = self.production_id.vehicle_id_sale.id
        if not self.vehicle_id:
            self.vehicle_id = False
