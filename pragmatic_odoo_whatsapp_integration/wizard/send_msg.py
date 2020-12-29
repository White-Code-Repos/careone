# -*- coding: utf-8 -*-

import logging
import json
import requests
from odoo import api, fields, models, _ , tools
from odoo.exceptions import Warning
from odoo.exceptions import UserError
import base64
import time
import re
import uuid
from odoo.tools import groupby, formataddr
# from whatsparser import WhatsParser



_logger = logging.getLogger(__name__)
try:
    import phonenumbers
    from phonenumbers.phonenumberutil import region_code_for_country_code
    _sms_phonenumbers_lib_imported = True

except ImportError:
    _sms_phonenumbers_lib_imported = False
    _logger.info(
        "The `phonenumbers` Python module is not available. "
        "Phone number validation will be skipped. "
        "Try `pip3 install phonenumbers` to install it."
    )

class ScanWAQRCode(models.TransientModel):
    _name = 'whatsapp.scan.qr'
    _description = 'Scan WhatsApp QR Code'

    def _get_default_image(self):
        Param = self.env['res.config.settings'].sudo().get_values()
        Param_set = self.env['ir.config_parameter'].sudo()
        url = 'https://api.chat-api.com/instance' + Param.get('whatsapp_instance_id') + '/status?token=' + Param.get('whatsapp_token')
        response = requests.get(url)
        json_response = json.loads(response.text)
        if (response.status_code == 201 or response.status_code == 200) and (json_response['accountStatus'] == 'got qr code'):
            # qr_code_image
            # qr_image = base64.b64encode(json_response['qrCode'])
            qr_code_url = 'https://api.chat-api.com/instance' + Param.get('whatsapp_instance_id') + '/qr_code?token=' + Param.get('whatsapp_token')
            response_qr_code = requests.get(qr_code_url)
            # json_data = response_qr_code.json()
            img = base64.b64encode(response_qr_code.content)
            Param_set.set_param("pragmatic_odoo_whatsapp_integration.whatsapp_authenticate", True)
            return img

    qr_code_img_data= fields.Binary(default=_get_default_image)


