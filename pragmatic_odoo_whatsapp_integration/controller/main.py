import requests

from odoo import http, _, models, api
import logging
import json
import base64
from odoo.exceptions import UserError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request


_logger = logging.getLogger(__name__)


class SendMessage(http.Controller):
    _name = 'send.message.controller'

    def format_amount(self, amount, currency):
        fmt = "%.{0}f".format(currency.decimal_places)
        lang = http.request.env['res.lang']._lang_get(http.request.env.context.get('lang') or 'en_US')

        formatted_amount = lang.format(fmt, currency.round(amount), grouping=True, monetary=True)\
            .replace(r' ', u'\N{NO-BREAK SPACE}').replace(r'-', u'-\N{ZERO WIDTH NO-BREAK SPACE}')

        pre = post = u''
        if currency.position == 'before':
            pre = u'{symbol}\N{NO-BREAK SPACE}'.format(symbol=currency.symbol or '')
        else:
            post = u'\N{NO-BREAK SPACE}{symbol}'.format(symbol=currency.symbol or '')

        return u'{pre}{0}{post}'.format(formatted_amount, pre=pre, post=post)

    @http.route('/whatsapp/send/message', type='http', auth='public', website=True, csrf=False)
    def sale_order_paid_status(self, **post):
        ref_name = post.get('order')
        ref_id = 'Shop/' + ref_name[-4:]
        pos_order = http.request.env['pos.order'].sudo().search([('name', '=', ref_id)])

        if pos_order.partner_id:
            if pos_order.partner_id.mobile and pos_order.partner_id.country_id.phone_code:
                doc_name = 'POS'
                # res_user_id = self.env['res.users'].search([('id', '=', self.env.user.id)])
                msg = "Hello " + pos_order.partner_id.name
                if pos_order.partner_id.parent_id:
                    msg += "(" + pos_order.partner_id.parent_id.name + ")"
                msg += "\n\nYour "
                msg += doc_name + " *" + pos_order.name + "* "

                msg += " with Total Amount " + self.format_amount(pos_order.amount_total, pos_order.pricelist_id.currency_id) + "."
                msg += "\n\nFollowing is your order details."
                for line_id in pos_order.lines:
                    msg += "\n\n*Product:* " + line_id.product_id.name + "\n*Qty:* " + str(line_id.qty) + " " + "\n*Unit Price:* " + str(
                        line_id.price_unit) + "\n*Subtotal:* " + str(line_id.price_subtotal)
                    msg += "\n------------------"

                Param = http.request.env['res.config.settings'].sudo().get_values()
                url = 'https://api.chat-api.com/instance' + Param.get('whatsapp_instance_id') + '/sendMessage?token=' + Param.get('whatsapp_token')
                headers = {
                    "Content-Type": "application/json",
                }
                whatsapp_number =  pos_order.partner_id.mobile
                whatsapp_msg_number_without_space = whatsapp_number.replace(" ", "")
                whatsapp_msg_number_without_code = whatsapp_msg_number_without_space.replace('+' + str(pos_order.partner_id.country_id.phone_code), "")
                tmp_dict = {
                    "phone": "+" + str(pos_order.partner_id.country_id.phone_code) + "" +whatsapp_msg_number_without_code,
                    "body": msg}

                response = requests.post(url, json.dumps(tmp_dict), headers=headers)

                if response.status_code == 201 or response.status_code == 200:
                    _logger.info("\nSend Message successfully")
                    return json.dumps({'msg_response': response.status_code})

class AuthSignupHomeDerived(AuthSignupHome):

    def get_auth_signup_config(self):
        """retrieve the module config (which features are enabled) for the login page"""
        get_param = request.env['ir.config_parameter'].sudo().get_param
        countries = request.env['res.country'].sudo().search([])
        return {
            'signup_enabled': request.env['res.users']._get_signup_invitation_scope() == 'b2c',
            'reset_password_enabled': get_param('auth_signup.reset_password') == 'True',
            'countries': countries
        }

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password', 'mobile', 'country_id') }
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        supported_langs = [lang['code'] for lang in request.env['res.lang'].sudo().search_read([], ['code'])]
        if request.lang in supported_langs:
            values['lang'] = request.lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()
    #
    #
    #
