# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    warranty_instruction = fields.Html(string='Warranty Instruction', related='product_variant_ids.warranty_instruction', readonly=False)

    def action_warranty_instruction(self):
        self.ensure_one()
        return self.env.ref('product_warranty_instruction.warranty_instruction_report').report_action(self)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_warranty_instruction(self):
        self.ensure_one()
        return self.env.ref('product_warranty_instruction.warranty_instruction_report').report_action(self.product_tmpl_id)

    warranty_instruction = fields.Html('Warranty Instruction')