# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class IrActionsServer(models.Model):

    _inherit = 'ir.actions.server'

    state = fields.Selection(selection_add=[
        ('sms', 'Send SMS'),
    ])

    sms_template_id = fields.Many2one('send_sms',string="SMS Template", ondelete='set null', domain="[('model_id', '=', model_id)]",)

    @api.model
    def run_action_sms(self, action, eval_context=None):
        if not action.sms_template_id or not self._context.get('active_id'):
            return False
        self.env['send_sms'].send_sms(action.sms_template_id, self.env.context.get('active_id'))
        return False
