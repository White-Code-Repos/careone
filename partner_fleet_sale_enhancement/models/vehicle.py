from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Customer(models.Model):
    _name = 'partner.vehicle'

    name = fields.Char(string='Palette No', required=True)
    customer_id = fields.Many2one(comodel_name='res.partner', string='Customer', related='vehicle_in_partner')
    size = fields.Selection(selection=[
        ('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], string='Size')
    doors = fields.Integer(string='Doors')
    color = fields.Char(string='Color')
    fleet_model = fields.Many2one(comodel_name='fleet.vehicle.model', string='Model')
    brand_id = fields.Many2one(comodel_name='fleet.vehicle.model.brand', related='fleet_model.brand_id',
                               string='Company')

    # Relation field
    vehicle_in_partner = fields.Many2one(comodel_name='res.partner', readonly=True)

    @api.constrains('palette_no')
    def _check_duplicate_palette_no(self):
        for record in self:
            palette = record.search([('palette_no', '=ilike', record.palette_no), ('id', '!=', record.id)])
            if palette:
                raise ValidationError('This Palette number is used before')

    @api.onchange('fleet_model')
    def onchange_fleet_model_size_color_doors(self):
        if self.fleet_model:
            self.size = self.fleet_model.size
            self.doors = self.fleet_model.doors
            self.color = self.fleet_model.color


class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    size = fields.Selection(selection=[
        ('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], string='Size')
    doors = fields.Integer(string='Doors')
    color = fields.Char(string='Color')


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    size = fields.Selection(selection=[
        ('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], string='Size')

    @api.onchange('model_id')
    def onchange_model_id_size_color_doors(self):
        if self.model_id:
            self.size = self.model_id.size
            self.doors = self.model_id.doors
            self.color = self.model_id.color
