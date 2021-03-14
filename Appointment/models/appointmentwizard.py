# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _ , api
import datetime
from datetime import timedelta, date


class ExtraCl(models.TransientModel):
    _name = 'extra.cl'
    _order = 'id desc'


    done = fields.Boolean()
    resource_id=fields.Many2one("business.resource")
    service_id=fields.Many2one('appointment.product')
    day_date = fields.Char()
    day_name = fields.Char()
    tim_from = fields.Float()
    tim_to = fields.Float()
    resource_type_id=fields.Many2one('business.resource.type')
    Quantity = fields.Integer()
    make_appointment_id = fields.Many2one('make.appointment.business')
    product_id = fields.Many2one('product.template')

class Complementary(models.TransientModel):
    _name = 'complementary.product'
    _order = 'id desc'

    comp_done = fields.Boolean()
    comp_quantity = fields.Float()
    comp_total_price=fields.Float()
    comp_price=fields.Float()
    comp_name=fields.Char()
    make_appointment_id = fields.Many2one('make.appointment.business')

    @api.onchange("comp_quantity")
    def calculate_price(self):
        # self.comp_done="True"
        self.comp_total_price = self.comp_quantity * self.comp_price

#the main object of first wizard
class Appointmentwizard(models.TransientModel):
    _name = 'make.appointment.business'


    x=fields.Boolean()
    c=fields.Boolean()
    date_start=fields.Date()
    date_end=fields.Date()
    timeslots=fields.Char()
    y=fields.Boolean()
    service_ids=fields.Many2many("appointment.product")
    resource_type_id=fields.Many2one('business.resource.type', string="Resource Type", required="True")
    resource_id=fields.Many2one("business.resource")
    service_id=fields.Many2one('appointment.product',string="Service")



    @api.onchange('service_id')
    def com_product(self):
        lines = [(5, 0, 0)]
        if self.service_id:
            for line in self.service_id.suggested_product_ids:
                ob=self.env['product.template'].search([('id','=',line.id)])
                lines.append((0, 0, {

                               'comp_done': False,
                               'comp_quantity' :0.0,
                               'comp_total_price':0.0,
                               'comp_price':ob.lst_price,

                               'comp_name':ob.name,
                               }))

        self.complementary_product = lines

    complementary_product= fields.One2many('complementary.product' , 'make_appointment_id' ,string="Complementary Products",readonly="False")




    @api.onchange("x_quantity")
    def calculate_price(self):
        self.x_price = self.x_quantity * self.lst_price

    @api.onchange("x_done")
    def calculate_allprice1(self):
        self.price = self.x_price


    Quantity = fields.Integer()
    done = fields.Boolean()
    appointment_duration=fields.Many2one("appointment.product")
    product_id = fields.Many2one('product.template')
    priceofservice=fields.Float(related="service_id.product_id.lst_price" ,readonly="1")
    time=fields.Float(related="service_id.appointment_duration")
    calendar=fields.Many2one(related="resource_id.resource_calendar_id")
    calendar1=fields.Float(related="calendar.attendance_ids.hour_from")
    day=fields.Selection(related="calendar.attendance_ids.day_period")
    z=fields.Boolean()
    date_day = fields.Char('Day')
    email = fields.Char("Email")
    phone = fields.Char("Phone")
    mobile = fields.Char("Mobile")
    function = fields.Char("Job Position")
    partner_name = fields.Char("Job Position")
    description = fields.Text("Notes")
    street = fields.Char("Street")
    street2 = fields.Char("Street2")
    city = fields.Char("City")
    state_id = fields.Many2one('res.country.state', "State")
    zipcode = fields.Char("Zip")
    country_id = fields.Many2one('res.country', "Country")
    parent_company_id = fields.Many2one('res.partner', "Parent Country")
    partner_id = fields.Many2one('res.partner', "Contact")
    contact_name = fields.Char("Contact Name")
    title = fields.Many2one('res.partner.title', "Title")
    w=fields.Boolean()


    @api.onchange('service_id')
    def Services2(self):
        if self.service_id:
            self.y = 'True'


    @api.onchange('resource_id')
    def _get_domain_services(self):
        for item in self:
            service_id = self.env['business.resource'].search(
                [('resource_id', '=', item.resource_id.id)])

            return {'domain': {'service_id': [('id', 'in',self.resource_id.service_ids.ids)]}}




    def daterange(self , start_date, end_date):
        for n in range(int((end_date - start_date).days)+1):
            yield start_date + timedelta(n)

    def ret_key_select(self , dayname):
        if dayname == 'Monday':
            return 0
        if dayname == 'Tuesday':
            return 1
        if dayname == 'Wednesday':
            return 2
        if dayname == 'Thursday':
            return 3
        if dayname == 'Friday':
            return 4
        if dayname == 'Saturday':
            return 5
        if dayname == 'Sunday':
            return 6

    @api.onchange('resource_id')
    def a(self):
        if self.resource_id:
            self.x = 'True'
        if self.date_start and self.date_end and self.calendar:
            lines = [(5, 0, 0)]
            year, month, day = (int(x) for x in str(self.date_start).split('-'))
            start_date = date(year, month, day)
            year, month, day = (int(x) for x in str(self.date_end).split('-'))
            end_date = date(year, month, day)
            for single_date in self.daterange(start_date, end_date):

                pp = single_date.strftime("%Y-%m-%d")
                year, month, day = (int(x) for x in str(pp).split('-'))
                ans = date(year, month, day)
                day_name = ans.strftime("%A")
                key = self.ret_key_select(day_name)
                for line in self.calendar.attendance_ids:

                    if str(line.dayofweek) == str(key):
                        start = line.hour_from
                        end = line.hour_from + self.time
                        while end <= line.hour_to and self.time != 0.0:
                            ob = self.env['business.appointment'].search_count([('done' , '=' , 'True') ,
                                                                 ('resource_id' , '=' , self.resource_id.id),
                                                                 ('resource_type_id' , '=' , self.resource_type_id.id),
                                                                 ('service_id' , '=' , self.service_id.id),
                                                                 ('day_date' , '=' , pp),
                                                                 ('day_name' , '=' , day_name),
                                                                 ('tim_from' , '=' , start),
                                                                 ('tim_to' , '=' , end),
                                                                 ])

                            if ob == 0:
                                lines.append((0, 0, {
                                    'resource_type_id':self.resource_type_id.id,
                                    'done':False,
                                    'service_id':self.service_id.id,
                                    'resource_id':self.resource_id.id,
                                    'day_date':pp,
                                    'day_name':day_name,
                                    'tim_from': start,
                                    'tim_to': end,
                                }))
                            start = end
                            end = end + self.time
            self.calen_new = lines



    calen_new = fields.One2many('extra.cl' , 'make_appointment_id' , string="Appointment")
    @api.onchange('calen_new')
    def secondwizard(self):
        for line in self.calen_new:
            if line.done==True:
                self.w="True"


    # def return_action_data(self):
    #     for line in self.calen_new:
    #         if line.done==True:
    #             return {
    #           'type': 'ir.actions.act_window',
    #           'name': 'Choose Contact and Confirm ',
    #           'view_mode': 'form',
    #           'target': 'new',
    #           'res_model': 'person.data',
    #           'context': { 'resource_type_id':self.resource_type_id.id,
    #                         'resource_id':self.resource_id.id,
    #                         'service_id':self.service_id.id,
    #                         'priceofservice':self.priceofservice,
    #                         'time':self.time,
    #                          'done': line.done,
    #                          'day_date':line.day_date,
    #                         'day_name':line.day_name,
    #                         'tim_from':line.tim_from,
    #                         'tim_to':line.tim_to,
    #
    #         }
    #         }
    #
    #     return {
    #           'type': 'ir.actions.act_window',
    #           'name': 'Choose Contact and Confirm ',
    #           'view_mode': 'form',
    #           'target': 'new',
    #           'res_model': 'person.data',
    #           'context': { 'resource_type_id':self.resource_type_id.id,
    #                         'resource_id':self.resource_id.id,
    #                         'service_id':self.service_id.id,
    #                         'priceofservice':self.priceofservice,
    #                         'time':self.time,
    #                          'done': line.done,
    #                          'day_date':line.day_date,
    #                         'day_name':line.day_name,
    #                         'tim_from':line.tim_from,
    #                         'tim_to':line.tim_to,
    #
    #         }
    # }


    def add_booked(self):
        for line in self.calen_new:
            print("#########################3333")
            if line.done==True:
                print("#########################3333")
                for record in self.complementary_product:
                    if record.comp_done==True:
                        self.env['business.appointment'].create(
                            {

                            'resource_type_id':self.resource_type_id.id,
                            'resource_id':self.resource_id.id,
                            'service_id':self.service_id.id,
                            'time':self.time,
                            'priceofservice':self.priceofservice,
                            'comp_quantity':record.comp_quantity,
                            'comp_total_price':record.comp_total_price,
                            'comp_price':record.comp_price,
                            'comp_name':record.comp_name,
                            'day_date':line.day_date,
                            'day_name':line.day_name,
                            'tim_from':line.tim_from,
                            'tim_to':line.tim_to,
                            'email':self.email,
                            'phone':self.phone,
                             'mobile':self.mobile,
                             'function':self.function,
                             'partner_name':self.partner_name ,
                             'description':self.description,
                             'street':self.street,
                            'street2':self.street2,
                            'city':self.city,
                             'state_id':self.state_id,
                            'zipcode':self.zipcode,
                             'country_id':self.country_id,
                            'parent_company_id':self.parent_company_id,
                            'partner_id':self.partner_id,
                             'contact_name': self.contact_name,
                             'title':self.title,

                            }
                        )





