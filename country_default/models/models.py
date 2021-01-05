# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CountryDefault(models.Model):

    _inherit = 'res.partner'

    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('name', '=', 'السعودية')], limit=1)
        return country

    country_id = fields.Many2one('res.country', string="Country Name" , default=_get_default_country , )

