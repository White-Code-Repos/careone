# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date,datetime

class HrSalaryRule(models.Model):

    _inherit = "hr.salary.rule"
    is_need_input = fields.Boolean(string="Is Need Input")

class HrSalaryInput(models.Model):

    _inherit = "hr.payslip.input"
    rule_id = fields.Many2one('hr.salary.rule', string='Rule')

class HrPayslip(models.Model):

    _inherit = "hr.payslip"

    def compute_sheet(self):
        for payslip in self.filtered(lambda slip: slip.state not in ['cancel', 'done']):
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            payslip.line_ids.unlink()
            lines = [(0, 0, line) for line in payslip._get_payslip_lines()]
            payslip.write({'line_ids': lines, 'number': number, 'state': 'verify', 'compute_date': fields.Date.today()})
            for line in payslip.line_ids:
                if line.salary_rule_id.is_need_input == True:
                    line.unlink()
            rules = []
            for line in payslip.input_line_ids:
                if line.rule_id.id:
                    rules.append((0, 0, {
                        'salary_rule_id' : line.rule_id.id,
                        'amount' : line.amount * line.rule_id.amount_fix,
                        'code'   : line.rule_id.code,
                        'name'   : line.rule_id.name,
                    }))
            payslip.write({'line_ids': rules})
        return True