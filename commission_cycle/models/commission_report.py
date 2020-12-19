from odoo import models, fields, api


class CommissionReport(models.Model):
    _name = 'commission.report'
    _rec_name = 'employee_id'
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False, )
    rule_id = fields.Many2one(comodel_name="commission.rule", string="Comm. Rule", required=False, )
    plan_id = fields.Many2one(comodel_name="commission.plan", string="Comm. Plan", required=False, )
    commission_type = fields.Selection(string="Rule Type",
                                       selection=[('product', 'Product'), ('category', 'Product Category'),
                                                  ('money', 'Money Target'), ],
                                       required=True, related='rule_id.commission_type')
    commission_item = fields.Char(string="Comm. Item", required=False, )
    accomplish = fields.Float(string="Acc.", required=False, )
    emp_comm = fields.Float(string="Employee Commission", required=False, )
    money_target_ids = fields.One2many(comodel_name="money.target", inverse_name="report_id", string="",
                                       required=False, )
    commission_date = fields.Date("Commission Date")
    status=fields.Boolean(string="Paid")


class MoneyTarget(models.Model):
    _name = 'money.target'
    calculation_type = fields.Selection(string="Calculation Type",
                                        selection=[('fixed', 'Fixed'), ('perc', 'Percentage'), ],
                                        required=True, default='fixed')
    min_amount = fields.Integer(string="Min Amount", required=False, )
    max_amount = fields.Integer(string="Max Amount", required=False, )
    commission = fields.Float(string="Commission", required=False, )
    # accomplish = fields.Float(string="Acc.", required=False, )
    # emp_comm = fields.Float(string="Employee Commission", required=False, )
    report_id = fields.Many2one(comodel_name="commission.report", string="", required=False, )
