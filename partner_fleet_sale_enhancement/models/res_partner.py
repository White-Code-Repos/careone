from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Customer(models.Model):
    _inherit = 'res.partner'

    vehicle_ids = fields.One2many(comodel_name='partner.vehicle',
                                  inverse_name='vehicle_in_partner',
                                  string='Vehicles')

    @api.constrains('mobile')
    def _check_duplicate_mobile(self):
        for record in self:
            customers = record.search([('mobile', '=ilike', record.mobile), ('id', '!=', record.id)])
            if customers:
                raise ValidationError('This mobile number is used before')
