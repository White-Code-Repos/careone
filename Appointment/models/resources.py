# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _




class Appointment4(models.Model):
    _name = 'business.resource'

    resource_id=fields.Many2one('business.appointment')
    image=fields.Binary()
    name=fields.Char(required="True")
    resource_type=fields.Selection([ ('user', 'Human'),('material', 'Material'),],'Resource Kind',default='material',required="True")
    resource_type_id=fields.Many2one('business.resource.type',"Type")
    resource_calendar_id=fields.Many2one('resource.calendar',"Working Hours")
    user_id=fields.Many2one('res.users','Responsible')
    location=fields.Char("Location")
    description=fields.Text()
    group_custom_fields=fields.Char()
    website_id=fields.Many2one('website','Website')
    donotshow_full_description=fields.Boolean("Do not show website full description")
    service_ids=fields.Many2many("appointment.product")
