import logging

from ast import literal_eval

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr

from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.addons.auth_signup.models.res_partner import SignupError, now
import requests
import json

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    mobile = fields.Char()
    country_id = fields.Many2one('res.country', 'Country')


    @api.model
    def signup(self, values, token=None):


        # print("\n\nself121212: ",self,"\nvalues: ",values)
        if not token:
            values['mobile'] = values.get('mobile')
            values['country_id'] = values.get('country_id')
            # print("\n\n\n\nvalues121================::::",values)
            user_id=self._signup_create_user(values)
            if values['mobile']:
                user_id.partner_id.mobile=values['mobile']

            if values['country_id']:
                user_id.partner_id.country_id=int(values['country_id'])


            Param = self.env['res.config.settings'].sudo().get_values()
            if values.get('country_id'):
                country_id = self.env['res.country'].sudo().search([('id', '=', values.get('country_id') )])
                msg = ''
                if values.get('mobile') and country_id:
                    whatsapp_number = "+" + str(country_id.phone_code) + "" + values.get('mobile')
                    url = 'https://api.chat-api.com/instance' + Param.get('whatsapp_instance_id') + '/sendMessage?token=' + Param.get('whatsapp_token')
                    headers = {
                        "Content-Type": "application/json",
                    }
                    tmp_dict = {
                        "phone": "+" + whatsapp_number,
                        "body": 'Hello ' + values.get('name')+','+ '\nYou have successfully registered and logged in'+'\n*Your Email:* '+values.get('login'),

                    }
                    response = requests.post(url, json.dumps(tmp_dict), headers=headers)

                    if response.status_code == 201 or response.status_code == 200:
                        _logger.info("\nSend Message successfully")
        # return True
        return (self.env.cr.dbname, values.get('login'), values.get('password'))








