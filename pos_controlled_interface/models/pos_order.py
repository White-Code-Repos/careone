# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
###################################################################################
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    control_discount = fields.Boolean(string='Control Discount')
    control_price = fields.Boolean(string='Control Price')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            control_discount = self.env['ir.config_parameter'].sudo().get_param('control_discount'),
            control_price = self.env['ir.config_parameter'].sudo().get_param('control_price'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('control_discount', self.control_discount)
        self.env['ir.config_parameter'].sudo().set_param('control_price', self.control_price)
