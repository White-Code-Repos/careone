# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
import requests
import json
from odoo.exceptions import Warning
from datetime import date
from odoo.http import request
from datetime import timezone, timedelta
import datetime

_logger = logging.getLogger(__name__)


class accountInvoice(models.Model):
    _inherit = 'account.move'

    def _payment_remainder_send_message(self):
        account_invoice_ids = self.env['account.move'].search([('state', 'in', ['draft','posted']),('invoice_date_due', '<', datetime.datetime.now())])
        Param = self.env['res.config.settings'].sudo().get_values()

        for account_invoice_id in account_invoice_ids:
            if account_invoice_id.partner_id.country_id.phone_code and account_invoice_id.partner_id.mobile:
                msg = "Hello "+account_invoice_id.partner_id.name+"\nYour invoice is pending"
                whatsapp_msg_number = account_invoice_id.partner_id.mobile
                whatsapp_msg_number_without_space = whatsapp_msg_number.replace(" ", "")
                whatsapp_msg_number_without_code = whatsapp_msg_number_without_space.replace('+' + str(account_invoice_id.partner_id.country_id.phone_code), "")
                url = 'https://api.chat-api.com/instance' + Param.get('whatsapp_instance_id') + '/sendMessage?token=' + Param.get('whatsapp_token')
                headers = {
                    "Content-Type": "application/json",
                }
                a= "+" + str(account_invoice_id.partner_id.country_id.phone_code) + "" + whatsapp_msg_number_without_code
                tmp_dict = {
                    "phone": a,
                    "body": msg
                }
                response = requests.post(url, json.dumps(tmp_dict), headers=headers)

                if response.status_code == 201 or response.status_code == 200:
                    _logger.info("\nSend Message successfully")

                    # if response.status_code == 201 or response.status_code == 200:
                    #     _logger.info("\nSend Message successfully")

                    mail_message_obj = self.env['mail.message']
                    mail_message_id = mail_message_obj.sudo().create({
                        'res_id': account_invoice_id.id,
                        'model': 'account.move',
                        'body': msg,
                    })


