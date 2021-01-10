# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.addons.iap.models import iap
import requests

DEFAULT_ENDPOINT = 'https://iap-sms.odoo.com'

class SmsApi(models.AbstractModel):
    _inherit = 'sms.api'
    _description = 'SMS API'

    @api.model
    def _contact_iap(self, local_endpoint, params):

        service = self.env['sms.integration'].search([('state', '=', True)])

        dict = {}
        for line in service.attr_ids:
            dict[line.name] = line.value

        for parm in params['messages']:

            req = dict['url'] + dict['end-point'] + "username=" + dict['username'] + "&password=" + dict['password'] + "&unicode=" + dict['unicode'] + "&sender=" + dict['sender'] + "&message=" + parm['content'] + "&numbers=" + parm['number'] + "&retrun=string"

            response = requests.get(req)

        return iap.jsonrpc(endpoint + local_endpoint, params=params)

    @api.model
    def _send_sms(self, numbers, message):
        """ Send a single message to several numbers

        :param numbers: list of E164 formatted phone numbers
        :param message: content to send

        :raises ? TDE FIXME
        """
        params = {
            'numbers': numbers,
            'message': message,
        }
        return self._contact_iap('/iap/message_send', params)

    @api.model
    def _send_sms_batch(self, messages):
        """ Send SMS using IAP in batch mode

        :param messages: list of SMS to send, structured as dict [{
            'res_id':  integer: ID of sms.sms,
            'number':  string: E164 formatted phone number,
            'content': string: content to send
        }]

        :return: return of /iap/sms/1/send controller which is a list of dict [{
            'res_id': integer: ID of sms.sms,
            'state':  string: 'insufficient_credit' or 'wrong_number_format' or 'success',
            'credit': integer: number of credits spent to send this SMS,
        }]

        :raises: normally none
        """
        params = {
            'messages': messages
        }
        return self._contact_iap('/iap/sms/1/send', params)
