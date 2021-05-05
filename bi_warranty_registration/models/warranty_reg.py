# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo import SUPERUSER_ID

class ProductionLot(models.Model):
	_inherit = 'stock.production.lot'

	company_id = fields.Many2one('res.company', string='Company', required=True,stored=True, index=True,
		default=lambda self: self.env.company)

#Warranty Registration Master
class WarrantyDetails(models.Model):
	_name = 'product.warranty'
	_rec_name = 'serial_no'
	_order = 'id desc'
	_description = "Product Warranty"

	def reset_to_new(self):
		self.write({'state':'new'})
	def calc_warranty_end_date(self):
		if self.product_id.warranty_period:
			months_w = int(self.product_id.warranty_period)
			date_1= (datetime.strptime(self.warranty_create_date, '%Y-%m-%d')+relativedelta(months =+ months_w))
			self.update({'warranty_end_date':date_1})
		else:
			self.update({'warranty_end_date': False})


	partner_id = fields.Many2one('res.partner', 'Customer', required=True)
	phone = fields.Char('Phone')
	email = fields.Char('Email')
	comment = fields.Text('Comment')
	accept1 = fields.Boolean("I accept the Terms and Conditions")
	product_id = fields.Many2one('product.product','Product', domain="[('under_warranty', '=', True)]", required=True)
	serial_no = fields.Char('Receipt No.')
	warranty_end_date = fields.Date('Warranty End Date', readonly=True)
	merchant = fields.Char('Merchant')
	renew_no = fields.Integer('No. of Renew', readonly=True)
	warranty_create_date = fields.Date('Warranty Start Date', default=fields.date.today())
	product_serial_id = fields.Many2one('stock.production.lot',"Serial No", domain="[('product_id', '=', product_id)]")
	warranty_history_ids = fields.One2many('warranty.history','warranty_id','Warranty History', readonly=True)
	warranty_type = fields.Selection([('free','Free'),('paid','Paid')], string="Warranty Type", default='free')
	warranty_team = fields.Many2one('crm.team', domain="[('use_warranty', '=', True)]", string="Warranty Team")
	tags_w = fields.Many2many('warranty.tag', string='Tags')
	model_no = fields.Char('Model #')
	warranty_cost = fields.Float('Renewal Amount')
	warranty_claim_ids = fields.One2many('warranty.claim','warranty','Claims', readonly=True)
	warranty_sales_person = fields.Many2one('res.users','Salesperson', default=lambda self: self.env.user)
	state = fields.Selection([('new','New'),('in_progress','Under Warranty'),('to_be_invoice','To Be Invoice'),('invoiced','Invoiced'),('to_renew','To Be Renew'),('expired','Expired')], default='new', string='State')

	so_id = fields.Many2one('sale.order',"Sale Order")
	company_id = fields.Many2one('res.company', 'Company')
	viechle_id = fields.Many2one('fleet.vehicle')
	size = fields.Char(string="Car Size")
	model_id = fields.Many2one('fleet.model')

	@api.onchange('partner_id')
	def customer_details(self):
		if self.partner_id:
			self.update({'phone': self.partner_id.phone, 'email': self.partner_id.email,})

	@api.onchange('product_serial_id')
	def check_warranty_serial(self):
		warranty_obj = self.env['product.warranty'].search([])
		for ser in warranty_obj:
			if ser.product_serial_id == self.product_serial_id:
				raise ValidationError(_('You Cannot Create more than one Warranty with same serial No. Please Renew existing Warranty'))

	def action_view_invoice(self):
		action = self.env.ref('bi_warranty_registration.action_warranty_invoice_tree1').read()[0]
		return action

	def _create_invoice(self):
		self.update({'state':"invoiced"})
		inv_obj = self.env['account.move']


		account_id = False
		name = _('Warranty')
		if self.product_id.id:
			if not self.product_id.property_account_income_id:
				account_id = self.product_id.categ_id.property_account_income_categ_id.id
			else:
				account_id = self.product_id.property_account_income_id.id

		invoice = inv_obj.create({
			'invoice_origin': self.serial_no,
			'type': 'out_invoice',
			'ref': False,
			'partner_id': self.partner_id.id,
			'warranty_invoice': True,
			'warranty_reg_id': self.id,
			'invoice_line_ids': [(0, 0, {
										'name': 'Warranty of '+ str(self.product_id.display_name),
										'product_id': self.product_id.id,
										'price_unit': self.warranty_cost,
										})],

			'narration': self.comment,
		})

		return invoice

	def state_renew(self):
		if self.renew_no < self.product_id.warranty_renewal_time:
			self.update({'renew_no': self.renew_no + 1})
			self.update({'warranty_create_date': self.warranty_end_date,'state': 'renew'})

			months_w = int(self.product_id.warranty_period)
			date_1= (datetime.strptime(self.warranty_create_date, '%Y-%m-%d')+relativedelta(months =+ months_w))
			self.update({'warranty_end_date':date_1})

			renew_history_obj = self.env['warranty.history']

			if self.warranty_type == 'free':

				renew_history_obj.create({
					'date_renewal' : datetime.now(),
					'warranty_renewal_date': self.warranty_end_date,
					'warranty_renew_end_date': date_1,
					'warranty_id':self.id,
					'free': True,
				})
			if self.warranty_type == 'paid':
				renew_history_obj.create({
					'date_renewal' : datetime.now(),
					'warranty_renewal_date': self.warranty_end_date,
					'warranty_renew_end_date': date_1,
					'renewal_cost': self.product_id.warranty_renewal_cost,
					'warranty_id':self.id,
					'paid': True,
				})
		else:
			raise UserError(_('Maximun Renewal Times Exceeded'))

	def create_invoice(self):
		self._create_invoice()

		return self.action_view_invoice()


	@api.model
	def warranty_expiry_scheduler_queue(self):
		warranty_obj = self.env['product.warranty'].search([("state",'!=','new')])
		for scheduler in warranty_obj :
			warranty_end = datetime.strptime(str(scheduler.warranty_end_date), DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
			if warranty_end < str(datetime.now().date()):
				scheduler.update({"state":'expired'})

	@api.model
	def warranty_renew_scheduler(self):

		warranty_renew_obj = self.env['product.warranty'].search([])
		#days_w = 15
		days_w = self.env['warranty.settings'].search([],order="id desc", limit=1).renew_notif

		date_to_renew= (datetime.strptime(str(datetime.now().date()), '%Y-%m-%d')+relativedelta(days =+ int(days_w)))
		date_to_renew = date_to_renew.date()

		manager_id = self.env['ir.model.data'].sudo().get_object_reference('base','group_system')[1]
		group_manager = self.env['res.groups'].sudo().browse(manager_id)
		super_user = group_manager.users[0]

		if not group_manager.users:
			internal_user_id = self.env['ir.model.data'].sudo().get_object_reference('base','group_user')[1]
			group_internal_user = self.env['res.groups'].sudo().browse(internal_user_id)
			super_user = group_internal_user.users[0]

		for renew_sch in warranty_renew_obj:
			if renew_sch.warranty_end_date == date_to_renew:
				renew_sch.update({"state":'to_renew'})
				template_id = self.env['ir.model.data'].get_object_reference('bi_warranty_registration', 'email_template_warranty_renew')[1]
				email_template_obj = self.env['mail.template'].browse(template_id)
				values = email_template_obj.generate_email(renew_sch.id)
				values['email_from'] = super_user.partner_id.email
				values['email_to'] = renew_sch.partner_id.email
				values['res_id'] = renew_sch.id
				values['author_id'] = super_user.partner_id.id
				mail_mail_obj = self.env['mail.mail']
				msg_id = mail_mail_obj.create(values)
				if msg_id:

					mail_mail_obj.send([msg_id])
		warranty_renew_obj = self.env['product.warranty'].search([])
		days_w = 15
		date_to_renew= (datetime.strptime(str(datetime.now().date()), '%Y-%m-%d')+relativedelta(days =+ days_w))
		for renew_sch in warranty_renew_obj:
			if renew_sch.warranty_end_date == date_to_renew:
				renew_sch.update({"state":'to_renew'})


	@api.onchange('product_serial_id')
	def lot_update_date(self):
		if self.warranty_create_date and self.warranty_end_date:
			self.product_serial_id.write({'start_date_warranty': self.warranty_create_date, 'end_date_warranty': self.warranty_end_date})

	@api.model
	def create(self, vals):
		vals['serial_no'] = self.env['ir.sequence'].next_by_code('warranty.serial') or 'New'
		result = super(WarrantyDetails, self).create(vals)
		# warranty_obj = self.env['product.warranty'].search([])
		# for ser in warranty_obj:
		# 	if ser.id != result.id:
		# 		if ser.product_serial_id == result.product_serial_id:
		# 			raise ValidationError(_('You Cannot Create more than one Warranty with same serial No. Please Renew existing Warranty'))
		#

		return result

	@api.onchange('product_id','warranty_type')
	def product_cost_warranty(self):
		self.update({'warranty_cost': self.product_id.warranty_renewal_cost})

	def state_update(self):

		template = self.env.ref('bi_warranty_registration.email_template_warranty_registration')
		self.env['mail.template'].browse(template.id).send_mail(self.id)

		if self.product_id.warranty_period:
			months_w = int(self.product_id.warranty_period)
			date_1= (datetime.strptime(str(self.warranty_create_date), '%Y-%m-%d').date()+relativedelta(months =+ months_w))

			self.update({'warranty_end_date':date_1})
			self.product_serial_id.update({'start_date_warranty': self.warranty_create_date, 'end_date_warranty': date_1, 'renewal_times': self.renew_no})
		else:
			self.update({'warranty_end_date': False})


		confirm_history_obj = self.env['warranty.history']
		if self.warranty_type == 'free':
			self.update({'state': 'in_progress'})
			confirm_history_obj.create({
				'date_renewal' : datetime.now(),
				'warranty_renewal_date': self.warranty_create_date,
				'warranty_renew_end_date': self.warranty_end_date,
				'warranty_id':self.id,
				'free': True

			})
		if self.warranty_type == 'paid':
			self.update({'state': 'to_be_invoice'})
			confirm_history_obj.create({
				'date_renewal' : datetime.now(),
				'warranty_renewal_date': self.warranty_create_date,
				'warranty_renew_end_date': self.warranty_end_date,
				'renewal_cost': self.warranty_cost,
				'warranty_id':self.id,
				'paid': True

			})




#Warranty Start and end date in lot
class StartWarrantyLot(models.Model):
	_inherit = 'stock.production.lot'

	start_date_warranty = fields.Date('Warranty Start Date')
	end_date_warranty = fields.Date('Warranty End Date')
	renewal_times = fields.Integer('No. of Renew')


#Warranty Tags
class WarrantyTag(models.Model):
	_name = 'warranty.tag'
	_rec_name = 'tag_name'
	_description = "Warranty Tag"

	tag_name = fields.Char('Tag Name')
	tag_desc = fields.Char('Description')


#Warranty Team
class WarrantyTeam(models.Model):
	_inherit = 'crm.team'

	use_warranty = fields.Boolean("Warranty")


#Warranty Settings form
class WarrantySettings(models.Model):
	_name = 'warranty.settings'
	_inherit = 'res.config.settings'
	_rec_name = 'setting_desc'
	_description = "Warranty Settings"

	@api.model
	def default_get(self, flds):
		result = super(WarrantySettings, self).default_get(flds)
		warranty_notif = self.env['ir.model.data'].xmlid_to_object('bi_warranty_registration.email_template_warranty_registration')
		renew_notif = self.env['ir.model.data'].xmlid_to_object('bi_warranty_registration.email_template_warranty_renew')
		create_warranty_from_saleorder = self.env['ir.config_parameter'].sudo().get_param('bi_warranty_registration.create_warranty_from_saleorder')
		renew_notif_interval = self.env['ir.config_parameter'].sudo().get_param('bi_warranty_registration.renew_notif')

		result['warranty_tmpl'] = warranty_notif.id
		result['renew_tmpl'] = renew_notif.id
		result['create_warranty_from_saleorder'] = create_warranty_from_saleorder
		result['renew_notif'] = renew_notif_interval
		return result

	renew_notif = fields.Char("Renew Notification Submit Interval")
	setting_desc = fields.Char('Description')
	warranty_tmpl = fields.Many2one('mail.template', 'Warranty Registration mail template')
	renew_tmpl = fields.Many2one('mail.template', 'Warranty Renew mail template')
	company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
	create_warranty_from_saleorder = fields.Boolean('Create Warranty from Sale Order')


	def set_values(self):
		super(WarrantySettings,self).set_values()
		self.env['ir.config_parameter'].sudo().set_param('bi_warranty_registration.renew_notif', self.renew_notif)
		self.env['ir.config_parameter'].sudo().set_param('bi_warranty_registration.create_warranty_from_saleorder', self.create_warranty_from_saleorder)
		module = False
		if self.create_warranty_from_saleorder == True :
			module = self.env['ir.module.module'].search([('state', '!=', 'installed'),('name', '=', 'v9_sale_invoice_serial')])
		if module :
			module.button_immediate_install()




#Warranty History Details
class WarrantyHistory(models.Model):
	_name = "warranty.history"
	_description = "Warranty History"

	date_renewal = fields.Date('Date')
	warranty_renewal_date = fields.Date('Warranty Start Date')
	warranty_renew_end_date = fields.Date('Warranty End Date')
	renewal_cost = fields.Float('Renewal Amount')
	paid = fields.Boolean('Paid')
	free = fields.Boolean('Free')
	warranty_id = fields.Many2one('product.warranty','Warranty')


#Warranty Invoice Validation and state of warranty becomes under warranty
class WarrantyInvoice(models.Model):
	_inherit = 'account.move'

	warranty_invoice = fields.Boolean('Warranty Renew Invoice')
	warranty_reg_id = fields.Many2one('product.warranty', 'Warranty')

	def action_post(self):
		self.warranty_reg_id.update({'state': 'in_progress'})
		if self.mapped('line_ids.payment_id') and any(post_at == 'bank_rec' for post_at in self.mapped('journal_id.post_at')):
			raise UserError(_("A payment journal entry generated in a journal configured to post entries only when payments are reconciled with a bank statement cannot be manually posted. Those will be posted automatically after performing the bank reconciliation."))
		return self.post()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
