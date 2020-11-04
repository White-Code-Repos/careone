from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    emp_ids = fields.Many2many(string='employees',comodel_name='res.user',)
    
    