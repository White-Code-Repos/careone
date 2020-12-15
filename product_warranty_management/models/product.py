from odoo import models, fields, api, _
from odoo.exceptions import UserError
class ProductProduct(models.Model):
    _inherit = "product.product"

    warranty_product_id = fields.Many2one("product.product", string="Warranty Product",help="When Create warranty at that time this service type of product will use, If product is not created then we can not set warranty product automatically in warrany.",copy=False)
    warranty_type_id = fields.Many2one("product.warranty.type", "Warranty Type")