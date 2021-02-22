from odoo import models, fields, api, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    branch_id = fields.Many2one(comodel_name='res.branch')