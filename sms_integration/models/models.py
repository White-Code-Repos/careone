# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SMSIntegration(models.Model):
    _name = 'sms.integration'
    _description = 'SMS Integration'

    name     = fields.Char(string="Name"       , required=True)
    state    = fields.Boolean(string="Active"  , default=False)
    attr_ids = fields.One2many('attr.line.ids' , 'sms_integration_id' , string="Attributes")

    @api.constrains('state')
    def _check_state(self):
        if self.state == True:
            for record in self:
                state = record.search([('state', '=', True), ('id', '!=', record.id)])
                if state:
                    raise ValidationError('You can not active more than one of sms api, Please check api record and try again.')
    
class SMSAttributesLines(models.Model):
    _name = 'attr.line.ids'
    _description = 'SMS Attributes Lines'

    name  = fields.Char(string="Name"  , required=True)
    value = fields.Char(string="Value" , required=True)
    sms_integration_id = fields.Many2one('sms.integration')
