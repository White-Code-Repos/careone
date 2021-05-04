# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import date_utils, float_compare, float_round, float_is_zero


class SaleOrder(models.Model):
    _inherit = "sale.order"

    mo_count = fields.Integer(string='MO Count', compute='_get_mrp', readonly=True)
    check_combo = fields.Boolean()
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True,
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)],
                                         'sale': [('readonly', False)]},
                                 copy=False, default=fields.Datetime.now,
                                 help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")

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

    def action_confirm(self):
        if self.check_combo:
            self.check_combo = False
        else:
            for line in self.order_line:
                if line.product_id.is_combo:
                    raise UserError(_("please check combo first to confirm the order."))

        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'date_order': fields.Datetime.now()
        })
        self._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        return True

    def check_compo(self):
        sale_order_line = self.env['sale.order.line']
        for lines in self.order_line:
            if lines.checked:
                lines.unlink()

        for line in self.order_line:
            for product in line.product_id.combo_product_id:
                # Create new bonus line in sale order
                sale_order_line.create({
                    'product_id': product.product_id.id,
                    'order_id': self.id,
                    'name': product.product_id.display_name,
                    'product_uom_qty': product.product_quantity,
                    'product_uom': product.uom_id.id,
                    'price_unit': product.product_id.standard_price,
                    'checked': True,
                })
            self.check_combo = True


class SaleOrderLines(models.Model):
    _inherit = "sale.order.line"

    checked = fields.Boolean()
