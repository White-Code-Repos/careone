from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    purchase_type = fields.Many2one(
        comodel_name='purchase.order.type', string='Purchase Order Type')