class SendWAMessageResPartner(models.TransientModel):
    _name = 'whatsapp.msg.res.partner'
    _description = 'Send WhatsApp Message'

    def _default_unique_user(self):
        IPC = self.env['ir.config_parameter'].sudo()
        dbuuid = IPC.get_param('database.uuid')
        return dbuuid + '_' + str(self.env.uid)

    partner_ids = fields.Many2many(
        'res.partner', 'whatsapp_msg_res_partner_res_partner_rel',
        'wizard_id', 'partner_id', 'Recipients')
    message = fields.Text('Message', required=True)
    attachment_ids = fields.Many2many(
        'ir.attachment', 'whatsapp_msg_res_partner_ir_attachments_rel',
        'wizard_id', 'attachment_id', 'Attachments')
    unique_user = fields.Char(default=_default_unique_user)

    def _phone_get_country(self, partner):
        if 'country_id' in partner:
            return partner.country_id
        return self.env.user.company_id.country_id

    def _msg_sanitization(self, partner, field_name):
        number = partner[field_name]
        if number and _sms_phonenumbers_lib_imported:
            country = self._phone_get_country(partner)
            country_code = country.code if country else None
            try:
                phone_nbr = phonenumbers.parse(number, region=country_code, keep_raw_input=True)
            except phonenumbers.phonenumberutil.NumberParseException:
                return number
            if not phonenumbers.is_possible_number(phone_nbr) or not phonenumbers.is_valid_number(phone_nbr):
                return number
            phone_fmt = phonenumbers.PhoneNumberFormat.E164
            return phonenumbers.format_number(phone_nbr, phone_fmt)
        else:
            return number

    def _get_records(self, model):
        if self.env.context.get('active_domain'):
            records = model.search(self.env.context.get('active_domain'))
        elif self.env.context.get('active_ids'):
            records = model.browse(self.env.context.get('active_ids', []))
        else:
            records = model.browse(self.env.context.get('active_id', []))
        return records

    @api.model
    def default_get(self, fields):
        result = super(SendWAMessageResPartner, self).default_get(fields)
        active_model = self.env.context.get('active_model')
        res_id = self.env.context.get('active_id')
        rec = self.env[active_model].browse(res_id)
        Attachment = self.env['ir.attachment']
        res_name = 'Invoice_' + rec.number.replace('/', '_') if active_model == 'account.move' else rec.name.replace('/', '_')
        msg = result.get('message', '')
        result['message'] = msg

        if not self.env.context.get('default_recipients') and active_model and hasattr(self.env[active_model], '_sms_get_default_partners'):
            model = self.env[active_model]
            records = self._get_records(model)
            partners = records._sms_get_default_partners()
            phone_numbers = []
            no_phone_partners = []
            if active_model != 'res.partner':
                is_attachment_exists = Attachment.search([('res_id', '=', res_id), ('name', 'like', res_name + '%'), ('res_model', '=', active_model)], limit=1)
                if not is_attachment_exists:
                    attachments = []
                    if active_model == 'sale.order':
                        template = self.env.ref('sale.email_template_edi_sale')
                    elif active_model == 'account.move':
                        template = self.env.ref('account.email_template_edi_invoice')
                    elif active_model == 'purchase.order':
                        if self.env.context.get('send_rfq', False):
                            template = self.env.ref('purchase.email_template_edi_purchase')
                        else:
                            template = self.env.ref('purchase.email_template_edi_purchase_done')
                    elif active_model == 'stock.picking':
                        template = self.env.ref('stock.mail_template_data_delivery_confirmation')
                    elif active_model == 'account.payment':
                        template = self.env.ref('account.mail_template_data_payment_receipt')

                    report = template.report_template
                    report_service = report.report_name

                    if report.report_type not in ['qweb-html', 'qweb-pdf']:
                        raise UserError(_('Unsupported report type %s found.') % report.report_type)
                    res, format = report.render_qweb_pdf([res_id])
                    res = base64.b64encode(res)
                    if not res_name:
                        res_name = 'report.' + report_service
                    ext = "." + format
                    if not res_name.endswith(ext):
                        res_name += ext
                    attachments.append((res_name, res))
                    attachment_ids = []
                    for attachment in attachments:
                        attachment_data = {
                            'name': attachment[0],
                            'datas': attachment[1],
                            'type': 'binary',
                            'res_model': active_model,
                            'res_id': res_id,
                        }
                        attachment_ids.append(Attachment.create(attachment_data).id)
                    if attachment_ids:
                        result['attachment_ids'] = [(6, 0, attachment_ids)]
                else:
                    result['attachment_ids'] = [(6, 0, [is_attachment_exists.id])]

            for partner in partners:
                number = self._msg_sanitization(partner, self.env.context.get('field_name') or 'mobile')
                if number:
                    phone_numbers.append(number)
                else:
                    no_phone_partners.append(partner.name)
            if len(partners) > 1:
                if no_phone_partners:
                    raise UserError(_('Missing mobile number for %s.') % ', '.join(no_phone_partners))
            result['partner_ids'] = [(6, 0, partners.ids)]

            result['message'] = msg

        return result

    def action_send_msg_res_partner(self):
        Param = self.env['res.config.settings'].sudo().get_values()
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')


        status_url = 'https://api.chat-api.com/instance'+Param.get('whatsapp_instance_id')+'/status?token='+Param.get('whatsapp_token')
        status_response = requests.get(status_url)
        json_response_status = json.loads(status_response.text)
        if (status_response.status_code == 200 or status_response.status_code == 201) and json_response_status['accountStatus'] == 'authenticated':
            if active_model == 'res.partner':
                for res_partner_id in self.partner_ids:

                    # res_partner_id = self.env['res.partner'].search([('id', '=', active_id)])

                    number = str(res_partner_id.country_id.phone_code) + res_partner_id.mobile
                    if res_partner_id.country_id.phone_code and res_partner_id.mobile:
                        whatsapp_number = res_partner_id.mobile
                        whatsapp_msg_number_without_space = whatsapp_number.replace(" ", "")
                        whatsapp_msg_number_without_code = whatsapp_msg_number_without_space.replace('+' + str(res_partner_id.country_id.phone_code), "")
                        url = 'https://api.chat-api.com/instance'+Param.get('whatsapp_instance_id')+'/sendMessage?token='+Param.get('whatsapp_token')
                        headers = {
                            "Content-Type": "application/json",
                        }
                        tmp_dict  = {
                            "phone": "+"+str(res_partner_id.country_id.phone_code)+""+ whatsapp_msg_number_without_code,
                            "body": self.message}
                        response = requests.post(url, json.dumps(tmp_dict), headers=headers)

                        if response.status_code == 201 or response.status_code == 200:
                            _logger.info("\nSend Message successfully")
                        if self.attachment_ids:
                            for attachment in self.attachment_ids:
                                with open("/tmp/" + attachment.name, 'wb') as tmp:
                                    # tmp.write(base64.decodebytes(attachment.datas))

                                    # encoded_string = base64.b64encode(attachment.datas_fname.read())

                                    encoded_file = str(attachment.datas)
                                    url_send_file = 'https://api.chat-api.com/instance' + Param.get('whatsapp_instance_id') + '/sendFile?token=' + Param.get('whatsapp_token')
                                    headers_send_file = {
                                        "Content-Type": "application/json",
                                    }
                                    dict_send_file = {
                                        "phone": "+"+str(res_partner_id.country_id.phone_code)+""+ whatsapp_msg_number_without_code,
                                        "body": "data:"+attachment.mimetype+";base64," + encoded_file[2:-1],
                                        "filename": attachment.name
                                    }

                                    response_send_file = requests.post(url_send_file, json.dumps(dict_send_file), headers=headers_send_file)

                                    if response_send_file.status_code == 201 or response_send_file.status_code == 200:
                                        _logger.info("\nSend file attachment successfully11")

                    else:
                        raise Warning('Please enter %s mobile number or select country', res_partner_id)
        else:
            raise Warning('Please authorize your mobile number with chat api')



