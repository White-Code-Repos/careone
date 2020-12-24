from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, RedirectWarning

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
    commission_date = fields.Date("Last update on")
    status=fields.Boolean(string="Posted to Payroll")

    @api.onchange('status')
    def post_to_payroll(self):
        empReports = self.env['commission.report'].search([('employee_id','=',self.employee_id.id),('status','=',False)])
        comm = 0
        for reps in empReports:
            comm += reps.emp_comm
            reps.write({'status':True})
        self.env['hr.contract'].search([('employee_id','=',self.employee_id.id)]).write({'commission':comm})
        
    def action_post_payroll(self):
        comm = 0
        for reps in self:
            if reps.status == True:
                raise UserError(_('These Rows Already Posted.'))
            comm += reps.emp_comm
            reps.write({'status':True})
        self.env['hr.contract'].search([('employee_id','=',self.employee_id.id)]).write({'commission':comm})

class hrContract(models.Model):
    _inherit='hr.contract'
    commission = fields.Float('Sales Commission')

class HRPAYSLIP(models.Model):
    _inherit ='hr.payslip'
    def action_payslip_done(self):
        self.contract_id.write({'commission':0})
        return super(HRPAYSLIP, self).action_payslip_done()

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
