#  -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2019-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning


class ProductPacktWizard(models.TransientModel):
	_name = 'product.pack.wizard'
	_description = 'Pack Product Wizard'

	product_id = fields.Many2one('product.product',string='Bundle',required=True)
	quantity = fields.Float('Quantity',required=True ,default=1)

	def add_product_button(self):
		product_obj = self.product_id.wk_product_pack
		orderLine = self.env['sale.order.line'].create({
			'order_id':self._context['active_id'],
			'product_id':self.product_id.id,
			'name':self.product_id.name,
			'price_unit':self.product_id.list_price,
			'product_uom':1,
			'product_uom_qty':self.quantity,
		})
		orderLine._compute_tax_id()
		return True

	@api.onchange('quantity', 'product_id')
	def onchange_quantity_pack(self):
		if self.quantity:
			if self.product_id:
				for prod in self.product_id.wk_product_pack:
					if self.quantity > prod.product_id.virtual_available:
						warn_msg = _('You plan to sell %s of the pack %s but you have only  %s quantities of the product %s available, and the total quantity to sell is  %s !!'%(self.quantity, prod.name, prod.product_id.virtual_available, prod.product_id.name, self.quantity * prod.product_quantity))
						return {
						'warning': {
							'title': 'Invalid value',
							'message': warn_msg
						}
					}