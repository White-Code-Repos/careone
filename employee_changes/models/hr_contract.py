from odoo import models, fields ,api

class HrContract(models.Model):
    _inherit = 'hr.contract'

    attachment_ids = fields.One2many('contract.attachment','contract_id')

    settelment_allowance = fields.Float()
    transportation_allowance = fields.Float()
    other_allowance = fields.Float()

    gosi_record_number = fields.Char()
    gosi_record_date = fields.Date()
    gosi_record_type = fields.Selection([('saudi','Saudi'),('not_saudi','Not Saudi')])
    gosi_record_salary = fields.Float()
    gosi_record_end_date = fields.Date()

class ContractAttch(models.Model):
    _name = 'contract.attachment'

    contract_id = fields.Many2one('hr.contract')
    attachment = fields.Binary()
