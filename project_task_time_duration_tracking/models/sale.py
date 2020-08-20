# -*- coding: utf-8 -*-

from odoo import fields, models, _

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for line in self.order_line:
            if line.product_id.is_combo:
                task_id = self.env['project.task'].search([('id', '=', line.task_id.id)])
                if task_id:
                    combo_list = []
                    for combo_product in line.product_id.combo_product_id:
                        combo_list.append((0, 0, {
                            'product_id': combo_product.product_id.id,
                            'product_uom_qty': (combo_product.product_quantity * line.product_uom_qty),
                            'partner_id': self.partner_id.id,
                        }))
                    task_id.sale_task_bom_ids = combo_list
        return res