class SendWAMessageSendResPartner(models.TransientModel):
    _name = 'whatsapp.msg.send.partner'
    _description = 'Send WhatsApp Message'

    def _default_unique_user(self):
        IPC = self.env['ir.config_parameter'].sudo()
        dbuuid = IPC.get_param('database.uuid')
        return dbuuid + '_' + str(self.env.uid)

    partner_ids = fields.Many2many(
        'res.partner', 'whatsapp_msg_send_partner_res_partner_rel',
        'wizard_id', 'partner_id', 'Recipients')
    message = fields.Text('Message', required=True)
    attachment_ids = fields.Many2many(
        'ir.attachment', 'whatsapp_msg_send_partner_ir_attachments_rel',
        'wizard_id', 'attachment_id', 'Attachments')
    unique_user = fields.Char(default=_default_unique_user)

    def _phone_get_country(self, partner):
        if 'country_id' in partner:
            return partner.country_id
        return self.env.user.company_id.country_id

    def _msg_sanitization(self, partner, field_name):
        number = partner[field_name]
        if number and _sms_phonenumbers_lib_imported:
            country = self._phone_get_country(partner)
            country_code = country.code if country else None
            try:
                phone_nbr = phonenumbers.parse(number, region=country_code, keep_raw_input=True)
            except phonenumbers.phonenumberutil.NumberParseException:
                return number
            if not phonenumbers.is_possible_number(phone_nbr) or not phonenumbers.is_valid_number(phone_nbr):
                return number
            phone_fmt = phonenumbers.PhoneNumberFormat.E164
            return phonenumbers.format_number(phone_nbr, phone_fmt)
        else:
            return number

    def _get_records(self, model):
        if self.env.context.get('active_domain'):
            records = model.search(self.env.context.get('active_domain'))
        elif self.env.context.get('active_ids'):
            records = model.browse(self.env.context.get('active_ids', []))
        else:
            records = model.browse(self.env.context.get('active_id', []))
        return records

    @api.model
    def default_get(self, fields):
        result = super(SendWAMessageSendResPartner, self).default_get(fields)
        active_model = self.env.context.get('active_model')
        # active_model = 'res.partner'
        res_id = self.env.context.get('active_id')
        if res_id:

            rec = self.env[active_model].browse(res_id)
            Attachment = self.env['ir.attachment']
            res_name = 'Invoice_' + rec.number.replace('/', '_') if active_model == 'account.move' else rec.name.replace('/', '_')
            msg = result.get('message', '')
            result['message'] = msg

            if not self.env.context.get('default_recipients') and active_model and hasattr(self.env[active_model], '_sms_get_default_partners'):
                model = self.env[active_model]
                records = self._get_records(model)
                partners = records._sms_get_default_partners()
                phone_numbers = []
                no_phone_partners = []
                if active_model != 'res.partner':
                    is_attachment_exists = Attachment.search([('res_id', '=', res_id), ('name', 'like', res_name + '%'), ('res_model', '=', active_model)], limit=1)
                    if not is_attachment_exists:
                        attachments = []
                        if active_model == 'sale.order':
                            template = self.env.ref('sale.email_template_edi_sale')
                        elif active_model == 'account.move':
                            template = self.env.ref('account.email_template_edi_invoice')
                        elif active_model == 'purchase.order':
                            if self.env.context.get('send_rfq', False):
                                template = self.env.ref('purchase.email_template_edi_purchase')
                            else:
                                template = self.env.ref('purchase.email_template_edi_purchase_done')
                        elif active_model == 'stock.picking':
                            template = self.env.ref('stock.mail_template_data_delivery_confirmation')
                        elif active_model == 'account.payment':
                            template = self.env.ref('account.mail_template_data_payment_receipt')

                        report = template.report_template
                        report_service = report.report_name

                        if report.report_type not in ['qweb-html', 'qweb-pdf']:
                            raise UserError(_('Unsupported report type %s found.') % report.report_type)
                        res, format = report.render_qweb_pdf([res_id])
                        res = base64.b64encode(res)
                        if not res_name:
                            res_name = 'report.' + report_service
                        ext = "." + format
                        if not res_name.endswith(ext):
                            res_name += ext
                        attachments.append((res_name, res))
                        attachment_ids = []
                        for attachment in attachments:
                            attachment_data = {
                                'name': attachment[0],
                                'datas': attachment[1],
                                'type': 'binary',
                                'res_model': active_model,
                                'res_id': res_id,
                            }
                            attachment_ids.append(Attachment.create(attachment_data).id)
                        if attachment_ids:
                            result['attachment_ids'] = [(6, 0, attachment_ids)]
                    else:
                        result['attachment_ids'] = [(6, 0, [is_attachment_exists.id])]

                for partner in partners:
                    number = self._msg_sanitization(partner, self.env.context.get('field_name') or 'mobile')
                    if number:
                        phone_numbers.append(number)
                    else:
                        no_phone_partners.append(partner.name)
                if len(partners) > 1:
                    if no_phone_partners:
                        raise UserError(_('Missing mobile number for %s.') % ', '.join(no_phone_partners))
                result['partner_ids'] = [(6, 0, partners.ids)]

                result['message'] = msg

        return result

    def action_send_msg_res_partner(self):
        Param = self.env['res.config.settings'].sudo().get_values()
        active_id = self.partner_ids
        active_model = 'res.partner'

        status_url = 'https://api.chat-api.com/instance'+Param.get('whatsapp_instance_id')+'/status?token='+Param.get('whatsapp_token')
        status_response = requests.get(status_url)
        json_response_status = json.loads(status_response.text)
        if (status_response.status_code == 200 or status_response.status_code == 201) and json_response_status['accountStatus'] == 'authenticated':
            if active_model == 'res.partner':
                for res_partner_id in self.partner_ids:

                    # res_partner_id = self.env['res.partner'].search([('id', '=', active_id)])

                    number = str(res_partner_id.country_id.phone_code) + res_partner_id.mobile
                    if res_partner_id.country_id.phone_code and res_partner_id.mobile:
                        whatsapp_number = res_partner_id.mobile
                        whatsapp_msg_number_without_space = whatsapp_number.replace(" ", "")
                        whatsapp_msg_number_without_code = whatsapp_msg_number_without_space.replace('+' + str(res_partner_id.country_id.phone_code), "")
                        url = 'https://api.chat-api.com/instance'+Param.get('whatsapp_instance_id')+'/sendMessage?token='+Param.get('whatsapp_token')
                        headers = {
                            "Content-Type": "application/json",
                        }
                        tmp_dict  = {
                            "phone": "+"+str(res_partner_id.country_id.phone_code)+""+whatsapp_msg_number_without_code,
                            "body": self.message}
                        response = requests.post(url, json.dumps(tmp_dict), headers=headers)

                        if response.status_code == 201 or response.status_code == 200:
                            _logger.info("\nSend Message successfully")
                        if self.attachment_ids:
                            for attachment in self.attachment_ids:
                                with open("/tmp/" + attachment.name, 'wb') as tmp:
                                    # tmp.write(base64.decodebytes(attachment.datas))

                                    # encoded_string = base64.b64encode(attachment.datas_fname.read())

                                    encoded_file = str(attachment.datas)
                                    url_send_file = 'https://api.chat-api.com/instance' + Param.get('whatsapp_instance_id') + '/sendFile?token=' + Param.get('whatsapp_token')
                                    headers_send_file = {
                                        "Content-Type": "application/json",
                                    }
                                    dict_send_file = {
                                        "phone": "+"+str(res_partner_id.country_id.phone_code)+""+whatsapp_msg_number_without_code,
                                        "body": "data:"+attachment.mimetype+";base64," + encoded_file[2:-1],
                                        "filename": attachment.name
                                    }

                                    response_send_file = requests.post(url_send_file, json.dumps(dict_send_file), headers=headers_send_file)

                                    if response_send_file.status_code == 201 or response_send_file.status_code == 200:
                                        _logger.info("\nSend file attachment successfully11")

                    else:
                        raise Warning('Please enter %s mobile number or select country', res_partner_id)
        else:
            raise Warning('Please authorize your mobile number with chat api')



