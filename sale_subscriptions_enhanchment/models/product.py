from odoo import api, fields, models, _


class ProductInherit(models.Model):
    _inherit = 'product.product'
    no_of_vehicles = fields.Integer(string="No Of Vehicles", required=False, related='product_tmpl_id.no_of_vehicles')


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'
    no_of_vehicles = fields.Integer(string="No Of Vehicles", required=False, )
