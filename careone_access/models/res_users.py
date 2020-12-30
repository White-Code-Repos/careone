# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = 'res.users'

    allowed_journal = fields.Many2many('account.journal','user_journal_rel_allow','user_id','journal_id')
    
