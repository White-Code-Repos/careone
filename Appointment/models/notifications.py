# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _ , api

class notifications1(models.Model):
    _name='appointment.alarm'
    _rec_name="combination"

    ttype=fields.Selection([('email','Email'),('sms','SMS'),('popup','Popup')],"Type",default="email",required="True")
    duration=fields.Integer("Remind Before",default="1")
    duration_uom=fields.Selection(([ ('minutes', 'Minute(s)'),('hours', 'Hour(s)'),('days', 'Day(s)')]),default="days")
    recipients=fields.Selection([('user_id','Only responsible'),('internal','All internal followers'),('portal','All external followers (portal)'),('everybody','All followers')],default="internal",string="Recipients")
    mail_template_id=fields.Many2one('mail.template',"Email Template")
    sms_template_id=fields.Many2one('sms.template',"SMS Template")
    combination = fields.Char(string='Combination', compute='_compute_fields_combination')



    def _compute_fields_combination(self):
        for test in self:
            var1=dict(test._fields['duration_uom'].selection).get(test.duration_uom)
            var2=dict(test._fields['ttype'].selection).get(test.ttype)
            var3=dict(test._fields['recipients'].selection).get(test.recipients)


            if test.ttype == "email":
                test.combination = str(test.duration) +' ' + var1+ ' ' + var2 + '( ' + var3 + '/' + test.mail_template_id.name + ' )'
            elif test.ttype == "sms":
                test.combination = str(test.duration) +' ' + var1+ ' ' + var2 + '( ' + var3 + '/' + test.sms_template_id.name + ' )'
            else:
                test.combination = str(test.duration) +' ' + var1+ ' ' + var2 + '( ' + var3 + ' )'







class notifications11(models.Model):
    _inherit='mail.template'
    name=fields.Char("Name")

class notifications111(models.Model):
    _inherit='sms.template'
    name=fields.Char("Name")

class notifications1111(models.Model):
    _name='alarm.task'

    alarm_time=fields.Datetime("Alarm Time",readonly="True")
    alarm_id=fields.Many2one('appointment.alarm',"Alarm",required="True")
    appointment_id=fields.Many2one('business.appointment',"Appointment" ,required="True")
