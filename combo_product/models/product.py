
from odoo import api, fields, models

class ComboProduct(models.Model):
    _name = "product.combo"
    _description = "Product packs"

    @api.onchange('product_id')
    def product_id_onchange(self):
        return {'domain': {'product_id': [('is_combo', '=', False)]}}

    name = fields.Char('name')
    product_template_id = fields.Many2one('product.template', 'Item')
    product_quantity = fields.Float('Quantity', default='1', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id')
    price = fields.Float('Product_price')

class ComboProductTemplate(models.Model):
    _inherit = "product.template"

    is_combo = fields.Boolean('Combo Product', default=False)
    combo_product_id = fields.One2many('product.combo', 'product_template_id', 'Combo Item')
