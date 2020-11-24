from odoo import models, fields, api


class CommissionPlan(models.Model):
    _name = 'commission.plan'
    _rec_name = 'name'
    name = fields.Char(string="Commission Plan Name", required=True, )
    start_date = fields.Date(string="Start Date", required=True, )
    end_date = fields.Date(string="End Date", required=True, )
    is_with_employees = fields.Boolean(string="Employees", )
    is_with_sales_team = fields.Boolean(string="Sales Teams", )
    is_job_position = fields.Boolean(string="Job Positions", )
    is_with_department = fields.Boolean(string="Departments", )
    is_with_portal = fields.Boolean(string="Portal Users", )
    employee_ids = fields.Many2many(comodel_name="hr.employee", string="Employees", )
    sales_team_ids = fields.Many2many(comodel_name="crm.team", string="Sales Teams", )
    job_position_ids = fields.Many2many(comodel_name="hr.job", string="Job Positions", )
    department_ids = fields.Many2many(comodel_name="hr.department", string="Departments", )
    portal_user_ids = fields.Many2many(comodel_name="res.users", string="Portal Users", )
    condition = fields.Selection(string="Condition",
                                 selection=[('confirm sales', 'Confirm Sales Orders'), ('invoice', 'Invoicing'),
                                            ('payment', 'Payment'), ], required=True, default='confirm sales')
    rule_ids = fields.Many2many(comodel_name="commission.rule", string="Commission Rules", )
