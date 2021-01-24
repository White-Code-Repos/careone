# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MRPProduction(models.Model):

    _inherit = "mrp.production"
    _order = 'state'