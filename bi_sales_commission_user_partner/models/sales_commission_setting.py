# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime, date

class ProductRealEstate(models.Model):
	_inherit = 'product.template'

	commission_ids = fields.One2many('commission.settings','product_id','Commission Settings')
	is_commission_product = fields.Boolean(string='Commission Product')
	
	def website_document_compute(self):
		for product in self:
			products = self.env['ir.attachment'].search([('res_model', '=', 'product.template'),('res_id', '=', product.id),('datas_fname', '!=', False)], order='mimetype')
			product.document_attach_ids = products

	

class SalesCommissionSettings(models.Model):
	_inherit = 'sale.order'
	
	product_comm_level_ids = fields.One2many('product.commission.level', 'sale_order_id', 'Sales Commission User Setting')

class PartnerCommissionSettings(models.Model):
	_inherit = 'res.partner'
	
	commission_ids = fields.One2many('commission.settings','partner_id','Commission Settings')

class ProductCategoryCommissionSettings(models.Model):
	_inherit = 'product.category'
	
	commission_ids = fields.One2many('commission.settings','product_category_id','Commission Settings')  

class ProductCategoryCommissionSettings(models.Model):
	_inherit = 'crm.team'
	
	commission_ids = fields.One2many('commission.settings','sales_team_id','Commission Settings')      

class CommissionSetting(models.Model): 

	_name = 'commission.settings'
	_rec_name = 'commission_level_id'
	
	commission_level_id = fields.Many2one('commission.level', 'Sales Commission Level')
	percentage = fields.Float('Percentage(%)')
	partner_id = fields.Many2one('res.partner', string='Partners')
	product_id = fields.Many2one('product.template', string='Product')
	product_category_id = fields.Many2one('product.category', string='Product Category')
	sales_team_id = fields.Many2one('crm.team', string='Sales Team')


class SalesCommissionUserSetting(models.Model):
	_name = 'product.commission.level'
	
	sale_order_id = fields.Many2one('sale.order', 'Sale Order')
	invoice_id = fields.Many2one('account.move', 'Invoice')
	payment_id = fields.Many2one('account.payment','Payment')
	commission_level_id = fields.Many2one('commission.level', 'Sales Commission Level')
	user_partner_id = fields.Many2one('res.partner', 'Users/Partners')


class SalesCommissionLevel(models.Model):
	_name = 'commission.level'
	_rec_name = 'commssion_level_name'
	
	commssion_level_name = fields.Char('Sales Commission Level')
	commssion_level_code = fields.Char('Code')

class CommissionConfigSale(models.TransientModel):
	_inherit = "res.config.settings"

	commission_configuration = fields.Selection([('sale_order', 'Commission based on Sales Order'),
										('invoice', 'Commission based on Invoice'),
										('payment', 'commission based on Payment')
									   ],string='Pay Commission Based On ', default='payment')
	
	commission_calc_on = fields.Selection([('sales_team', 'Sales Team'),
										('product_category', 'Product Category'),
										('product', 'Product'),
										('partner','Partner'),
									   ],string='Commission Calculation Based On ', default='product')
	@api.model
	def default_get(self, fields_list):
		res = super(CommissionConfigSale, self).default_get(fields_list)
		if self.search([], limit=1, order="id desc").commission_configuration:
			commission_configuration = self.search([], limit=1, order="id desc").commission_configuration
			res.update({
						'commission_configuration':commission_configuration
					  })
		
		if self.search([], limit=1, order="id desc").commission_calc_on:
			commission_calc_on = self.search([], limit=1, order="id desc").commission_calc_on
			res.update({
						'commission_calc_on':commission_calc_on
					  })    
		
		return res

class AccountInstallments(models.Model):
	_inherit = 'account.move'
	
	rel_sale_order = fields.Many2one('sale.order', 'Sales Order')
	product_comm_level_ids = fields.One2many('product.commission.level', 'invoice_id', 'Sales Commission User Setting')

class AccountPaymentCommission(models.Model):
	_inherit = 'account.payment'
	
	product_comm_level_ids = fields.One2many('product.commission.level', 'payment_id', 'Sales Commission User Setting')




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