#test returned data
class BookedTime(models.Model):
    _name = 'business.appointment'
    _order = 'id desc'

    done = fields.Boolean()
    resource_id = fields.Many2one("business.resource")
    service_id = fields.Many2one('appointment.product')
    day_date = fields.Char()
    day_name = fields.Char()
    tim_from = fields.Float()
    tim_to = fields.Float()
    resource_type_id=fields.Many2one('business.resource.type')
    time=fields.Float()
    priceofservice=fields.Float()
    email = fields.Char("Email")
    phone = fields.Char("Phone")
    mobile = fields.Char("Mobile")
    function = fields.Char("Job Position")
    partner_name = fields.Char("Job Position")
    description = fields.Text("Notes")
    street = fields.Char("Street")
    street2 = fields.Char("Street2")
    city = fields.Char("City")
    state_id = fields.Many2one('res.country.state', "State")
    zipcode = fields.Char("Zip")
    country_id = fields.Many2one('res.country', "Country")
    parent_company_id = fields.Many2one('res.partner', "Parent Country")
    partner_id = fields.Many2one('res.partner', "Contact")
    contact_name = fields.Char("Contact Name")
    title = fields.Many2one('res.partner.title', "Title")
    x_done = fields.Boolean()
    x_quantity = fields.Integer()
    x_price=fields.Float()
    price=fields.Float()
    name=fields.Char()
    comp_done = fields.Boolean()
    comp_quantity = fields.Float()
    comp_total_price=fields.Float()
    comp_price=fields.Float()
    comp_name=fields.Char()
