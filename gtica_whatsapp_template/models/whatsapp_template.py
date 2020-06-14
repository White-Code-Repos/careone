# -*- coding: utf-8 -*-

import logging
import urllib
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class WhatsappTemplate(models.Model):
    _name = 'whatsapp.template'
    _description = 'Message default in Whatsapp'

    name = fields.Char(string="Title Template")
    template_messege = fields.Text(string="Message Template")
    category = fields.Selection([ ('partner', 'Partner/Contact'),
                                  ('sale', 'Sale/Quoting'),
                                  ('invoice', 'Invoice'),
                                  ('delivery', 'Delivery/Stock'),
                                  ('crm', 'CRM/Marketing'),
                                  ('provider', 'Provider'),
                                  ('other', 'Other'),], default='other', string="Category")