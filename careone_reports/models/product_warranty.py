from odoo import fields, models, api, _


class ProductWarranty(models.Model):
    _inherit = 'product.warranty'

    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.user.company_id)
    vehicle_id = fields.Many2one('fleet.vehicle')
