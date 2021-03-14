# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _ , api



class Appointment2(models.Model):
    _name = 'business.appointment.core'
    _rec_name = "combination"

    state = fields.Selection([
        ('draft', 'Pre_Reservation'),
        ('need_approval', 'Awaiting Confirmation'),
        ('processed', 'Processed')], string='Stage', index=True, readonly=True, copy=False, default='draft')

    resource_id=fields.Many2one('business.resource',"Resource")
    service_id=fields.Many2one('appointment.product',"Service")
    datetime_start=fields.Datetime(string="Reserved Time")
    datetime_end=fields.Datetime()
    user_id=fields.Many2one('res.users',"Responsible")
    pricelist_id=fields.Many2one('product.pricelist',"Pricelist")
    website_id=fields.Many2one('website',"Website")
    company_id=fields.Many2one('res.company',"Company")
    partner_id=fields.Many2one('res.partner',"Contact")
    contact_name=fields.Char("Contact Name")
    title=fields.Many2one('res.partner.title',"Title")
    email=fields.Char("Email")
    phone=fields.Char("Phone")
    mobile=fields.Char("Mobile")
    function=fields.Char("Job Position")
    street=fields.Char("Street")
    street2=fields.Char("Street2")
    city=fields.Char("City")
    state_id=fields.Many2one('res.country.state',"State")
    zipcode=fields.Char("Zip")
    country_id=fields.Many2one('res.country',"Country")
    parent_company_id=fields.Many2one('res.partner',"Parent Country")
    partner_name=fields.Char("Partner Name")
    extra_product_ids=fields.One2many('associated.product.line','appointment_core_id',string="Complementary Products")
    description=fields.Text()
    create_date=fields.Datetime()
    schedule_datetime=fields.Datetime("Schedule Datetime")
    combination = fields.Char(string='Combination', compute='_compute_fields_combination')


    def _compute_fields_combination(self):
        for test in self:
            test.combination = 'Appointment for' +' ' + str(test.resource_id.name) + ' ' + 'by False'


    def action_cancel_prereserv(self):
        self.state="processed"



























class appointmentttt(models.Model):
    _name = 'associated.product.line'
    appointment_core_id=fields.Many2one('business.appointment.core')
    product_id=fields.Many2one('product.product',"Product")
    product_uom_qty=fields.Integer("Quantity")
