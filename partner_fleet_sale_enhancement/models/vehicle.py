from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Customer(models.Model):
    _name = 'partner.vehicle'

    name = fields.Char(string='Palette No', required=True, size=7)
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
