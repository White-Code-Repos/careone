# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _ , api



class Appointment5(models.Model):
    _name = 'appointment.product'

    image=fields.Binary()
    name=fields.Char(required="True",string="Service Name")
    appointment_duration=fields.Float("Appointment Default Duration",default="01.00")
    appointment_duration_days=fields.Float("Appointment Default Duration",default="1")
    duration_uom=fields.Selection([ ('hours', 'hours'),('days', 'days')],default="hours")
    location=fields.Char("Location")
    product_id=fields.Many2one('product.product','Related Product')
    suggested_product_ids=fields.Many2many('product.product',string='Complementary Products')
    start_round_rule=fields.Float("Start Round",default="00.30")
    start_round_rule_days=fields.Float("Start Time",default="00.00")
    manual_duration=fields.Boolean("Allow Manual Duration")
    min_manual_duration=fields.Float("Min Duration Hours",default="00.30")
    max_manual_duration=fields.Float("Max Duration Hours",default="02.00")
    multiple_manual_duration=fields.Float("Multiple for Hours",default="00.30")
    min_manual_duration_days=fields.Integer("Min Duration Days",default="1")
    max_manual_duration_days=fields.Integer("Min Duration Days",default="1")
    multiple_manual_duration_days=fields.Integer("Multiple for Days",default="1")
    description=fields.Text()
    group_custom_fields=fields.Char()
    website_id=fields.Many2one('website','Website')
    donotshow_full_description=fields.Boolean("Do not show website full description")
    service_ids=fields.Many2one('business.resource')
