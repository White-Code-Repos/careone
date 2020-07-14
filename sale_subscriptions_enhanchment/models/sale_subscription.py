# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SalesSubscriptionTemplate(models.Model):
    _inherit = "sale.subscription.template"

    freeze_for = fields.Integer('Freeze For')