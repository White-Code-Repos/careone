# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _ , api



class Appointment6(models.TransientModel):
    _inherit = 'res.config.settings'

    ba_max_preresevation_time=fields.Float("Maximim Period for Pre-Reservation",default="00.30")
    ba_multi_scheduling=fields.Boolean("Multi Scheduling",default="True")
    ba_max_multi_scheduling=fields.Integer("Maximum Appointments (Backend)",default="3")
    group_product_pricelist=fields.Boolean()
    product_pricelist_setting=fields.Selection([
        ('basic', 'Multiple prices per product'),
        ('advanced', 'Advanced price rules (discounts, formulas)')],default="basic")
    ba_extra_products_backend=fields.Boolean(default="True",string="Complementary Products Offer")
    business_appointment_rating=fields.Boolean(default="True",string="Use Rating for Appointments")
    appointment_website=fields.Boolean(default="True",string="Appointments in Portal and Website")
    ba_approval_type=fields.Selection([('no','No Confirmation'),('email','Email Confirmation'),('sms','SMS Confirmation')],default="no",string="Website / Portal Confirmation")
    ba_max_approval_time=fields.Float("Maximim Period for Confirmation (h.)",default="02.00")
    ba_max_approval_trials=fields.Integer("Maximum Number of Attempts to Confirm",default="5")
    ba_confirmation_retry_period=fields.Integer("New Confirmation Code Minimum Period (s.)",default="60")
    ba_confirmation_retry_trials=fields.Integer("Maximum Number of Code Refreshing",default="3")
    appoin_comp_tz=fields.Many2one("res.country",string="Company Timezone")

    appointment_sale=fields.Boolean(string="Link Appointments to Sale Orders" , default="True")
    ba_auto_sale_order= fields.Selection([
        ('no','No Auto Creation'),
        ('draft','Auto Draft Sale Order'),
        ('confirmed','Auto Confirmed Sale Order')], string='Auto Sale Order', default='draft')
    appointment_website_sale=fields.Boolean(default="True",string="Website Sales")
    appointment_custom_fields=fields.Boolean(default="True",string="Custom Fields")
    appointment_custom_fields_website=fields.Boolean(default="True",string="Portal and Website Custom Fields")
    appointment_hr=fields.Boolean(default="True",string="Employees as Resources")
    appointment_website_id=fields.Many2one('website',string="Website for appointments")
    ba_turn_on_appointments=fields.Boolean(default="True",string="Business appointments in portal")
    ba_turn_on_appointments_public=fields.Boolean(default="True",string="Business appointments on website")
    ba_step_1=fields.Char(string="Label for step 1: Choose resource type",default="Choose resource type")
    ba_step_2=fields.Char(string="Label for step 2: Choose resource",default="Choose resource")
    ba_step_3=fields.Char(string="Label for step 3: Choose service",default="Choose service")
    ba_step_4=fields.Char(string="Label for step 4: Choose time",default="Choose time")
    ba_step_5=fields.Char(string="Label for step 5: Account Details",default="Account Details")
    ba_step_6=fields.Char(string="Label for step 6: Confirmation",default="Confirmation")

    ba_contact_info=fields.Many2one("res.country",string="Company Timezone")
    ba_contact_info_mandatory_ids=fields.Many2many("ir.model.fields")
    ba_max_portal=fields.Integer("Maximum Appointments (Portal)",default="2")

    agree_public=fields.Boolean(default="True",string="Agree on terms and conditions")
    public_only=fields.Boolean(default="True",string="Terms for public users only")
    agree_text=fields.Text(string="Agree on terms text",default="I have read and agree to the terms presented in the <a href='/''>Terms and Conditions agreement</a>.")
    appointment_filter=fields.Many2many("ir.filters",string="Custom Portal Appointment Filters")
    appointment_search=fields.Many2many("business.appointment.custom.search",string="Custom Portal Appointment Search")
    details_page=fields.Boolean(default="True",string="Show types full details pages")
    resource_details=fields.Boolean(default="True",string="Show resources full details pages")
    servicee_details=fields.Boolean(default="True",string="Show services full details pages")
    product_reservation=fields.Boolean(default="True",string="Complementary Products for Reservation")
    pricesandpricelist=fields.Boolean(default="True",string="Pricelists and Prices")












class Appointment7(models.Model):
    _inherit = 'resource.calendar'
    name=fields.Char("working Time")




class Appointment66557(models.Model):
    _name = 'business.appointment.custom.search'
