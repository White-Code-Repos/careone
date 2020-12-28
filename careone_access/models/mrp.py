# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

# class AccountMove(models.Model):
#     _inherit = 'mrp.production'

    # current_group_mrp = fields.Boolean(compute="_compute_current_group_mrp")
    #
    # def _compute_current_group_mrp(self):
    #     flag = self.pool.get('res.users').has_group(self.env.user, 'careone_access.careone_worker')
    #     if flag:
    #         self.current_group_mrp = True
    #     else:
    #         self.current_group_mrp = False