class SendWAMessage(models.TransientModel):
    _name = 'whatsapp.msg'
    _description = 'Send WhatsApp Message'
    _inherit =  ['mail.thread', 'mail.activity.mixin']

    def _default_unique_user(self):
        IPC = self.env['ir.config_parameter'].sudo()
        dbuuid = IPC.get_param('database.uuid')
        return dbuuid + '_' + str(self.env.uid)

    partner_ids = fields.Many2many(
        'res.partner', 'whatsapp_msg_res_partner_rel',
        'wizard_id', 'partner_id', 'Recipients')
    message = fields.Text('Message', required=True)
    attachment_ids = fields.Many2many(
        'ir.attachment', 'whatsapp_msg_ir_attachments_rel',
        'wizard_id', 'attachment_id', 'Attachments', tracking=True)
    unique_user = fields.Char(default=_default_unique_user)

    def format_amount(self, amount, currency):
        fmt = "%.{0}f".format(currency.decimal_places)
        lang = self.env['res.lang']._lang_get(self.env.context.get('lang') or 'en_US')

        formatted_amount = lang.format(fmt, currency.round(amount), grouping=True, monetary=True)\
            .replace(r' ', u'\N{NO-BREAK SPACE}').replace(r'-', u'-\N{ZERO WIDTH NO-BREAK SPACE}')

        pre = post = u''
        if currency.position == 'before':
            pre = u'{symbol}\N{NO-BREAK SPACE}'.format(symbol=currency.symbol or '')
        else:
            post = u'\N{NO-BREAK SPACE}{symbol}'.format(symbol=currency.symbol or '')

        return u'{pre}{0}{post}'.format(formatted_amount, pre=pre, post=post)

    def _phone_get_country(self, partner):
        if 'country_id' in partner:
            return partner.country_id
        return self.env.user.company_id.country_id

    def _msg_sanitization(self, partner, field_name):
        number = partner[field_name]
        if number and _sms_phonenumbers_lib_imported:
            country = self._phone_get_country(partner)
            country_code = country.code if country else None
            try:
                phone_nbr = phonenumbers.parse(number, region=country_code, keep_raw_input=True)
            except phonenumbers.phonenumberutil.NumberParseException:
                return number
            if not phonenumbers.is_possible_number(phone_nbr) or not phonenumbers.is_valid_number(phone_nbr):
                return number
            phone_fmt = phonenumbers.PhoneNumberFormat.E164
            return phonenumbers.format_number(phone_nbr, phone_fmt)
        else:
            return number

    def _get_records(self, model):
        if self.env.context.get('active_domain'):
            records = model.search(self.env.context.get('active_domain'))
        elif self.env.context.get('active_ids'):
            records = model.browse(self.env.context.get('active_ids', []))
        else:
            records = model.browse(self.env.context.get('active_id', []))
        return records

    def cleanhtml(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext



    @api.model
    def default_get(self, fields):
        result = super(SendWAMessage, self).default_get(fields)
        active_model = self.env.context.get('active_model')
        res_id = self.env.context.get('active_id')
        rec = self.env[active_model].browse(res_id)
        Attachment = self.env['ir.attachment']
        # res_name = 'Invoice_' + rec.number.replace('/', '_') if active_model == 'account.move' else rec.name.replace('/', '_')
        res_name = ''
        # if rec.number and rec.name:
        if active_model == 'account.move':
            if rec.name:
                # if rec.name and rec.number:

                res_name = 'Invoice_' + rec.name.replace('/', '_') if active_model == 'account.move' else rec.name.replace('/', '_')

        msg = result.get('message', '')
        result['message'] = msg

        # print("\n\nself.env.context.get('default_recipients'): ", self.env.context.get('default_recipients'))
        # print("\n\nself.env.context: ", self.env.context)


        res_user_id = self.env['res.users'].search([('partner_id', '=' , rec.partner_id.id)])
        if not self.env.context.get('default_recipients') and active_model and hasattr(self.env[active_model], '_sms_get_default_partners'):
            model = self.env[active_model]
            records = self._get_records(model)
            partners = records._sms_get_default_partners()
            phone_numbers = []
            no_phone_partners = []
            if active_model != 'res.partner':
                # if not self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_send_report_url_in_message')\
                #         or not self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_purchase_send_report_url_in_message')\
                #         or not self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_stock_send_report_url_in_message')\
                #         or not self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_invoice_send_report_url_in_message'):

                is_attachment_exists = Attachment.search([('res_id', '=', res_id), ('name', 'like', res_name + '%'), ('res_model', '=', active_model)], limit=1)
                if not is_attachment_exists:
                    attachments = []
                    if active_model == 'sale.order':
                        template = self.env.ref('sale.email_template_edi_sale')
                    elif active_model == 'account.move':
                        template = self.env.ref('account.email_template_edi_invoice')
                    elif active_model == 'purchase.order':
                        if self.env.context.get('send_rfq', False):
                            template = self.env.ref('purchase.email_template_edi_purchase')
                        else:
                            template = self.env.ref('purchase.email_template_edi_purchase_done')
                    elif active_model == 'stock.picking':
                        template = self.env.ref('stock.mail_template_data_delivery_confirmation')
                    elif active_model == 'account.payment':
                        template = self.env.ref('account.mail_template_data_payment_receipt')
                    # else:


                    report = template.report_template
                    report_service = report.report_name

                    if report.report_type not in ['qweb-html', 'qweb-pdf']:
                        raise UserError(_('Unsupported report type %s found.') % report.report_type)
                    res, format = report.render_qweb_pdf([res_id])
                    res = base64.b64encode(res)
                    if not res_name:
                        res_name = 'report.' + report_service
                    ext = "." + format
                    if not res_name.endswith(ext):
                        res_name += ext
                    attachments.append((res_name, res))
                    attachment_ids = []
                    for attachment in attachments:
                        attachment_data = {
                            'name': attachment[0],
                            'datas': attachment[1],
                            'type': 'binary',
                            'res_model': active_model,
                            'res_id': res_id,
                        }
                        attachment_ids.append(Attachment.create(attachment_data).id)
                    if attachment_ids:
                        result['attachment_ids'] = [(6, 0, attachment_ids)]
                else:
                    result['attachment_ids'] = [(6, 0, [is_attachment_exists.id])]
                # else:
                #     if active_model == 'sale.order':
                #         order_id = self.env['sale.order'].search([('id', '=', rec.id)])
                #         url = 'http://192.168.1.100:8014/mail/view?model=sale.order&res_id='+str(order_id.id)+'&access_token='+str(uuid.uuid4())
            if active_model == 'sale.order':
                if rec.partner_id.mobile and rec.partner_id.country_id.phone_code:
                    # doc_name = 'quotation' if rec.state in ('approved', 'to_confirm') else 'order'
                    doc_name = 'quotation'
                    res_user_id = self.env['res.users'].search([('id', '=', self.env.user.id)])
                    msg = "Hello " + rec.partner_id.name
                    if rec.partner_id.parent_id:
                        msg += "(" + rec.partner_id.parent_id.name + ")"
                    if self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_order_info_msg'):
                        msg += "\n\nYour "
                        if self.env.context.get('proforma'):
                            msg += "in attachment your pro-forma invoice"
                        else:
                            msg += doc_name + " *" + rec.name + "* "
                        if rec.origin:
                            msg += "(with reference: " + rec.origin + ")"
                        msg += " with Total Amount " + self.format_amount(rec.amount_total, rec.pricelist_id.currency_id) + "."
                    if self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_order_product_details_msg'):
                        msg +="\n\nFollowing is your order details."
                        for line_id in rec.order_line:
                            msg += "\n\n*Product:* "+line_id.product_id.name+"\n*Qty:* "+str(line_id.product_uom_qty)+" "+str(line_id.product_uom.name)+"\n*Unit Price:* "+str(
                                line_id.price_unit)+"\n*Subtotal:* "+str(line_id.price_subtotal)
                            msg+="\n------------------"
                    msg += "\n Please find attached document which will help you to get detailed information."
                    # if rec
                    if res_user_id.has_group('pragmatic_odoo_whatsapp_integration.group_enable_signature'):
                        user_signature = self.cleanhtml(res_user_id.signature)
                        msg += "\n\n"+user_signature
                else:
                    raise Warning('Please enter mobile number or select country')
            # result['message'] = msg

            if active_model == 'account.move':
                if rec.partner_id.mobile and rec.partner_id.country_id.phone_code:
                    # doc_name = 'invoice' if rec.state in ('open', 'paid') else 'invoice'
                    doc_name = 'invoice'
                    res_user_id = self.env['res.users'].search([('id', '=', self.env.user.id)])
                    msg = "Hello " + rec.partner_id.name
                    if rec.partner_id.parent_id:
                        msg += "(" + rec.partner_id.parent_id.name + ")"
                    if self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_invoice_info_msg'):
                        msg += "\n\nYour "
                        # if self.env.context.get('proforma'):
                        #     msg += "in attachment your pro-forma invoice"
                        # else:
                        if res_name:
                            msg += doc_name + " *" + res_name + "* "
                        else:
                            msg += doc_name + " *" + "draft invoice"  + "* "

                        # if rec.origin:
                        #     msg += "(with reference: " + rec.origin + ")"
                        msg += " with Total Amount " + self.format_amount(rec.amount_total, rec.currency_id) + "."
                    if self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_invoice_product_details_msg'):
                        msg += "\n\nFollowing is your order details."
                        for line_id in rec.invoice_line_ids:
                            msg += "\n\n*Product:* "+line_id.product_id.name+"\n*Qty:* "+str(line_id.quantity)+"\n*Unit Price:* "+str(
                                line_id.price_unit)+"\n*Subtotal:* "+str(line_id.price_subtotal)
                            msg+="\n------------------"

                    msg += "\n Please find attached document which will help you to get detailed information."
                    if res_user_id.has_group('pragmatic_odoo_whatsapp_integration.group_invoice_enable_signature'):
                        user_signature = self.cleanhtml(res_user_id.signature)
                        msg += "\n\n" + user_signature
                else:
                    raise Warning('Please enter mobile number or select country')

            if active_model == 'stock.picking':
                if rec.partner_id.mobile and rec.partner_id.country_id.phone_code:
                    # doc_name = 'stock picking' if rec.state in ('assigned', 'done') else 'picking'
                    doc_name = 'stock picking'
                    res_user_id = self.env['res.users'].search([('id', '=', self.env.user.id)])
                    msg = "Hello " + rec.partner_id.name
                    if rec.partner_id.parent_id:
                        msg += "(" + rec.partner_id.parent_id.name + ")"
                    if self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_stock_info_msg'):
                        msg += "\n\nYour "
                        # if self.env.context.get('proforma'):
                        #     msg += "in attachment your pro-forma invoice"
                        # else:

                        msg += doc_name + " *" + rec.name + "* "
                        if rec.origin:
                            msg += "(with reference: " + rec.origin + ")"
                    if self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_stock_product_details_msg'):
                        msg += "\n\nFollowing is your delivery order details."

                        for line_id in rec.move_ids_without_package:
                            msg += "\n\n*Product:* "+line_id.product_id.name+"\n*Qty:* "+str(line_id.product_uom_qty)+" "+str(line_id.product_uom.name)+"\n*Done:* "+str(
                                line_id.quantity_done)
                            msg+="\n------------------"
                    # msg += " Initial Demand " + self.format_amount(rec.amount_total, rec.currency_id) + "*."
                    msg += "\n Please find attached document which will help you to get detailed information."
                    if res_user_id.has_group('pragmatic_odoo_whatsapp_integration.group_stock_enable_signature'):
                        user_signature = self.cleanhtml(res_user_id.signature)
                        msg += "\n\n" + user_signature
                else:
                    raise Warning('Please enter mobile number or select country')

            if active_model == 'purchase.order':
                if rec.partner_id.mobile and rec.partner_id.country_id.phone_code:
                    # doc_name = 'purchase order' if rec.state in ('sent','to approve','purchase','done') else 'purchase order'
                    doc_name = 'purchase order'
                    res_user_id = self.env['res.users'].search([('id', '=', self.env.user.id)])
                    msg = "Hello " + rec.partner_id.name
                    if rec.partner_id.parent_id:
                        msg += "(" + rec.partner_id.parent_id.name + ")"
                    if self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_purchase_order_info_msg'):
                        msg += "\n\nYour "
                        # if self.env.context.get('proforma'):
                        #     msg += "in attachment your pro-forma invoice"
                        # else:
                        msg += doc_name + " *" + rec.name + "* "
                        if rec.origin:
                            msg += "(with reference: " + rec.origin + ")"
                        msg += " with Total Amount " + self.format_amount(rec.amount_total, rec.currency_id) + "."
                    if self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_purchase_order_product_details_msg'):
                        msg += "\n\nFollowing is your order details."
                        for line_id in rec.order_line:
                            msg += "\n\n*Product:* "+line_id.product_id.name+"\n*Qty:* "+str(line_id.product_qty)+" "+str(line_id.product_uom.name)+"\n*Unit Price:* "+str(
                                line_id.price_unit)+"\n*Subtotal:* "+str(line_id.price_subtotal)
                            msg+="\n------------------"
                    msg += "\n Please find attached document which will help you to get detailed information."
                    if res_user_id.has_group('pragmatic_odoo_whatsapp_integration.group_purchase_enable_signature'):
                        user_signature = self.cleanhtml(res_user_id.signature)
                        msg += "\n\n" + user_signature
                else:
                    raise Warning('Please enter mobile number or select country')

            if active_model == 'account.payment':
                if rec.partner_id.mobile and rec.partner_id.country_id.phone_code:
                    # doc_name = 'purchase order' if rec.state in ('sent','to approve','purchase','done') else 'purchase order'
                    doc_name = 'account payment'
                    res_user_id = self.env['res.users'].search([('id', '=', self.env.user.id)])
                    msg = "Hello " + rec.partner_id.name
                    if rec.partner_id.parent_id:
                        msg += "(" + rec.partner_id.parent_id.name + ")"
                    if self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_invoice_info_msg'):
                        msg += "\n\nYour "
                        # if self.env.context.get('proforma'):
                        #     msg += "in attachment your pro-forma invoice"
                        # else:
                        if rec.name:
                            msg += doc_name + " *" + rec.name + "* "
                            # if rec.origin:
                            #     msg += "(with reference: " + rec.origin + ")"
                        else:
                            msg += doc_name + " *" + "Draft Payment" + "* "

                        msg += " with Total Amount " + self.format_amount(rec.amount, rec.currency_id) + "."
                    if self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_invoice_product_details_msg'):
                        msg += "\n\nFollowing is your payment details."
                        # for line_id in rec.order_line:
                        msg += "\n\n*Payment Type:* " + rec.payment_type + "\n*Payment Journal:* " + rec.journal_id.name + "\n*Payment date:* " + str(
                            rec.payment_date) + "\n*Memo:* " + str(rec.communication)
                    msg += "\n Please find attached document which will help you to get detailed information."
                    if res_user_id.has_group('pragmatic_odoo_whatsapp_integration.group_invoice_enable_signature'):
                        user_signature = self.cleanhtml(res_user_id.signature)
                        msg += "\n\n" + user_signature
                else:
                    raise Warning('Please enter mobile number or select country')

            result['message'] = msg

            for partner in partners:
                number = self._msg_sanitization(partner, self.env.context.get('field_name') or 'mobile')
                if number:
                    phone_numbers.append(number)
                else:
                    no_phone_partners.append(partner.name)
            if len(partners) > 1:
                if no_phone_partners:
                    raise UserError(_('Missing mobile number for %s.') % ', '.join(no_phone_partners))
            result['partner_ids'] = [(6, 0, partners.ids)]

            result['message'] = msg

        return result

    def convert_to_html(self, message):
        str1 = '**Hello Welcome In *india*'
        for data in re.findall(r'\*.*?\*', message):
            message = message.replace(data, "<strong>" + data.strip('*') + "</strong>")
        return message


    def action_send_msg(self):
        Param = self.env['res.config.settings'].sudo().get_values()
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')


        status_url = 'https://api.chat-api.com/instance'+Param.get('whatsapp_instance_id')+'/status?token='+Param.get('whatsapp_token')
        status_response = requests.get(status_url)
        json_response_status = json.loads(status_response.text)
        if (status_response.status_code == 200 or status_response.status_code == 201) and json_response_status['accountStatus'] == 'authenticated':
            if active_model == 'res.partner':
                for res_partner_id in self.partner_ids:


                    # res_partner_id = self.env['res.partner'].search([('id', '=', active_id)])
                    whatsapp_number = res_partner_id.mobile
                    whatsapp_msg_number_without_space = whatsapp_number.replace(" ", "")
                    whatsapp_msg_number_without_code = whatsapp_msg_number_without_space.replace('+' + str(res_partner_id.country_id.phone_code), "")
                    number = str(res_partner_id.country_id.phone_code) + res_partner_id.mobile
                    if res_partner_id.country_id.phone_code and res_partner_id.mobile:
                        url = 'https://api.chat-api.com/instance'+Param.get('whatsapp_instance_id')+'/sendMessage?token='+Param.get('whatsapp_token')
                        headers = {
                            "Content-Type": "application/json",
                        }
                        tmp_dict  = {
                            "phone": "+"+str(res_partner_id.country_id.phone_code)+""+whatsapp_msg_number_without_code,
                            "body": self.message}
                        response = requests.post(url, json.dumps(tmp_dict), headers=headers)


                        if response.status_code == 201 or response.status_code == 200:
                            _logger.info("\nSend Message successfully")
                # else:
                #     view_id = self.env.ref('pragmatic_odoo_whatsapp_integration.whatsapp_retry_msg_view_form').id
                #     context = dict(self.env.context or {})
                #     context.update(wiz_id=self.id)
                #     return {
                #         'name': _("Retry to send"),
                #         'view_mode': 'form',
                #         'view_id': "view_partner_simple_form_inherit_mobile_widget",
                #         'view_type': 'form',
                #         'res_model': 'res.partner',
                #         'type': 'ir.actions.act_window',
                #         'target': 'new',
                #         'context': context,
                #     }
            elif active_model == 'sale.order' or active_model == 'account.move' or active_model == 'purchase.order' or active_model == 'stock.picking' or active_model == \
                    'account.payment':
                # sale_order_id = self.env['sale.order'].search([('id', '=', active_id)])
                rec = self.env[active_model].browse(active_id)
                # res_user_id = self.env['res.users'].search([('partner_id', '=', rec.partner_id )])
                number = str(rec.partner_id.country_id.phone_code) + rec.partner_id.mobile
                if rec.partner_id.country_id.phone_code and rec.partner_id.mobile:
                    url = 'https://api.chat-api.com/instance' + Param.get('whatsapp_instance_id') + '/sendMessage?token=' + Param.get('whatsapp_token')
                    headers = {
                        "Content-Type": "application/json",
                    }

                    whatsapp_msg_number = rec.partner_id.mobile
                    whatsapp_msg_number_without_space = whatsapp_msg_number.replace(" ", "");
                    whatsapp_msg_number_without_code=whatsapp_msg_number_without_space.replace('+' + str(rec.partner_id.country_id.phone_code),"")
                    tmp_dict = {
                        "phone": "+" + str(rec.partner_id.country_id.phone_code)+""+ whatsapp_msg_number_without_code,
                        "body": self.message}
                    response = requests.post(url, json.dumps(tmp_dict), headers=headers)

                    if response.status_code == 201 or response.status_code == 200:
                        _logger.info("\nSend Message successfully")

                    if self.attachment_ids:
                        for attachment in self.attachment_ids:
                            with open("/tmp/" + attachment.name, 'wb') as tmp:
                                # tmp.write(base64.decodebytes(attachment.datas))

                                # encoded_string = base64.b64encode(attachment.datas_fname.read())

                                encoded_file = str(attachment.datas)
                                url_send_file = 'https://api.chat-api.com/instance' + Param.get('whatsapp_instance_id') + '/sendFile?token=' + Param.get('whatsapp_token')
                                headers_send_file = {
                                    "Content-Type": "application/json",
                                }

                                whatsapp_msg_number = rec.partner_id.mobile
                                whatsapp_msg_number_without_space = whatsapp_msg_number.replace(" ", "");
                                whatsapp_msg_number_without_code = whatsapp_msg_number_without_space.replace('+' + str(rec.partner_id.country_id.phone_code), "")

                                dict_send_file = {
                                    "phone": "+" + str(rec.partner_id.country_id.phone_code) + "" + whatsapp_msg_number_without_code,
                                    # "body": "data:application/pdf;base64,"+encoded_file[2:-1],
                                    "body": "data:" + attachment.mimetype + ";base64," + encoded_file[2:-1],
                                    "filename": attachment.name
                                }
                                response_send_file = requests.post(url_send_file, json.dumps(dict_send_file), headers=headers_send_file)

                                if response_send_file.status_code == 201 or response_send_file.status_code == 200:
                                    _logger.info("\nSend file attachment successfully")
                                    mail_message_obj = self.env['mail.message']
                                    if self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_display_chatter_message')\
                                            or self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_purchase_display_chatter_message')\
                                        or self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_stock_display_chatter_message')\
                                        or self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_invoice_display_chatter_message'):

                                        # body_html = tools.append_content_to_html('<div>%s</div>' % self.message)
                                        comment = "fa fa-whatsapp"
                                        body_html = tools.append_content_to_html('<div class = "%s"></div>' % tools.ustr(comment), self.message)
                                        update_msg = self.convert_to_html(body_html)
                                        # update_msg = WhatsParser(body_html)
                                        rec.message_main_attachment_id = attachment.id
                                        rec.access_token = str(uuid.uuid4())
                                        mail_message_id = mail_message_obj.sudo().create({
                                            'res_id': rec.id,
                                            'model' : active_model,
                                            'body': update_msg
                                        })
                                        mail_values = {
                                            'mail_message_id': mail_message_id.id,
                                            'attachment_ids': [(4, attachment.id) for attachment in self.attachment_ids],
                                        }
                                        mail = self.env['mail.mail'].create(mail_values)
                                        mail_message_id.message_format()

                else:
                    
                    raise Warning('Please enter %s mobile number or select country',rec.partner_id)
        else:
            raise Warning('Please authorize your mobile number with chat api')

class RetryWAMsg(models.TransientModel):
    _name = 'whatsapp.retry.msg'
    _description = 'Retry WhatsApp Message'

    name = fields.Char()

    def action_retry_send_msg(self):
        res_id = self.env.context.get('wiz_id')
        if res_id:
            time.sleep(5)
            self.env['whatsapp.msg.res.partner'].browse(res_id).action_send_msg()
        return True