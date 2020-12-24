# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
#              Dan Stoica
# See README.rst file on addons root folder for license details

import logging

import requests

from odoo import api, models
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, RedirectWarning

_logger = logging.getLogger(__name__)


class SmsApi(models.AbstractModel):
    _inherit = "sms.api"

    @api.model
    def _contact_iap(self, local_endpoint, params):
        account = self.env["iap.account"].get("sms")
        # params['account_token'] = account.account_token
        # endpoint = self.env['ir.config_parameter'].sudo().get_param('sms.endpoint')

        res = []
        endpoint = self.env["ir.config_parameter"].sudo().get_param("sms.endpoint", "")
        for message in params["messages"]:

            endpoint = account.endpoint
            endpoint = endpoint.format(**message)
            result = requests.get(endpoint)
            response = result.content.decode("utf-8")
            res_value = {"state": "success", "res_id": message["res_id"]}
            if "OK" not in response:
                res_value["state"] = "server_error"
            res += [res_value]
        raise UserError(res)
        return res
    
    
    #def smssend(self,mobile):
    #    rendered_sms_to =mobile
    #    sms_rendered_content_msg1 ="تم تحديد (" + str(self.name) + ") المتواجد  في  (" + str(self.companyid.name) +") كمطلوب, يرجى سرعة الضبط"

        #sms_rendered_content = sms_rendered_content_msg1#.encode('utf8', 'ignore')

        #sms_rendered_content_msg = urllib.parse.quote_plus(sms_rendered_content)
#        send_url="https://smsmisr.com/api/webapi/?username=wI5xKUgK&password=YVxakdcT1T&language=2&sender=tabadeal&mobile="+str(rendered_sms_to)+",&message="+str(sms_rendered_content)
        