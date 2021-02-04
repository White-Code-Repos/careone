# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime
from odoo.exceptions import ValidationError

class SaleCoupon(models.Model):

    _inherit = 'sale.coupon'

    validity_duration = fields.Integer(string="Validity Duration")