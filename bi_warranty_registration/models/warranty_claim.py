# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import html2plaintext
import odoo.addons.decimal_precision as dp

class crm_claim_stage(models.Model):
	_name = "warranty.claim.stage"
	_description = "Claim stages"
	_rec_name = 'name'
	_order = "sequence"

	name = fields.Char('Stage Name', required=True, translate=True)
	sequence = fields.Integer('Sequence', help="Used to order stages. Lower is better.",default=lambda *args: 1)
	team_ids = fields.Many2many('crm.team', 'crm_team_claim_stage_rel', 'stage_id', 'team_id', string='Teams',
						help="Link between stages and sales teams. When set, this limitate the current stage to the selected sales teams.")
	case_default = fields.Boolean('Common to All Teams',
						help="If you check this field, this stage will be proposed by default on each sales team. It will not assign this stage to existing teams.")

	_defaults = {
		'sequence': lambda *args: 1
	}


class crm_claim(models.Model):
	_name = "warranty.claim"
	_description = "Claim"
	_order = "priority,date desc"

	@api.model
	def default_get(self, flds):
		result = super(crm_claim, self).default_get(flds)
		stage_nxt1 = self.env['ir.model.data'].xmlid_to_object('bi_warranty_registration.stage_claim1')
		result['stage_id'] = stage_nxt1.id
		return result

	id = fields.Integer('ID', readonly=True)
	name = fields.Char('Claim Subject', required=True)
	active = fields.Boolean('Active',default=lambda *a: 1)
	action_next = fields.Char('Next Action')
	date_action_next = fields.Datetime('Next Action Date')
	description = fields.Text('Description')
	resolution = fields.Text('Resolution')
	create_date = fields.Datetime('Creation Date' , readonly=True)
	write_date = fields.Datetime('Update Date' , readonly=True)
	date_deadline = fields.Date('Deadline')
	date_closed = fields.Datetime('Closed', readonly=True)
	date = fields.Datetime('Claim Date', index=True,default=fields.datetime.now())
	categ_id = fields.Many2one('warranty.claim.category', 'Category')
	priority = fields.Selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority',default='1')
	type_action = fields.Selection([('correction','Corrective Action'),('prevention','Preventive Action')], 'Action Type')
	user_id = fields.Many2one('res.users', 'Responsible', track_visibility='always',default=lambda self: self.env.user)
	user_fault = fields.Char('Trouble Responsible')
	team_id = fields.Many2one('crm.team', 'Sales Team',\
						index=True, help="Responsible sales team."\
								" Define Responsible user and Email account for"\
								" mail gateway.")
	company_id = fields.Many2one('res.company', 'Company',default=lambda self: self.env['res.company'])
	partner_id = fields.Many2one('res.partner', 'Customer')
	email_cc = fields.Text('Watchers Emails', size=252, help="These email addresses will be added to the CC field of all inbound and outbound emails for this record before being sent. Separate multiple email addresses with a comma")
	email_from = fields.Char('Email', size=128, help="Destination email for email gateway.")
	partner_phone = fields.Char('Phone')
	stage_id = fields.Many2one ('warranty.claim.stage', 'Stage', track_visibility='onchange', index=True)
	cause = fields.Text('Root Cause')
	product_id = fields.Many2one('product.product', 'Product', domain="[('under_warranty', '=', True)]", required=True)
	serial_no = fields.Many2one('stock.production.lot',"Serial No", domain="[('product_id', '=', product_id)]")
	warranty = fields.Many2one('product.warranty','Related Warranty')
	stage_match = fields.Selection([('first','first'), ('second','second'), ('third','third'),('fourth','fourth')], 'Stage Match', default='first')
	viechle_id = fields.Many2one('fleet.veichle')
	size = fields.Char(string="Car Size")
	model_id = fields.Many2one('fleet.model')

	so_referance = fields.Many2one('sale.order')
	sale_order_referance = fields.Many2one('sale.order')
	@api.onchange('sale_order_referance')
	def get_partner_customer(self):
		if self.sale_order_referance:
			self.partner_id = self.sale_order_referance.partner_id.id
			self.customer_details()
			self.warranty_updt_prod()

	@api.onchange('partner_id')
	def customer_details(self):
		self.partner_phone = self.partner_id.phone
		self.email_from = self.partner_id.email
		warranty_claim_obj = self.env['product.warranty'].search([('partner_id','=',self.partner_id.id),('state','not in',['expired','new'])])
		prod = []
		if warranty_claim_obj:
			for i in warranty_claim_obj:
				prod.append(i.product_id.id)
		self.warranty_updt_prod()
		return {'domain': {'product_id': [('id', 'in', prod)]}}

	@api.onchange('product_id')
	def warranty_updt_prod(self):
		warranty_claim_obj = self.env['product.warranty'].search([('partner_id','=',self.partner_id.id),('product_id','=',self.product_id.id),('state','not in',['expired','new'])])
		prod = []
		if warranty_claim_obj:
			for i in warranty_claim_obj:
				prod.append(i.product_serial_id.id)
		return {'domain': {'serial_no': [('id', 'in',prod)]}}


	@api.onchange('serial_no')
	def warranty_updt_serial(self):
		warranty_claim_obj = self.env['product.warranty'].search([])
		for res in warranty_claim_obj:
			if res.product_serial_id == self.serial_no:
				self.update({'warranty': res.id})

	def submit_claim(self):
		if self.serial_no:
			warranty_obj = self.env['product.warranty'].search([('product_serial_id','=', self.serial_no.id)])
			if not warranty_obj:
					raise ValidationError(_('Warranty is not created for this product'))
			else:
				stage_nxt = self.env['ir.model.data'].xmlid_to_object('bi_warranty_registration.stage_claim5')
				self.update({'stage_id': stage_nxt.id, 'stage_match': 'second'})


			if warranty_obj:
				if warranty_obj.state == 'new':
					raise ValidationError(_('Warranty is not confirmed for this product'))

			if warranty_obj:
				if warranty_obj.warranty_end_date :
					if fields.datetime.today().date() > warranty_obj.warranty_end_date :
						raise ValidationError(_('Warranty is expired for this product'))
		else:
			raise ValidationError(_('Empty Serial Number'))

	def completed_claim(self):
		stage_nxt1 = self.env['ir.model.data'].xmlid_to_object('bi_warranty_registration.stage_claim2')
		self.update({'stage_id': stage_nxt1.id, 'stage_match': 'third'})

	def claim_done(self):
		stage_nxt2 = self.env['ir.model.data'].xmlid_to_object('bi_warranty_registration.stage_claim3')
		self.update({'stage_id': stage_nxt2.id, 'stage_match': 'fourth'})


	@api.model
	def create(self, vals):
		context = dict(self._context or {})
		if vals.get('team_id') and not self._context.get('default_team_id'):
			context['default_team_id'] = vals.get('team_id')

		# context: no_log, because subtype already handle this
		return super(crm_claim, self).create(vals)


class crm_claim_category(models.Model):
	_name = "warranty.claim.category"
	_description = "Category of claim"

	name = fields.Char('Name', required=True, translate=True)
	team_id = fields.Many2one('crm.team', 'Sales Team')
