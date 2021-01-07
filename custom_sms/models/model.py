# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class SendSMS(models.Model):
    _name = 'send.sms'
    _description = 'Send SMS'

    name    = fields.Many2one('res.partner' , string="Customer" , required=True)
    phone   = fields.Integer(string="Phone" , required=True)
    massage = fields.Text(string="Massage" , require=True)