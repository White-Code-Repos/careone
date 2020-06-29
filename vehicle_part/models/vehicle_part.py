from odoo import models, fields


class VehiclePart(models.Model):
    _name = 'vehicle.part'
    _description = 'Vehicle Part'

    name = fields.Char('Name', help='Vehicle Part Name')

