# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float('Discount %')


    @api.depends('product_qty', 'price_unit', 'taxes_id','discount')
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
            if line.discount:
                discount = (line.price_unit * line.discount * line.product_qty)/100
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'] ,
                    'price_subtotal': taxes['total_excluded'] - discount,
                })
            else:
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
