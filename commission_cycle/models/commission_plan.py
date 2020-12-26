from odoo import models, fields, api
from odoo.exceptions import ValidationError


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

    

    @api.constrains('employee_ids', 'sales_team_ids', 'job_position_ids', 'department_ids')
    def prevent_duplication(self):
        objects = self.env['commission.plan'].search([('id', '!=', self.id)])
        for plan in objects:
            if plan.end_date >= self.start_date >= plan.start_date or plan.end_date <= self.end_date <= plan.start_date:
                if self.rule_ids and plan.rule_ids:
                    for record in self.rule_ids:
                        if record.id in plan.rule_ids.ids:
                            if self.employee_ids and plan.employee_ids:
                                for rec in self.employee_ids:
                                    if rec.id in plan.employee_ids.ids:
                                        raise ValidationError(
                                            "You have another plan in the same period that have the rule : %s and also with the same employee : %s" % (
                                                record.name, rec.name))

                            if self.sales_team_ids and plan.sales_team_ids:
                                for rec in self.sales_team_ids:
                                    if rec.id in plan.sales_team_ids.ids:
                                        raise ValidationError(
                                            "You have another plan in the same period that have that have the rule : %s and also with the same Sale Team : %s" % (
                                                record.name, rec.name))

                            if self.job_position_ids and plan.job_position_ids:
                                for rec in self.job_position_ids:
                                    if rec.id in plan.job_position_ids.ids:
                                        raise ValidationError(
                                            "You have another plan in the same period that have that have the rule : %s and also with the same Job position : %s" % (
                                                record.name, rec.name))

                            if self.department_ids and plan.department_ids:
                                for rec in self.department_ids:
                                    if rec.id in plan.department_ids.ids:
                                        raise ValidationError(
                                            "You have another plan in the same period that have that have the rule : %s and also with the same department : %s" % (
                                            record.name, rec.display_name))

    @api.constrains('rule_ids')
    def _check_duplicate_money_target_rule(self):
        x = 0
        for record in self.rule_ids:
            if record.commission_type == 'money':
                x += 1
        if x > 1:
            raise ValidationError("Your Plan Shouldn't Have More Than One Money Target Rule !")
