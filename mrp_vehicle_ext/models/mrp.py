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

class MRP_P_inherit_EXT(models.Model):
    _inherit = 'mrp.production'

    state = fields.Selection([
        ('draft', '1- Draft'),
        ('confirmed', '2- Confirmed'),
        ('planned', '3- Planned'),
        ('progress', '4- In Progress'),
        ('to_close', '5- To Close'),
        ('done', '6- Done'),
        ('cancel', '7- Cancelled')], string='State',
        compute='_compute_state', copy=False, index=True, readonly=True,
        store=True, tracking=True,
        help=" * Draft: The MO is not confirmed yet.\n"
             " * Confirmed: The MO is confirmed, the stock rules and the reordering of the components are trigerred.\n"
             " * Planned: The WO are planned.\n"
             " * In Progress: The production has started (on the MO or on the WO).\n"
             " * To Close: The production is done, the MO has to be closed.\n"
             " * Done: The MO is closed, the stock moves are posted. \n"
             " * Cancelled: The MO has been cancelled, can't be confirmed anymore.")
