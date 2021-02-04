# -*- coding: utf-8 -*-
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime
from odoo.tools import float_round, date_utils
import logging
_logger = logging.getLogger(__name__)


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Loan Installment", help="Loan installment")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []
        contracts = self.env['hr.contract']

        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(date_from), "%Y-%m-%d")))
        locale = self.env.context.get('lang') or 'en_US'
        self.name = _('Salary Slip of %s for %s') % (
            employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        self.company_id = employee.company_id
        if not self.contract_id or self.employee_id != self.contract_id.employee_id: # Add a default contract if not already defined
            contracts = employee._get_contracts(date_from, date_to)

            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                self.contract_id = False
                self.struct_id = False
                return
            self.contract_id = contracts[0]
            self.struct_id = contracts[0].structure_type_id.default_struct_id
        if date_to > date_utils.end_of(fields.Date.today(), 'month'):
            self.warning_message = _("This payslip can be erroneous! Work entries may not be generated for the period from %s to %s." %
                (date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1), date_to))
        else:
            self.warning_message = False

        self.worked_days_line_ids = self._get_new_worked_days_lines()


        # if not self.env.context.get('contract') or not self.contract_id:
        #     contract_ids = self.get_contract(employee, date_from, date_to)
        #     if not contract_ids:
        #         return
        #     self.contract_id = self.env['hr.contract'].browse(contract_ids[0])
        #
        # if not self.contract_id.struct_id:
        #     return
        # self.struct_id = self.contract_id.struct_id
        #
        # # computation of the salary input
        # contracts = self.env['hr.contract'].browse(contract_ids)
        # worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        # worked_days_lines = self.worked_days_line_ids.browse([])
        # for r in worked_days_line_ids:
        #     worked_days_lines += worked_days_lines.new(r)
        # self.worked_days_line_ids = worked_days_lines
        # if len(contracts) > 0:
        #     input_line_ids = self.get_inputs(contracts, date_from, date_to)
        #     input_lines = self.input_line_ids.browse([])
        #     for r in input_line_ids:
        #         input_lines += input_lines.new(r)
        #     self.input_line_ids = input_lines
        lon_obj = self.env['hr.loan'].search([('employee_id', '=', employee.id), ('state', '=', 'approve')])
        # _logger.info("<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>")
        # _logger.info(res)
        # _logger.info(contract_ids)
        # _logger.info(lon_obj)
        # _logger.info("<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>")
        for loan in lon_obj:
            for loan_line in loan.loan_lines:
                if date_from <= loan_line.date <= date_to and not loan_line.paid:
                    payslip_other_input_type = self.env['hr.payslip.input.type'].search([('code','=','LO')], limit=1)
                    old_inputs = self.env['hr.payslip.input'].search([('payslip_id','=',self.id)]).filtered(lambda x:x.code == 'LO')
                    if len(old_inputs) > 0:
                        # self.input_line_ids = [(1,old_inputs[0].id,{'input_type_id':payslip_other_input_type.id,'amount':loan_line.amount})]
                        pass
                    else:
                        self.input_line_ids = [(0,0,{'input_type_id':payslip_other_input_type.id,'amount':loan_line.amount,'loan_line_id':loan_line.id})]

                    # for result in res:
                    #     if result.get('code') == 'LO':
                    #         result['amount'] = loan_line.amount
                    #         result['loan_line_id'] = loan_line.id

        return

    # def get_inputs(self, contract_ids, date_from, date_to):
    #     """This Compute the other inputs to employee payslip.
    #                        """
    #     res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
    #     # _logger.info("<<<<<<<<<<<<<<<<res>>>>>>>>>>>>>>>>>>")
    #     # _logger.info(res)
    #     # _logger.info("<<<<<<<<<<<<<<<<res>>>>>>>>>>>>>>>>>>")
    #     contract_obj = self.env['hr.contract']
    #     emp_id = contract_obj.browse(contract_ids[0].id).employee_id
    #     lon_obj = self.env['hr.loan'].search([('employee_id', '=', emp_id.id), ('state', '=', 'approve')])
    #     # _logger.info("<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>")
    #     # _logger.info(res)
    #     # _logger.info(contract_ids)
    #     # _logger.info(lon_obj)
    #     # _logger.info("<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>")
    #     for loan in lon_obj:
    #         for loan_line in loan.loan_lines:
    #             if date_from <= loan_line.date <= date_to and not loan_line.paid:
    #                 for result in res:
    #                     if result.get('code') == 'LO':
    #                         result['amount'] = loan_line.amount
    #                         result['loan_line_id'] = loan_line.id
    #     return res

    def action_payslip_done(self):
        for line in self.input_line_ids:
            if line.loan_line_id:
                line.loan_line_id.paid = True
                line.loan_line_id.payslip_id = self.id
                line.loan_line_id.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_done()
