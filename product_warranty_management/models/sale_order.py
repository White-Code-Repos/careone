from odoo import models, fields, api, _
from odoo.exceptions import UserError
class SaleOrder(models.Model):
    _inherit = "sale.order"

    product_warrany_ids = fields.One2many("product.warranty.management", "sale_order_id", string="Product Warranty")

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    warranty_type_id = fields.Many2one("product.warranty.type", "Warranty Type",copy=False)
    warranty_product_id = fields.Many2one("product.product", "Warranty Product")