# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FleetVehicleNumberSearch(models.Model):

    _inherit = 'fleet.vehicle'

    @api.model
    def name_get(self):
        res = []
        for rec in self:
            res.append(('%s  -  %s' %(rec.model_id.name , rec.license_plate)))
        return res

