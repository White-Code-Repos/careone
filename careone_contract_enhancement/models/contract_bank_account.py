from odoo import models, fields, api


class ContractBankAccount(models.Model):
    _name = 'bank.account'
    _description = 'Bank Accounts'

    name = fields.Text("Bank Name")
    bank_account_number = fields.Text("Bank Account Number")
    contract_id = fields.Many2one(comodel_name='hr.contract', string='Contract')
