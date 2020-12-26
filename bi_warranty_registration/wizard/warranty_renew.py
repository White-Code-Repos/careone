# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class WarrantyRenew(models.TransientModel):
	_name = 'warranty.renew'
	_description = "Warranty Renew"
	
	product_id = fields.Many2one('product.product', 'Product', domain="[('allow_renewal', '=', True)]", required=True)
	serial_no = fields.Many2one('stock.production.lot',"Serial No", domain="[('product_id', '=', product_id)]", required=True)
	partner_id = fields.Many2one('res.partner', 'Customer', required=True)
	warranty = fields.Many2one('product.warranty', 'Warranty')
	renew_amt = fields.Float('Renewal Amount')
	
	@api.onchange('product_id')
	def renewal_cost_update(self):
		if self.product_id:
			self.update({'renew_amt': self.product_id.warranty_renewal_cost})

	def action_view_invoice(self):
		action = self.env.ref('bi_warranty_registration.action_warranty_invoice_tree1').read()[0]
		
		return action     

	@api.onchange('serial_no')
	def warranty_updt_serial(self): 
		warranty_obj = self.env['product.warranty'].search([])
		for res in warranty_obj:
			if res.product_serial_id == self.serial_no:
				self.update({
					'warranty': res.id,
					'partner_id' : res.partner_id.id,
					})
	
	def _create_invoice(self):

		if self.warranty.partner_id.id != self.partner_id.id :
			raise ValidationError(_('Select Correct Customer Of Warranty'))

		if self.warranty.state == 'new' :
			raise ValidationError(_('Selected Serial number is not in under warranty'))

		
		self.warranty.update({'state':"invoiced"})
		inv_obj = self.env['account.move']
		
		account_id = False
		name = _('Warranty Renewal')
		if self.product_id.id:
			if not self.product_id.property_account_income_id:
				account_id = self.product_id.categ_id.property_account_income_categ_id.id
				
			else:
				account_id = self.product_id.property_account_income_id.id
	   
		invoice = inv_obj.create({
			'invoice_origin': self.warranty.serial_no,
			'type': 'out_invoice',
			'ref': False,
			
			'partner_id': self.partner_id.id,
			'warranty_invoice': True,
			'warranty_reg_id': self.warranty.id,
			'invoice_line_ids': [(0, 0, {
				'name': 'Warranty of '+ str(self.product_id.display_name),
				
				'price_unit': self.renew_amt, 
				
			})],
			
			'narration': self.warranty.comment,
		})
		return invoice
	
	def state_renew(self):
		if self.warranty.renew_no < self.product_id.warranty_renewal_time:
			self.warranty.update({'renew_no': self.warranty.renew_no + 1})
			self.serial_no.update({'renewal_times': self.warranty.renew_no})
			self.warranty.update({'warranty_create_date': self.warranty.warranty_end_date, 'state':'invoiced'})
			self.serial_no.update({'start_date_warranty': self.warranty.warranty_end_date})
			
			months_w = int(self.product_id.warranty_renewal_period)
			date_1= (datetime.strptime(str(self.warranty.warranty_create_date), '%Y-%m-%d').date()+relativedelta(months =+ months_w))
			self.warranty.update({'warranty_end_date':date_1})
			self.serial_no.update({'end_date_warranty': date_1})
			
			renew_history_obj = self.env['warranty.history']
			
			if self.renew_amt == 0:
			
				renew_history_obj.create({
					'date_renewal' : datetime.now(),
					'warranty_renewal_date': self.warranty.warranty_create_date,
					'warranty_renew_end_date': date_1,
					'warranty_id':self.warranty.id,
					'free': True,
				})
			if self.renew_amt > 0:
				renew_history_obj.create({
					'date_renewal' : datetime.now(),
					'warranty_renewal_date': self.warranty.warranty_create_date,
					'warranty_renew_end_date': date_1,
					'renewal_cost': self.renew_amt,
					'warranty_id':self.warranty.id,
					'paid': True,
				})
		else:
			raise UserError(_('Maximun Renewal Times Exceeded'))
		

	def create_invoices(self):
		warranty_re_obj = self.env['product.warranty'].search([('product_serial_id','=', self.serial_no.id)])
		if not warranty_re_obj: 
			raise ValidationError(_('Warranty is not created for this Product/Serial No'))
		else:
			if self.renew_amt > 0 : 
				self._create_invoice()
			self.state_renew()
		if self._context.get('open_invoices', False) and self.renew_amt > 0:
			return self.action_view_invoice()
		return {'type': 'ir.actions.act_window_close'}
