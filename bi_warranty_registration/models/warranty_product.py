# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo import api, fields, models, tools, _
import psycopg2
import itertools
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, Warning, except_orm
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


class product_template(models.Model):
	_inherit = 'product.template'
	
	under_warranty = fields.Boolean('Under Warranty')
	warranty_period = fields.Integer("Warranty Period")
	allow_renewal = fields.Boolean('Allow Renewal')
	warranty_renewal_time = fields.Integer("Allow Warranty Renewal Times ")
	warranty_renewal_period = fields.Integer("Warranty Renewal Period")
	warranty_renewal_cost = fields.Float("Warranty renewal Cost")
	create_warranty_with_saleorder = fields.Boolean('Create Warranty from Sale Order')
	warranty_sale_config = fields.Boolean(compute ='_compute_sale_warranty')

	

	def _compute_sale_warranty(self):

		tmp = self.env['warranty.settings'].search([],order="id desc", limit=1).create_warranty_from_saleorder
		for line in self :
			line.warranty_sale_config = tmp
		return 

	def write(self, vals):
		# tools.image_resize_images(vals)
		res = super(product_template, self).write(vals)
		product_product = self.env['product.product'].search([('product_tmpl_id','=',self.id)])

		
		
		if 'under_warranty' in vals :
			for line in product_product :
				line.under_warranty = vals['under_warranty']

		if 'warranty_period' in vals :
			for line in product_product :
				line.warranty_period = vals['warranty_period']


		if 'allow_renewal' in vals :
			for line in product_product :
				line.allow_renewal = vals['allow_renewal']



		if 'warranty_renewal_time' in vals :
			for line in product_product :
				line.warranty_renewal_time = vals['warranty_renewal_time']


		if 'warranty_renewal_period' in vals :
			for line in product_product :
				line.warranty_renewal_period = vals['warranty_renewal_period']

		if 'warranty_renewal_cost' in vals :
			for line in product_product :
				line.warranty_renewal_cost = vals['warranty_renewal_cost']

		if 'create_warranty_with_saleorder' in vals :
			for line in product_product :
				line.create_warranty_with_saleorder = vals['create_warranty_with_saleorder']

		return res

	def create_variant_ids(self):
		Product = self.env["product.product"]
		AttributeValues = self.env['product.attribute.value']
		for tmpl_id in self.with_context(active_test=False):
			
			# adding an attribute with only one value should not recreate product
			# write this attribute on every product to make sure we don't lose them
			variant_alone = tmpl_id.attribute_line_ids.filtered(lambda line: len(line.value_ids) == 1).mapped('value_ids')
			for value_id in variant_alone:
				
				updated_products = tmpl_id.product_variant_ids.filtered(lambda product: value_id.attribute_id not in product.mapped('attribute_value_ids.attribute_id'))
				updated_products.write({'attribute_value_ids': [(4, value_id.id)],
					'under_warranty':tmpl_id.under_warranty,
					'warranty_period' : tmpl_id.warranty_period,
					'allow_renewal' :  tmpl_id.allow_renewal,
					'warranty_renewal_time' :  tmpl_id.warranty_renewal_time,
					'warranty_renewal_period' :tmpl_id.warranty_renewal_period,
					'warranty_renewal_cost' : tmpl_id.warranty_renewal_cost,
					'create_warranty_with_saleorder' : tmpl_id.create_warranty_with_saleorder,
				
				})

			# iterator of n-uple of product.attribute.value *ids*
			variant_matrix = [
				AttributeValues.browse(value_ids)
				for value_ids in itertools.product(*(line.value_ids.ids for line in tmpl_id.attribute_line_ids if line.value_ids[:1].attribute_id.create_variant))
			]

			# get the value (id) sets of existing variants
			existing_variants = {frozenset(variant.attribute_value_ids.ids) for variant in tmpl_id.product_variant_ids}
			# -> for each value set, create a recordset of values to create a
			#    variant for if the value set isn't already a variant
			to_create_variants = [
				value_ids
				for value_ids in variant_matrix
				if set(value_ids.ids) not in existing_variants
			]

			# check product
			variants_to_activate = self.env['product.product']
			variants_to_unlink = self.env['product.product']
			for product_id in tmpl_id.product_variant_ids:
				if not product_id.active and product_id.attribute_value_ids.filtered(lambda r: r.attribute_id.create_variant) in variant_matrix:
					variants_to_activate |= product_id
				elif product_id.attribute_value_ids.filtered(lambda r: r.attribute_id.create_variant) not in variant_matrix:
					variants_to_unlink |= product_id
			if variants_to_activate:
				variants_to_activate.write({'active': True})

			# create new product
			for variant_ids in to_create_variants:
				
				new_variant = Product.create({
					'product_tmpl_id': tmpl_id.id,
					'attribute_value_ids': [(6, 0, variant_ids.ids)],
					'under_warranty':tmpl_id.under_warranty,
					'warranty_period' : tmpl_id.warranty_period,
					'allow_renewal' :  tmpl_id.allow_renewal,
					'warranty_renewal_time' :  tmpl_id.warranty_renewal_time,
					'warranty_renewal_period' :tmpl_id.warranty_renewal_period,
					'warranty_renewal_cost' : tmpl_id.warranty_renewal_cost,
					'create_warranty_with_saleorder' : tmpl_id.create_warranty_with_saleorder,
				})

			# unlink or inactive product
			for variant in variants_to_unlink:
				try:
					with self._cr.savepoint(), tools.mute_logger('odoo.sql_db'):
						variant.unlink()
				# We catch all kind of exception to be sure that the operation doesn't fail.
				except (psycopg2.Error, except_orm):
					variant.write({'active': False})
					pass
		return True



class product_product(models.Model):
	_inherit = 'product.product'
	
	under_warranty = fields.Boolean('Under Warranty')
	warranty_period = fields.Integer("Warranty Period")
	allow_renewal = fields.Boolean('Allow Renewal')
	warranty_renewal_time = fields.Integer("Allow Warranty Renewal Times ")
	warranty_renewal_period = fields.Integer("Warranty Renewal Period")
	warranty_renewal_cost = fields.Float("Warranty renewal Cost")
	create_warranty_with_saleorder = fields.Boolean('Create Warranty from Sale Order')
	warranty_sale_config = fields.Boolean(compute ='_compute_sale_warranty')

	
	def _compute_sale_warranty(self):

		tmp = self.env['warranty.settings'].search([],order="id desc", limit=1).create_warranty_from_saleorder
		for line in self :
			line.warranty_sale_config = tmp


	@api.model
	def create(self, vals) :
		res = super(product_product,self).create(vals)
		template = res.product_tmpl_id
		if template :
			res.under_warranty = template.under_warranty
			res.warranty_period = template.warranty_period
			res.allow_renewal = template.allow_renewal

			res.warranty_renewal_time = template.warranty_renewal_time
			res.warranty_renewal_period = template.warranty_renewal_period
			res.warranty_renewal_cost = template.warranty_renewal_cost
			res.create_warranty_with_saleorder = template.create_warranty_with_saleorder


		return res



