# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError

class SaleCoupon(models.Model):

    _inherit = 'sale.coupon'

    validity_duration = fields.Integer(string="Validity Duration", compute ='_compute_validity_duration', store = True)

    @api.model
    def create(self, vals):
        rec = super(SaleCoupon, self).create(vals)
        rec.ensure_one()
        return rec

    @api.model
    def _compute_validity_duration(self):
        for this in self:
            print(fffffff)
            # if this.validity_duration == 0:
            this.validity_duration = this.program_id.validity_duration