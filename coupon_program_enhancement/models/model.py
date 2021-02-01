# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class SaleCoupon(models.Model):

    _inherit = 'sale.coupon'

    validity_duration = fields.Integer(string="Validity Duration" )

    