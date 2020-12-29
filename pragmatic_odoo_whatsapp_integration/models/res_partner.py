# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # @api.model
    # def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     if (not view_id) and (view_type == 'form') and self._context.get('force_mobile'):
    #         view_id = self.env.ref('pragmatic_odoo_whatsapp_integration.view_partner_simple_form_inherit_mobile_widget').id
    #     res = super(ResPartner, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_type == 'form':
    #         res['arch'] = self._fields_view_get_address(res['arch'])
    #     return res

    def _get_default_whatsapp_recipients(self):
        """ Override of mail.thread method.
            WhatsApp recipients on partners are the partners themselves.
        """
        return self

   


