# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _ , api

class CustomExtra(models.Model):
    _name = 'custom.extra.field.selection'

    value = fields.Char(string = 'Value' , required="1")
    sequence = fields.Char()
    custom_id = fields.Many2one('custom.appointment.contact.info.field')


class Appointment777(models.Model):
    _name ='custom.appointment.contact.info.field'


    name=fields.Char(required="True")
    ttype=fields.Selection([('char','Single Line Text'),
    ('text','Simple Text'),
    ('html','Rich Text'),
    ('integer','Integer Number'),
    ('float','Float Number'),
    ('selection','Dropdown'),
    ('boolean','Checkbox'),
    ('date','Date'),
    ('datetime','Date and time'),
    ('many2one','Reference (Many2one)'),
    ('binary','Binary')],"Type")
    sel_options_ids=fields.One2many('custom.extra.field.selection','custom_id',string = 'Selection options')
    res_model=fields.Many2one('ir.module.module', domain=[('state' , '=' , 'installed')] ,string="Related to")

    placement=fields.Selection([('group_custom_fields','Custom Tab'),('left_panel_group','Left Column'),('right_panel_group','Rigth Column'),('after_description_group','After Description')]," Backend Form View Placement",required="True",default="group_custom_fields")
    portal_placement=fields.Selection([('after_descri','At the end'),('left_panel_group','Left Column'),('right_panel_group','Rigth Column')],"Portal Page Placement")

    input_placement=fields.Selection([('group_custom_fields','At the end')] ,"Input Form Placement")
    required=fields.Boolean("Required to enter a value")
    used_in_report=fields.Boolean("Used for Analysis")
    # ..................................
    class Appointment7737(models.Model):
        _name ='custom.business.resource.type.field'


        name=fields.Char(required="True")
        ttype=fields.Selection([('char','Single Line Text'),
        ('text','Simple Text'),
        ('html','Rich Text'),
        ('integer','Integer Number'),
        ('float','Float Number'),
        ('selection','Dropdown'),
        ('boolean','Checkbox'),
        ('date','Date'),
        ('datetime','Date and time'),
        ('many2one','Reference (Many2one)'),
        ('binary','Binary')],"Type")
        sel_options_ids=fields.One2many('custom.extra.field.selection','custom_id',string = 'Selection options')
        res_model=fields.Many2one('ir.module.module', domain=[('state' , '=' , 'installed')],string="Related to")

        placement=fields.Selection([('group_custom_fields','Custom Tab'),('left_panel_group','Left Column'),('right_panel_group','Rigth Column'),('after_description_group','After Description')]," Backend Form View Placement",required="True",default="group_custom_fields")
        portal_placement=fields.Selection([('after_descri','At the end'),('left_panel_group','Left Column'),('right_panel_group','Rigth Column')],"Portal Page Placement")

        required=fields.Boolean("Required to enter a value")
# .....................................
class Appointmenttt77437(models.Model):
    _name ='custom.business.resource.field'


    name=fields.Char(required="True")
    ttype=fields.Selection([('char','Single Line Text'),
    ('text','Simple Text'),
    ('html','Rich Text'),
    ('integer','Integer Number'),
    ('float','Float Number'),
    ('selection','Dropdown'),
    ('boolean','Checkbox'),
    ('date','Date'),
    ('datetime','Date and time'),
    ('many2one','Reference (Many2one)'),
    ('binary','Binary')],"Type")
    sel_options_ids=fields.One2many('custom.extra.field.selection','custom_id',string = 'Selection options')
    res_model=fields.Many2one('ir.module.module', domain=[('state' , '=' , 'installed')],string="Related to")
    placement=fields.Selection([('group_custom_fields','Custom Tab'),('left_panel_group','Left Column'),('right_panel_group','Rigth Column'),('after_description_group','After Description')]," Backend Form View Placement",required="True",default="group_custom_fields")
    portal_placement=fields.Selection([('after_descri','At the end'),('left_panel_group','Left Column'),('right_panel_group','Rigth Column')],"Portal Page Placement")
    required=fields.Boolean("Required to enter a value")
    types_ids=fields.Many2many('business.resource.type',"Types")
    # ..................................
    class Appointmenttt77s437(models.Model):
        _name ='custom.appointment.product.field'


        name=fields.Char(required="True")
        ttype=fields.Selection([('char','Single Line Text'),
        ('text','Simple Text'),
        ('html','Rich Text'),
        ('integer','Integer Number'),
        ('float','Float Number'),
        ('selection','Dropdown'),
        ('boolean','Checkbox'),
        ('date','Date'),
        ('datetime','Date and time'),
        ('many2one','Reference (Many2one)'),
        ('binary','Binary')],"Type")
        sel_options_ids=fields.One2many('custom.extra.field.selection','custom_id',string = 'Selection options')
        res_model=fields.Many2one('ir.module.module', domain=[('state' , '=' , 'installed')],string="Related to")
        placement=fields.Selection([('group_custom_fields','Custom Tab'),('left_panel_group','Left Column'),('right_panel_group','Rigth Column'),('after_description_group','After Description')]," Backend Form View Placement",required="True",default="group_custom_fields")
        portal_placement=fields.Selection([('after_descri','At the end'),('left_panel_group','Left Column'),('right_panel_group','Rigth Column')],"Portal Page Placement")
        required=fields.Boolean("Required to enter a value")
