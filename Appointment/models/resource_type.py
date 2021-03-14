# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _


class Appointment3(models.Model):
    _name = 'business.resource.type'

    image=fields.Binary()
    name=fields.Char(required="True")
    id=fields.Integer(string="ID")
    color=fields.Integer(string="Color")
    service_method=fields.Selection([ ('multiple', 'service should be selected for resources and for appointment'),('single', 'service is always the same for all resources and for appointments'),],'Service Method', default='multiple',required="True")
    service_ids=fields.Many2many("appointment.product",string="Available Services",required="True")
    always_service_id=fields.Char("Service")
    allocation_type=fields.Selection([ ('automtic', 'Automatic'),('manual', 'Manual')],'Resource Selection', default='manual',required="True")
    allocation_method=fields.Selection([ ('by_order', 'By Order'),('by_number', 'By Appointments Number'),('by_workload', 'By Workload')],'Resource Allocation Method', default='by_number',required="True")
    pricing_method=fields.Selection([ ('per_planned_duration', 'Planned Duration'),('per_unit', 'Units'),('per_real_duration', 'Tracked Duration')],'Calculate price for', default='per_planned_duration',required="True")
    allowed_from=fields.Integer("Reservation should be done in",default="1")
    allowed_from_uom=fields.Selection([ ('minutes', 'minutes'),('hours', 'hours'),('days', 'days'),('weeks', 'weeks'),('months', 'months'),('years', 'years')], default='days',required="True")
    allowed_to=fields.Integer("Reservation should not be done after	Portal:",default="30")
    allowed_to_uom=fields.Selection([ ('minutes', 'minutes'),('hours', 'hours'),('days', 'days'),('weeks', 'weeks'),('months', 'months'),('years', 'years')], default='days',required="True")
    allowed_cancellation=fields.Integer("Cancellation/Re-Schedule might be done in",default="1")
    allowed_cancellation_uom=fields.Selection([ ('minutes', 'minutes'),('hours', 'hours'),('days', 'days'),('weeks', 'weeks'),('months', 'months'),('years', 'years')], default='days',required="True")
    calendar_event_workload=fields.Boolean("Calendar Events as Busy Time")
    rating_option=fields.Boolean("Appointments Customer Rating")
    success_mail_template_id=fields.Many2one('mail.template','Success Email')
    rating_mail_template_id=fields.Many2one('mail.template','Rating Email')
    description=fields.Text()
    group_custom_fields=fields.Char()
    website_id=fields.Many2one('website','Website')
    donotshow_full_description=fields.Boolean("Do not show website full description")
    default_alarm_ids=fields.Many2many("appointment.alarm",string="Default Alarms")
