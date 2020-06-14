# -*- coding: utf-8 -*-

import logging
import urllib
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SendWhatsapp(models.TransientModel):
    _name = 'send.whatsapp.partner'
    _description = 'Send Whatsapp'

    partner_id = fields.Many2one('res.partner', domain="[('parent_id','=',partner_id)]")
    default_messege_id = fields.Many2one('whatsapp.template', domain="[('category', '=', 'partner')]")

    name = fields.Char(related='partner_id.name')
    mobile = fields.Char(related='partner_id.mobile',help="use country mobile code without the + sign")

    message = fields.Text(string="Message", required=True)
    format_visible_context = fields.Boolean(default=False)


    @api.onchange('default_messege_id')
    def _onchange_message(self):

        partner_record = self.env['res.partner'].browse(self._context.get('active_id'))
        message = self.default_messege_id.template_messege
        incluid_name = str(message).format(
            name=partner_record.name,
            sales_person=partner_record.user_id.name,
            company=partner_record.company_id.name,
            website=partner_record.company_id.website)

        if message:
            self.message = incluid_name

    @api.model
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.format_visible_context = self.env.context.get('format_invisible', False)
        self.mobile = self.partner_id.mobile

    @api.model
    def close_dialog(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def send_dialog(self, whatsapp_url):
        action = {'type': 'ir.actions.act_url', 'url': whatsapp_url, 'target': 'new', 'res_id': self.id}

    def sending_reset(self):
        partner_id = self.env['res.partner'].browse(self._context.get('active_id'))
        partner_id.update({
            'send_whatsapp': 'without_sending',
            })
        self.close_dialog()

    def sending_confirmed(self):

        if not self.mobile or not self.message:
            raise ValidationError(_("You must send your WhatsApp message before"))

        partner_id = self.env['res.partner'].browse(self._context.get('active_id'))
        message_fomat = '<p class="text-info">Successful Whatsapp</p><p><b>Message sent:</b></p>%s' % self.message
        partner_id._action_whatsapp_confirmed(message_fomat.replace('\n', '<br>'))
        partner_id.update({
            'send_whatsapp': 'sent',
            })
        self.close_dialog()

    def sending_error(self):

        if not self.mobile or not self.message:
            raise ValidationError(_("You must send your WhatsApp message before"))

        partner_id = self.env['res.partner'].browse(self._context.get('active_id'))
        message_fomat = '<p class="text-danger">Error Whatsapp</p><p>The recipient may not have whatsapp / verify the country code / other reasons</p>'
        partner_id._action_whatsapp_confirmed(message_fomat.replace('\n', '<br>'))
        partner_id.update({
            'send_whatsapp': 'not_sent',
            })
        self.close_dialog()

    def send_whatsapp(self):

        if not self.mobile or not self.message:
            raise ValidationError(_("You must add the mobile number or message"))
        else:
            movil = self.mobile
            array_int = re.findall("\d+", movil)
            whatsapp_number = ''.join(str(e) for e in array_int)
            messege_prepare = u'{}'.format(self.message)
            messege_encode = urllib.parse.quote(messege_prepare.encode('utf8'))
            whatsapp_url = 'https://wa.me/{}?text={}'.format(whatsapp_number, messege_encode)

        return {'type': 'ir.actions.act_url',
                    'url': whatsapp_url,
                    'nodestroy': True,
                    'target': 'new',
                    'res_id': self.id
                    }