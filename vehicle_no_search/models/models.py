# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FleetVehicleNumberSearch(models.Model):

    _inherit = 'fleet.vehicle'

    def name_get(self):
        res = []
        for rec in self:
            if rec.id and rec.model_id.name and rec.license_plate:
                res.append((rec.id, '%s  -  %s' %(rec.model_id.name , rec.license_plate)))
        return res

