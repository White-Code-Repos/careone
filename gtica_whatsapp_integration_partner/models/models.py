# -*- coding: utf-8 -*-

import logging
from odoo import http, models, fields, api, tools, _

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    send_whatsapp = fields.Selection([
        ('without_sending', 'without sending'),
        ('sent', 'sent'), ('not_sent', 'no sent'),
        ], default='without_sending')

    def send_whatsapp_step(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Send Whatsapp'),
                'res_model': 'send.whatsapp.partner',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_partner_id': self.id, 'format_invisible': True},
                }

    def _action_whatsapp_confirmed(self, message=None):
        self.ensure_one()
        lang = self.env.context.get('lang')

        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_composition_mode': 'comment',
            'mark_so_as_sent': False,
            'mark_whatsapp_sent': True,
            'custom_layout': False,
            'proforma': self.env.context.get('proforma', False),
            'force_email': False,
            }
        self.with_context(ctx).message_post(attachment_ids=[], body=message, canned_response_ids=[], channel_ids=[], message_type='notification', partner_ids=[], subtype='mail.mt_note')

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):

        res = super(ResPartner, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)
        if self.env.context.get('mark_whatsapp_sent'):
           pass

        return res