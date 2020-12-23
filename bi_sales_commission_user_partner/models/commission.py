# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import calendar
import datetime
from odoo import api, fields, models, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError

class SalesCommission(models.Model):

	_name = 'sale.commission.sheet'
	_order = "id desc"

	@api.depends('commission_line_ids')
	def calc_total_sheet_amt(self):
		
		for i in self:
			total = 0.0
			for am in i.commission_line_ids:
				total += am.amount
			i.update({'total_commission_amt': total})
			
	name = fields.Char('Name', default='New')
	sales_partner = fields.Many2one('res.partner', 'Sales Partner')
	start_date = fields.Date('Start Date')
	end_date = fields.Date('End Date', readonly='1')
	commission_product_id = fields.Many2one('product.product', 'Commission Product')
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
	total_commission_amt = fields.Float('Total Commission Amount', compute='calc_total_sheet_amt',store=True)
	commission_paid = fields.Boolean('Commission Paid',compute='_check_payment')
	commission_line_ids = fields.One2many('sale.commission.line', 'commission_id', 'Commission Lines')
	state = fields.Selection([('draft','Draft'),('open','Open'),('paid','Paid')], default='draft', string='Commission Line Paid')
	invoice_id = fields.Many2one('account.move', 'Invoice')
	
	def _check_payment(self):
		for line in self :
			if line.invoice_id.invoice_payment_state == 'paid' :
				line.commission_paid = True
				line.write({'state': 'paid'})
				for rec in line.commission_line_ids :
					rec.write({'state': 'paid'})

			else :
				line.commission_paid = False




	def create_invoice_commission(self):
	
		invoice_obj = self.env['account.move']
		invoice_line_obj = self.env['account.move.line']
		
		for u in self:
			if not u.sales_partner.property_account_payable_id:
				raise ValidationError(_('Please Configure Payable Account in Customer'))
			
			inv_create_obj = invoice_obj.create({
							'partner_id': u.sales_partner.id,
							'type': 'in_invoice',
							'invoice_line_ids' : [(0,0, {
								'product_id': u.commission_product_id.id,
								'name': u.commission_product_id.name,
								'quantity':1,
								'price_unit': u.total_commission_amt,
								'account_id': u.commission_product_id.property_account_expense_id.id,
							})]
						})
			if not u.commission_product_id.property_account_expense_id:
				raise ValidationError(_('Please Configure Expense Account in Product')) 
						
			u.update({'invoice_id': inv_create_obj.id, 'state':'open'})
			
			return {
					'name':'account.move.form',
					'res_model':'account.move',
					'view_mode':'form',
					'res_id': inv_create_obj.id,
					'target':'current',
					'type':'ir.actions.act_window'
					}
							
	
	@api.model
	def create(self,vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('sale.commission.sheet') or _('New')
		res = super(SalesCommission, self).create(vals)
		return res
	
	
class SalesCommissionLines(models.Model):
	
	_name = 'sale.commission.line'
	_rec_name = 'sales_partner'
	_order = "id desc"
	
	commission_date = fields.Date('Commission Date')
	sales_partner = fields.Many2one('res.partner', 'Sales Partner')
	source = fields.Char('Source Document')
	amount = fields.Float('Amount')
	state = fields.Selection([('draft','Draft'),('paid','Paid')], default='draft', string='Commission Line Paid')
	commission_id = fields.Many2one('sale.commission.sheet', 'Commission Sheet')
	
	def _cron_commission_worksheet(self):
		today_date = datetime.now().date()
		commission_line_obj = self.env['sale.commission.line'].search([])
		commission_sheet_obj = self.env['sale.commission.sheet']
		partner_obj = self.env['res.partner'].search([])
		commission_product = self.env['product.product'].search([('is_commission_product','=',True)], limit=1)
		
		end_date = datetime.today().date()
		last_day_of_month = calendar.monthrange(end_date.year, end_date.month)[1]
		
		if int(datetime.today().strftime("%d")) == int(last_day_of_month):
			for p in partner_obj:
				for m in p.commission_line_ids:
					comm_date = str(datetime.strptime(str(m.commission_date), '%Y-%m-%d').strftime("%m")) 
					if int(comm_date) == int(datetime.today().strftime("%m")):
						today = date.today()
						d = today

						start_date = date(d.year, d.month,1)
						end_date = date(today.year, today.month,1) + relativedelta(days=29)
						
						from_date = str(start_date)
						to_date = str(end_date)
						
						sheet_id = commission_sheet_obj.search([('sales_partner','=', p.id),('start_date','=', from_date)])
						if not sheet_id:
							sheet_id = commission_sheet_obj.create({'sales_partner': p.id, 'start_date': from_date, 'end_date': to_date, 'commission_product_id':commission_product.id})
						m.update({'commission_id': sheet_id.id})

class CreateCommissionSalesOrder(models.Model):
	_inherit = 'sale.order'
	
	def action_confirm(self):
		res = super(CreateCommissionSalesOrder, self).action_confirm()
		if self.env['res.config.settings'].sudo().search([], limit=1, order="id desc").commission_configuration == 'sale_order':
			commission_line_obj = self.env['sale.commission.line']
			commission_calc_amt = self.env['commission.settings']
			comm_calc_product = self.env['product.template']
			comm_worksheet_obj = self.env['sale.commission.sheet']
			

			order_product = []
			for i in self.order_line:
				order_product = i.product_id.product_tmpl_id
			
			order_product_category = []
			for j in self.order_line:
				order_product_category = j.product_id.product_tmpl_id.categ_id
			
			commission_product = self.env['product.product'].search([('product_tmpl_id.is_commission_product','=', True)])
			
			date_1 = (datetime.strptime(str(datetime.now().date()), '%Y-%m-%d')+relativedelta(months =+ 1))

			for co in self.product_comm_level_ids:
				commission_calc_on = self.env['res.config.settings'].sudo().search([], limit=1, order="id desc").commission_calc_on
				if commission_calc_on == 'sales_team':
					if co.user_partner_id:
						if co.commission_level_id:
							comm_filter = commission_calc_amt.search([('sales_team_id','=', self.team_id.id),('commission_level_id','=', co.commission_level_id.id)])
							commission_line_obj.create({'sales_partner': co.user_partner_id.id, 'commission_date': datetime.now().date(), 'source': self.name, 'amount': (comm_filter.percentage * self.amount_total)/100}) #, 'commission_id': sheet.id
			
				if commission_calc_on == 'product':
					if co.user_partner_id:
						for o_line in self.order_line :

							order_product = o_line.product_id.product_tmpl_id
							
							if co.commission_level_id and order_product.is_commission_product == True:
								comm_filter_p = commission_calc_amt.sudo().search([('product_id','=', order_product.id),('commission_level_id','=', co.commission_level_id.id)])
								
								commission_p_line = commission_line_obj.sudo().search([('source','=',self.name),('sales_partner','=',co.user_partner_id.id)])

								
								if commission_p_line :
									commission_p_line.write({'amount' : commission_p_line.amount + (comm_filter_p.percentage * self.amount_total)/100})
								
								else:
								
									commission_line_obj.sudo().create({'sales_partner': co.user_partner_id.id, 'commission_date': datetime.now().date(), 'source': self.name, 'amount': (comm_filter_p.percentage * self.amount_total)/100}) 
				if commission_calc_on == 'product_category':
					if co.user_partner_id:
						if co.commission_level_id:
							comm_filter_p_c = commission_calc_amt.search([('product_category_id','=', order_product_category.id),('commission_level_id','=', co.commission_level_id.id)])
							commission_line_obj.create({'sales_partner': co.user_partner_id.id, 'commission_date': datetime.now().date(), 'source': self.name, 'amount': (comm_filter_p_c.percentage * self.amount_total)/100}) #, 'commission_id': sheet.id
				if commission_calc_on == 'partner':
					if co.user_partner_id:
						if co.commission_level_id:
							comm_filter_par = commission_calc_amt.search([('partner_id','=', self.partner_id.id),('commission_level_id','=', co.commission_level_id.id)])
							commission_line_obj.create({'sales_partner': co.user_partner_id.id, 'commission_date': datetime.now().date(), 'source': self.name, 'amount': (comm_filter_par.percentage * self.amount_total)/100}) #, 'commission_id': sheet.id
		return res
		

class CreateCommissionInvoice(models.Model):
	
	_inherit = 'account.move' 

	def action_post(self):
		res = super(CreateCommissionInvoice, self).action_post()
		###################################### Commission calculation on Invoice ###################################################
		
		if self.env['res.config.settings'].sudo().search([], limit=1, order="id desc").commission_configuration == 'invoice':
			commission_line_obj = self.env['sale.commission.line']
			commission_calc_amt = self.env['commission.settings']
			comm_calc_product = self.env['product.template']
			comm_worksheet_obj = self.env['sale.commission.sheet']
			
			commission_product = self.env['product.product'].search([('product_tmpl_id.is_commission_product','=', True)])
			date_1 = (datetime.strptime(str(datetime.now().date()), '%Y-%m-%d')+relativedelta(months =+ 1))
				
			inv_product = []
			for i in self.invoice_line_ids:
				inv_product = i.product_id.product_tmpl_id
				
			inv_product_category = []
			for j in self.invoice_line_ids:
				inv_product_category = j.product_id.product_tmpl_id.categ_id
					
			for co in self.product_comm_level_ids:
				commission_calc_on = self.env['res.config.settings'].sudo().search([], limit=1, order="id desc").commission_calc_on
				if commission_calc_on == 'sales_team':
					if co.user_partner_id:
						if co.commission_level_id:
							comm_filter = commission_calc_amt.search([('sales_team_id','=', self.team_id.id),('commission_level_id','=', co.commission_level_id.id)])
							commission_line_obj.create({'sales_partner': co.user_partner_id.id, 'commission_date': datetime.now().date(), 'source': self.name, 'amount': (comm_filter.percentage * self.amount_total)/100}) #, 'commission_id': sheet.id
				if commission_calc_on == 'product':
					if co.user_partner_id:
						for o_line in self.invoice_line_ids:

								inv_product = o_line.product_id.product_tmpl_id

								if co.commission_level_id and inv_product.is_commission_product == True:
									comm_filter_p = commission_calc_amt.search([('product_id','=', inv_product.id),('commission_level_id','=', co.commission_level_id.id)])
									
									commission_p_line = commission_line_obj.sudo().search([('source','=',self.name),('sales_partner','=',co.user_partner_id.id)])

										
									if commission_p_line :
										commission_p_line.write({'amount' : commission_p_line.amount + (comm_filter_p.percentage * self.amount_total)/100})
									
									else:
										commission_line_obj.create({'sales_partner': co.user_partner_id.id, 'commission_date': datetime.now().date(), 'source': self.name, 'amount': (comm_filter_p.percentage * self.amount_total)/100}) #, 'commission_id': sheet.id
				
				if commission_calc_on == 'product_category':
					if co.user_partner_id:
						if co.commission_level_id:
							comm_filter_p_c = commission_calc_amt.search([('product_category_id','=', inv_product_category.id),('commission_level_id','=', co.commission_level_id.id)])
							commission_line_obj.create({'sales_partner': co.user_partner_id.id, 'commission_date': datetime.now().date(), 'source': self.name, 'amount': (comm_filter_p_c.percentage * self.amount_total)/100}) #, 'commission_id': sheet.id
				if commission_calc_on == 'partner':
					if co.user_partner_id:
						if co.commission_level_id:
							comm_filter_par = commission_calc_amt.search([('partner_id','=', self.partner_id.id),('commission_level_id','=', co.commission_level_id.id)])
							commission_line_obj.create({'sales_partner': co.user_partner_id.id, 'commission_date': datetime.now().date(), 'source': self.name, 'amount': (comm_filter_par.percentage * self.amount_total)/100}) #, 'commission_id': sheet.id
	
		#########################################################################################
		return res


class CreateCommissionPayment(models.Model):
	_inherit = 'account.payment'  
	
	def post(self):
		res = super(CreateCommissionPayment, self).post()
		for rec in self:
			############################################### Commission calculation on Invoice ########################################################
			if self.env['res.config.settings'].sudo().search([], limit=1, order="id desc").commission_configuration == 'payment':
				commission_line_obj = self.env['sale.commission.line']
				commission_calc_amt = self.env['commission.settings']
				comm_calc_product = self.env['product.template']
				comm_worksheet_obj = self.env['sale.commission.sheet']
				
				commission_product = self.env['product.product'].search([('product_tmpl_id.is_commission_product','=', True)])
				date_1 = (datetime.strptime(str(datetime.now().date()), '%Y-%m-%d')+relativedelta(months =+ 1))
					
				pay_product = []
				for i in rec.invoice_ids:
					for j in i.invoice_line_ids:
						pay_product = j.product_id.product_tmpl_id
					
				pay_product_category = []
				for m in rec.invoice_ids:
					for n in m.invoice_line_ids:
						pay_product_category = n.product_id.product_tmpl_id.categ_id
				
				
				pay_sales_team = []
				for m in rec.invoice_ids:
					pay_sales_team = m.team_id
					
					
				for i in rec.invoice_ids :
					vendor_partner = i.partner_id.id
					break
				for co in rec.product_comm_level_ids:
					commission_calc_on = self.env['res.config.settings'].sudo().search([], limit=1, order="id desc").commission_calc_on
					if commission_calc_on == 'sales_team':
						if co.user_partner_id:
							if co.commission_level_id:
								comm_filter = commission_calc_amt.search([('sales_team_id','=', pay_sales_team.id),('commission_level_id','=', co.commission_level_id.id)])
								commission_line_obj.create({'sales_partner': co.user_partner_id.id, 'commission_date': datetime.now().date(), 'source': rec.name, 'amount': (comm_filter.percentage * rec.amount)/100}) #, 'commission_id': sheet.id
					
					if commission_calc_on == 'product':
						if co.user_partner_id:
							for o_line in rec.invoice_ids[0].invoice_line_ids:

								inv_product = o_line.product_id.product_tmpl_id

								if co.commission_level_id and inv_product.is_commission_product == True:
									comm_filter_p = commission_calc_amt.search([('product_id','=', inv_product.id),('commission_level_id','=', co.commission_level_id.id)])
									
									commission_p_line = commission_line_obj.sudo().search([('source','=',rec.name),('sales_partner','=',co.user_partner_id.id)])

										
									if commission_p_line :
										commission_p_line.write({'amount' : commission_p_line.amount + (comm_filter_p.percentage * rec.amount)/100})
									
									else:
										commission_line_obj.create({'sales_partner': co.user_partner_id.id, 'commission_date': datetime.now().date(), 'source': rec.name, 'amount': (comm_filter_p.percentage * rec.amount)/100}) #, 'commission_id': sheet.id
				
					if commission_calc_on == 'product_category':
						if co.user_partner_id:
							if co.commission_level_id:
								comm_filter_p_c = commission_calc_amt.search([('product_category_id','=', pay_product_category.id),('commission_level_id','=', co.commission_level_id.id)])
								commission_line_obj.create({'sales_partner': co.user_partner_id.id, 'commission_date': datetime.now().date(), 'source': rec.name, 'amount': (comm_filter_p_c.percentage * rec.amount)/100}) #, 'commission_id': sheet.id
					if commission_calc_on == 'partner':
						if co.user_partner_id:
							if co.commission_level_id:
								comm_filter_par = commission_calc_amt.search([('partner_id','=',vendor_partner),('commission_level_id','=', co.commission_level_id.id)])
								commission_line_obj.create({'sales_partner': co.user_partner_id.id, 'commission_date': datetime.now().date(), 'source': rec.name, 'amount': (comm_filter_par.percentage * rec.amount)/100}) #, 'commission_id': sheet.id
			#######################################################################################################
		return res
class PartnerCommissionLine(models.Model):

	_inherit = 'res.partner'   
	
	commission_line_ids = fields.One2many('sale.commission.line','sales_partner', 'Commission Lines')           
		
		
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:        
