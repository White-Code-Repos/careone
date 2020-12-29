from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MRP_inherit_EXT(models.Model):
    _inherit = 'mrp.production'

    
