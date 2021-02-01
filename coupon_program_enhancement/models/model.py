# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError

class SaleCoupon(models.Model):

    _inherit = 'sale.coupon'

    validity_duration = fields.Integer(string="Validity Duration")
    validity_duration1 = fields.Integer(string="Validity Duration", compute='compute_validity_duration')

    def compute_validity_duration(self):
        for this in self:
            if this.validity_duration == 0:
                this.validity_duration1 = this.program_id.validity_duration
                this.validity_duration = this.program_id.validity_duration