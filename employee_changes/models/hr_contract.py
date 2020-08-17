from odoo import models, fields ,api

class HrContract(models.Model):
    _inherit = 'hr.contract'

    attachment_ids = fields.One2many('contract.attachment','contract_id')

class ContractAttch(models.Model):
    _name = 'contract.attachment'

    contract_id = fields.Many2one('hr.contract')
    attachment = fields.Binary()