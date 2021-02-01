# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date

class SaleCoupon(models.Model):

    _inherit = 'sale.coupon'

    validity_duration = fields.Integer(string="Validity Duration", compute = '_compute_validity_duration', store = True)

    @api.model
    def _compute_validity_duration(self):
        for this in self:
            if this.validity_duration == 0 and this.create_date.date == date.today():
                this.validity_duration = this.program_id.validity_duration


    