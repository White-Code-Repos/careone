import logging
from odoo import api, fields, models, tools
_logger = logging.getLogger(__name__)
class sms_track(models.Model):
    _name = "sms_track"

    model_id = fields.Char('Model',readonly=True)
    mobile_no = fields.Char('Mobile No.', readonly=True)
    response_id = fields.Char('Response',readonly=True)
    message_id = fields.Text('Messages',readonly=True)
    gateway_id = fields.Many2one('gateway_setup', string='GateWay',readonly=True)

    @api.model
    def sms_track_create(self, record_id, sms_rendered_content, rendered_sms_to, response, model, gateway_id):
        value = {
            'model_id': model,
            'mobile_no': rendered_sms_to,
            'message_id': sms_rendered_content,
            'response_id': response,
            'gateway_id': gateway_id,
        }
        track_id = self.create(value)
