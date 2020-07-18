from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_warranty = fields.Integer('Warranty Days')