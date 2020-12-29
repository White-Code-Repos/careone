import time
from io import BytesIO
import logging
_logger = logging.getLogger(__name__)


from odoo import api, fields, models, _
import requests
import base64
import json



class base(models.TransientModel):
    _inherit = "res.config.settings"

    whatsapp_instance_id = fields.Char('Whatsapp Instance ID')
    whatsapp_token = fields.Char('Whatsapp Token')
    qr_code_image = fields.Binary("QR code")
    whatsapp_authenticate = fields.Boolean('Authenticate', default=False)
    # group_send_report_url_in_message = fields.Boolean("Send Report URL in message", implied_group='pragmatic_odoo_whatsapp_integration.group_send_report_url_in_message')
    group_enable_signature = fields.Boolean("Add Signature?", implied_group='pragmatic_odoo_whatsapp_integration.group_enable_signature')
    group_display_chatter_message = fields.Boolean("Add in chatter message?",implied_group='pragmatic_odoo_whatsapp_integration.group_display_chatter_message')
    group_order_product_details_msg = fields.Boolean("Add Order product details in message?",implied_group='pragmatic_odoo_whatsapp_integration.group_order_product_details_msg')
    group_order_info_msg = fields.Boolean("Add Order product information in message?",implied_group='pragmatic_odoo_whatsapp_integration.group_order_info_msg')

    # group_purchase_send_report_url_in_message = fields.Boolean("Send Report URL in message", implied_group='pragmatic_odoo_whatsapp_integration.group_purchase_send_report_url_in_message')
    group_purchase_enable_signature = fields.Boolean("Add Signature?", implied_group='pragmatic_odoo_whatsapp_integration.group_purchase_enable_signature')
    group_purchase_display_chatter_message = fields.Boolean("Add in chatter message?", implied_group='pragmatic_odoo_whatsapp_integration.group_purchase_display_chatter_message')
    group_purchase_order_product_details_msg = fields.Boolean("Add Order product details in message?",
                                                            implied_group='pragmatic_odoo_whatsapp_integration.group_purchase_order_product_details_msg')
    group_purchase_order_info_msg = fields.Boolean("Add Order product information in message?", implied_group='pragmatic_odoo_whatsapp_integration.group_purchase_order_info_msg')


    # group_stock_send_report_url_in_message = fields.Boolean("Send Report URL in message",
    #                                                            implied_group='pragmatic_odoo_whatsapp_integration.group_stock_send_report_url_in_message')
    group_stock_enable_signature = fields.Boolean("Add Signature?", implied_group='pragmatic_odoo_whatsapp_integration.group_stock_enable_signature')
    group_stock_display_chatter_message = fields.Boolean("Add in chatter message?",
                                                            implied_group='pragmatic_odoo_whatsapp_integration.group_stock_display_chatter_message')
    group_stock_product_details_msg = fields.Boolean("Add order product details in message?",
                                                              implied_group='pragmatic_odoo_whatsapp_integration.group_stock_product_details_msg')
    group_stock_info_msg = fields.Boolean("Add order product information in message?", implied_group='pragmatic_odoo_whatsapp_integration.group_stock_info_msg')


    # group_invoice_send_report_url_in_message = fields.Boolean("Send Report URL in message",
    #                                                         implied_group='pragmatic_odoo_whatsapp_integration.group_invoice_send_report_url_in_message')
    group_invoice_enable_signature = fields.Boolean("Add Signature?", implied_group='pragmatic_odoo_whatsapp_integration.group_invoice_enable_signature')
    group_invoice_display_chatter_message = fields.Boolean("Add in chatter message?",
                                                         implied_group='pragmatic_odoo_whatsapp_integration.group_invoice_display_chatter_message')
    group_invoice_product_details_msg = fields.Boolean("Add order product details in message?",
                                                     implied_group='pragmatic_odoo_whatsapp_integration.group_invoice_product_details_msg')
    group_invoice_info_msg = fields.Boolean("Add order product information in message?", implied_group='pragmatic_odoo_whatsapp_integration.group_invoice_info_msg')

    group_crm_display_chatter_message = fields.Boolean("Add in chatter message?",
                                                           implied_group='pragmatic_odoo_whatsapp_integration.group_crm_display_chatter_message')
    group_crm_enable_signature = fields.Boolean("Add Signature?", implied_group='pragmatic_odoo_whatsapp_integration.group_crm_enable_signature')

    group_project_display_chatter_message = fields.Boolean("Add in chatter message?",
                                                       implied_group='pragmatic_odoo_whatsapp_integration.group_project_display_chatter_message')
    group_project_enable_signature = fields.Boolean("Add Signature?", implied_group='pragmatic_odoo_whatsapp_integration.group_project_enable_signature')
    @api.model
    def get_values(self):
        res = super(base, self).get_values()
        Param = self.env['ir.config_parameter'].sudo()
        res['whatsapp_instance_id'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.whatsapp_instance_id')
        res['whatsapp_token'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.whatsapp_token')
        res['whatsapp_authenticate'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.whatsapp_authenticate')

        # res['group_send_report_url_in_message'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_send_report_url_in_message')
        res['group_enable_signature'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_enable_signature')
        res['group_display_chatter_message'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_display_chatter_message')
        res['group_order_product_details_msg'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_order_product_details_msg')
        res['group_order_info_msg'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_order_info_msg')

        # res['group_purchase_send_report_url_in_message'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_purchase_send_report_url_in_message')
        res['group_purchase_enable_signature'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_purchase_enable_signature')
        res['group_purchase_display_chatter_message'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_purchase_display_chatter_message')
        res['group_purchase_order_product_details_msg'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_purchase_order_product_details_msg')
        res['group_purchase_order_info_msg'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_purchase_order_info_msg')

        # res['group_stock_send_report_url_in_message'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_stock_send_report_url_in_message')
        res['group_stock_enable_signature'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_stock_enable_signature')
        res['group_stock_display_chatter_message'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_stock_display_chatter_message')
        res['group_stock_product_details_msg'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_stock_product_details_msg')
        res['group_stock_info_msg'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_stock_info_msg')

        # res['group_invoice_send_report_url_in_message'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_invoice_send_report_url_in_message')
        res['group_invoice_enable_signature'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_invoice_enable_signature')
        res['group_invoice_display_chatter_message'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_invoice_display_chatter_message')
        res['group_invoice_product_details_msg'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_invoice_product_details_msg')
        res['group_invoice_info_msg'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_invoice_info_msg')

        res['group_crm_enable_signature'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_crm_enable_signature')
        res['group_crm_display_chatter_message'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_crm_display_chatter_message')

        res['group_project_enable_signature'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_project_enable_signature')
        res['group_project_display_chatter_message'] = Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.group_project_display_chatter_message')
        res.update(qr_code_image=Param.sudo().get_param('pragmatic_odoo_whatsapp_integration.qr_code_image'))
        return res


    def set_values(self):
        super(base, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.whatsapp_instance_id', self.whatsapp_instance_id)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.whatsapp_token', self.whatsapp_token)
        # self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_send_report_url_in_message', self.group_send_report_url_in_message)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_enable_signature', self.group_enable_signature)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_display_chatter_message', self.group_display_chatter_message)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_order_product_details_msg', self.group_order_product_details_msg)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_order_info_msg', self.group_order_info_msg)

        # self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_purchase_send_report_url_in_message', self.group_purchase_send_report_url_in_message)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_purchase_enable_signature', self.group_purchase_enable_signature)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_purchase_display_chatter_message', self.group_purchase_display_chatter_message)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_purchase_order_product_details_msg', self.group_purchase_order_product_details_msg)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_purchase_order_info_msg', self.group_purchase_order_info_msg)

        # self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_stock_send_report_url_in_message',
        #                                                  self.group_stock_send_report_url_in_message)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_stock_enable_signature', self.group_stock_enable_signature)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_stock_display_chatter_message', self.group_stock_display_chatter_message)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_stock_product_details_msg',
                                                         self.group_stock_product_details_msg)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_stock_info_msg', self.group_stock_info_msg)

        # self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_invoice_send_report_url_in_message',
        #                                                  self.group_invoice_send_report_url_in_message)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_invoice_enable_signature', self.group_invoice_enable_signature)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_invoice_display_chatter_message', self.group_invoice_display_chatter_message)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_invoice_product_details_msg',
                                                         self.group_invoice_product_details_msg)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_invoice_info_msg', self.group_invoice_info_msg)

        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_crm_enable_signature', self.group_crm_enable_signature)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_crm_display_chatter_message', self.group_crm_display_chatter_message)

        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_project_enable_signature', self.group_project_enable_signature)
        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.group_project_display_chatter_message', self.group_project_display_chatter_message)

        self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.qr_code_image', self.qr_code_image)

    def action_get_qr_code(self):
        return {
            'name': _("Scan WhatsApp QR Code"),
            'view_mode': 'form',
            # 'view_id': view_id,
            'view_type': 'form',
            'res_model': 'whatsapp.scan.qr',
            'type': 'ir.actions.act_window',
            'target': 'new',
            # 'context': context,
        }

    def action_logout_from_whatsapp(self):
        Param = self.sudo().get_values()
        url = 'https://api.chat-api.com/instance' + Param.get('whatsapp_instance_id') + '/logout?token=' + Param.get('whatsapp_token')
        headers = {
            "Content-Type": "application/json",
        }

        tmp_dict = {
            "accountStatus": "Logout request sent to WhatsApp"
        }

        response = requests.post(url, json.dumps(tmp_dict), headers=headers)

        if response.status_code == 201 or response.status_code == 200:
            _logger.info("\nWhatsapp logout successfully")
            self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.whatsapp_authenticate', False)


