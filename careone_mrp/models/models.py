from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    
    emp_ids = fields.Many2many(
        string='employees',
        comodel_name='hr.employee',
    )
    