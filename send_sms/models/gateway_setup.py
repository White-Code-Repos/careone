from odoo import _, api, fields, models, tools
from odoo.exceptions import except_orm, UserError, Warning
import requests
import urllib
import re
import logging

_logger = logging.getLogger(__name__)

class GateWaysetup(models.Model):
    _name = "gateway_setup"
    _description = "GateWay Setup"

    name = fields.Char(required=True, string='Name')
    gateway_url = fields.Char(required=True, string='GateWay Url')
    message = fields.Text('Message')
    mobile = fields.Char('Mobile')

    def send_sms_link(self,sms_rendered_content,rendered_sms_to,record_id,model,gateway_url_id):
        sms_rendered_content = sms_rendered_content.encode('ascii', 'ignore')
        sms_rendered_content_msg = urllib.parse.quote_plus(sms_rendered_content)
        if rendered_sms_to:
            rendered_sms_to = re.sub(r' ', '', rendered_sms_to)
            if '+' in rendered_sms_to:
                rendered_sms_to = rendered_sms_to.replace('+', '')
            if '-' in rendered_sms_to:
                rendered_sms_to = rendered_sms_to.replace('-', '')


        if rendered_sms_to:
            send_url = gateway_url_id.gateway_url
            send_link = send_url.replace('{mobile}',rendered_sms_to).replace('{message}',sms_rendered_content_msg)
            try:
                response = requests.request("GET", url = send_link).text
                return response
            except Exception as e:
                return e


    @api.one
    def sms_test_action(self):
        active_model = 'gateway_setup'
        message = self.env['send_sms'].render_template(self.message, active_model, self.id)
        mobile_no = self.env['send_sms'].render_template(self.mobile, active_model, self.id)
        response = self.send_sms_link(message, mobile_no,self.id,active_model,self)
        raise Warning(response)
