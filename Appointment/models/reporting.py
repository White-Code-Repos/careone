# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _ , api

class Reporting1(models.Model):
    _name = 'appointment.analytic'

    datetime_start=fields.Datetime()
    resource_type_id=fields.Many2one("business.resource.type")
    resource_id=fields.Many2one("business.resource")
    duration=fields.Float("Duration")

class Reporting2(models.Model):
    _name = 'rating.appointment'

    nameofresource=fields.Char(string="Resource name")
    parent_nameofresource=fields.Char("Parent Document Name")
    rated_partner_id=fields.Many2one("res.partner",string="Rated Person")
    partner_id=fields.Many2one("res.partner",string="Customer")
    rating_text=fields.Selection([('satisfied','Satisfied'),('not_satisfied','Not satisfied'),('highly_dissatisfied','Highly dissatisfied'),('no_rating','No Rating yet')],string="Rating")
    feedback=fields.Text("Comment")
    create_date=fields.Datetime(string="Created On")
    rating_image=fields.Binary(string="Image")
    rating=fields.Float(string="Rating Number")
