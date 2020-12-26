from odoo import models, fields, api


class CommissionRule(models.Model):
    _name = 'commission.rule'
    _rec_name = 'name'
    name = fields.Char(string="Commission Rule Name", required=True, )
    commission_type = fields.Selection(string="Rule Type",
                                       selection=[('product', 'Product'), ('category', 'Product Category'),
                                                  ('money', 'Money Target'), ],
                                       required=True, default='product')
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False, )
    category_id = fields.Many2one(comodel_name="product.category", string="Category", required=False, )
    product_rule_info_ids = fields.One2many(comodel_name="rule.information", inverse_name="rule_id", string="",
                                            required=False, )

    category_rule_info_ids = fields.One2many(comodel_name="rule.information", inverse_name="rule_id", string="",
                                             required=False, )
    money_rule_info_ids = fields.One2many(comodel_name="rule.information", inverse_name="rule_id", string="",
                                          required=False, )


class RuleInformation(models.Model):
    _name = 'rule.information'
    product_calculation_type = fields.Selection(string="Calculation Type",
                                                selection=[('fixed', 'Fixed'), ('perc', 'Percentage'), ],
                                                required=True, default='fixed')
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=False,
                                 related='rule_id.product_id')
    category_id = fields.Many2one(comodel_name="product.category", string="Category", required=False,
                                  related='rule_id.category_id')
    min_qty = fields.Integer(string="Min Qty", required=False, )
    max_qty = fields.Integer(string="Max Qty", required=False, )
    min_amount = fields.Integer(string="Min Amount", required=False, )
    max_amount = fields.Integer(string="Max Amount", required=False, )
    commission = fields.Float(string="Commission", required=False, )
    rule_id = fields.Many2one(comodel_name="commission.rule", string="", required=False, )
