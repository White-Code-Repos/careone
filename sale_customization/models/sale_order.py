# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import date_utils, float_compare, float_round, float_is_zero


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    mo_count = fields.Integer(string='MO Count', compute='_get_mrp', readonly=True)
    
    @api.depends('name')
    def _get_mrp(self):
        for order in self:
            mrp_ids = self.env['mrp.production'].search([('origin', '=', order.name)])
            order.mo_count = len(mrp_ids)
    
    def action_view_manfacturing(self):
        self.ensure_one()

        # Create action.
        action = {
            'name': _('Reverse Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
        }
        mrp_ids = self.env['mrp.production'].search([('origin', '=', self.name)])
        if len(mrp_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': mrp_ids.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', mrp_ids.ids)],
            })
        return action