# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ArchiveModel(models.Model):

    _inherit = 'fleet.vehicle.model'

    active = fields.Boolean(string="Active" , default=True)