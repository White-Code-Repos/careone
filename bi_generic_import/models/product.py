# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import tempfile
import binascii
import xlrd
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
import time
from datetime import date, datetime
import io
import logging
_logger = logging.getLogger(__name__)

try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')
try:
	import xlwt
except ImportError:
	_logger.debug('Cannot `import xlwt`.')
try:
	import cStringIO
except ImportError:
	_logger.debug('Cannot `import cStringIO`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')

class gen_product(models.TransientModel):
	_name = "gen.product"

	file = fields.Binary('File',required=True)
	product_option = fields.Selection([('create','Create Product'),('update','Update Product')],string='Option', required=True,default="create")
	product_search = fields.Selection([('by_code','Search By Code'),('by_name','Search By Name'),('by_barcode','Search By Barcode')],string='Search Product')
	with_variant = fields.Boolean(string="Import Variants")
	import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='xls')

	def create_product(self, values):
		product_obj = self.env['product.product']
		product_categ_obj = self.env['product.category']
		product_uom_obj = self.env['uom.uom']
		if values.get('categ_id')=='':
			raise Warning(_('CATEGORY field can not be empty'))
		else:
			categ_id = product_categ_obj.search([('name','=',values.get('categ_id'))],limit=1)
			if not categ_id:
				raise Warning(_('Category %s not found.' %values.get('categ_id') ))
		
		if values.get('type') == 'Consumable':
			categ_type ='consu'
		elif values.get('type') == 'Service':
			categ_type ='service'
		elif values.get('type') == 'Storable Product':
			categ_type ='product'
		else:
			categ_type = 'product'
		
		if values.get('uom_id')=='':
			uom_id = 1
		else:
			uom_search_id  = product_uom_obj.search([('name','=',values.get('uom_id'))])
			if not uom_search_id:
				raise Warning(_('UOM %s not found.' %values.get('uom_id') ))
			uom_id = uom_search_id.id
		
		if values.get('uom_po_id')=='':
			uom_po_id = 1
		else:
			uom_po_search_id  = product_uom_obj.search([('name','=',values.get('uom_po_id'))])
			if not uom_po_search_id:
				raise Warning(_('Purchase UOM %s not found' %values.get('uom_po_id') ))
			uom_po_id = uom_po_search_id.id
		
		if values.get('barcode') == '':
			barcode = False
		else:
			barcode = values.get('barcode').split(".")	
			barcode = barcode[0]

		tax_id_lst = []
		if values.get('taxes_id'):
			if ';' in values.get('taxes_id'):
				tax_names = values.get('taxes_id').split(';')
				for name in tax_names:
					tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'sale')])
					if not tax:
						raise Warning(_('"%s" Tax not in your system') % name)
					tax_id_lst.append(tax.id)

			elif ',' in values.get('taxes_id'):
				tax_names = values.get('taxes_id').split(',')
				for name in tax_names:
					tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'sale')])
					if not tax:
						raise Warning(_('"%s" Tax not in your system') % name)
					tax_id_lst.append(tax.id)

			else:
				tax_names = values.get('taxes_id').split(',')
				tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'sale')])
				if not tax:
					raise Warning(_('"%s" Tax not in your system') % tax_names)
				tax_id_lst.append(tax.id)

		supplier_taxes_id = []
		if values.get('supplier_taxes_id'):
			if ';' in values.get('supplier_taxes_id'):
				tax_names = values.get('supplier_taxes_id').split(';')
				for name in tax_names:
					tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
					if not tax:
						raise Warning(_('"%s" Tax not in your system') % name)
					supplier_taxes_id.append(tax.id)

			elif ',' in values.get('supplier_taxes_id'):
				tax_names = values.get('supplier_taxes_id').split(',')
				for name in tax_names:
					tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
					if not tax:
						raise Warning(_('"%s" Tax not in your system') % name)
					supplier_taxes_id.append(tax.id)

			else:
				tax_names = values.get('supplier_taxes_id').split(',')
				tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'purchase')])
				if not tax:
					raise Warning(_('"%s" Tax not in your system') % tax_names)
				supplier_taxes_id.append(tax.id) 

		if (values.get('tracking') == 'By Lots') and (categ_type == 'product'):
			tracking = 'lot'
		elif (values.get('tracking') == 'By Unique Serial Number') and (categ_type == 'product'):
			tracking = 'serial'
		else:
			tracking = 'none'
		vals = {
				  'name':values.get('name'),
				  'default_code':values.get('default_code'),
				  'categ_id':categ_id[0].id,
				  'type':categ_type,
				  'barcode':barcode,
				  'uom_id':uom_id,
				  'uom_po_id':uom_po_id,
				  'lst_price':values.get('sale_price'),
				  'standard_price':values.get('cost_price'),
				  'weight':values.get('weight'),
				  'volume':values.get('volume'),
				  'taxes_id':[(6,0,tax_id_lst)],
				  'supplier_taxes_id':[(6,0,supplier_taxes_id)],
				  'tracking': tracking, 
			  }
		
		if self.with_variant and self.product_option == 'create':
			vals.update({'attribute_line_ids':[] })
			if values.get('attributes'):
				atr_value = values.get('attributes').split('#')

				for pair in atr_value:
					temp = pair.split(':')
					attr = temp[0]
					attr_values = temp[1].split(';')
					val_list = []
					
					
					for att in attr_values:
						if att == '':
							raise Warning(_('Please give the values after ;'))
					
					attribute = self.env['product.attribute'].search([['name','=',attr]],limit=1)
					if not attribute:
						if attr in ('color','colour','Color','Colour'):
							attribute = self.env['product.attribute'].create({'name': 'Color','type':'color'})
						else:
							attribute = self.env['product.attribute'].create({'name': attr})                              

					for val in attr_values:
						attribute_value = self.env['product.attribute.value'].search([['name','=',val]],limit=1)
						if not attribute_value:
							if attr in ('color','colour','Color','Colour'):
								attribute_value = self.env['product.attribute.value'].create({
									'name':val,
									'attribute_id':attribute.id,
									'html_color':val.lower(), 
								})
							else:
								attribute_value = self.env['product.attribute.value'].create({
									'name':val,
									'attribute_id':attribute.id 
									})
						
						
						attribute_value = self.env['product.attribute.value'].search([('name','=',val), ('attribute_id', '=', attr)], limit=1)
						if not attribute_value:
							if attribute_value.attribute_id.name != attr:
								attribute_value = self.env['product.attribute.value'].create({
                                        'name':val,
                                        'attribute_id':attribute.id 
                                        })
								
						val_list.append(attribute_value.id)

					vals['attribute_line_ids'].append((0,0,{
							'attribute_id':attribute.id,
							'value_ids':[(6,0,val_list)]
							}))

				res = self.env['product.template'].create(vals)
				res._create_variant_ids()
				for var in res.product_variant_ids:
					var.write({
						'lst_price':values.get('sale_price'),
						'standard_price':values.get('cost_price'),
						'weight':values.get('weight'),
						'volume':values.get('volume'),
						})
				return res


		res = product_obj.create(vals)

		return res

	def import_product(self):



		if self.import_option == 'csv':
			res = {}
			keys = ['name', 'default_code','categ_id','type','barcode','uom_id', 'uom_po_id','sale_price',
										'cost_price',
										'weight',
										'volume',
										'taxes_id',
										'supplier_taxes_id',
										'tracking']
			if self.with_variant:
				keys.append('attributes')
			try:
				csv_data = base64.b64decode(self.file)
				data_file = io.StringIO(csv_data.decode("utf-8"))
				data_file.seek(0)
				file_reader = []
				csv_reader = csv.reader(data_file, delimiter=',')
				file_reader.extend(csv_reader)
			except Exception:
				raise exceptions.Warning(_("Invalid file!"))
			values = {}
			
			for i in range(len(file_reader)):
				field = list(map(str, file_reader[i]))
				values = dict(zip(keys, field))
				
				if values:
					if i == 0:
						continue
					else:
						if self.product_option == 'create':
							
							res = self.create_product(values)
							
						else : 

							product_obj = self.env['product.product']
							product_categ_obj = self.env['product.category']
							product_uom_obj = self.env['uom.uom']
							categ_id = False
							categ_type = False
							barcode = False
							uom_id = False
							uom_po_id = False
							if values.get('categ_id')=='':
								pass
							else:
								categ_id = product_categ_obj.search([('name','=',values.get('categ_id'))],limit=1)
								if not categ_id:
									raise Warning(_('Category %s not found.' %values.get('categ_id') ))
							if values.get('type')=='':
								pass
							else:
								if values.get('type') == 'Consumable':
									categ_type ='consu'
								elif values.get('type') == 'Service':
									categ_type ='service'
								elif values.get('type') == 'Stockable Product':
									categ_type ='product'
								else:
									categ_type = 'product'
									
							if values.get('barcode')=='':                             
								pass
							else:
								barcode = values.get('barcode').split(".")
							
							if values.get('uom_id')=='':
								pass
							else:
								uom_search_id  = product_uom_obj.search([('name','=',values.get('uom_id'))])
								if not uom_search_id:
									raise Warning(_('UOM %s not found.' %values.get('uom_id')))
								else:
									uom_id = uom_search_id.id
							
							if values.get('uom_po_id')=='':
								pass
							else:
								uom_po_search_id  = product_uom_obj.search([('name','=',values.get('uom_po_id'))])
								if not uom_po_search_id:
									raise Warning(_('Purchase UOM %s not found' %values.get('uom_po_id')))
								else:
									uom_po_id = uom_po_search_id.id
							
							tax_id_lst = []
							if values.get('taxes_id'):
								if ';' in values.get('taxes_id'):
									tax_names = values.get('taxes_id').split(';')
									for name in tax_names:
										tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'sale')])
										if not tax:
											raise Warning(_('"%s" Tax not in your system') % name)
										tax_id_lst.append(tax.id)

								elif ',' in values.get('taxes_id'):
									tax_names = values.get('taxes_id').split(',')
									for name in tax_names:
										tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'sale')])
										if not tax:
											raise Warning(_('"%s" Tax not in your system') % name)
										tax_id_lst.append(tax.id)

								else:
									tax_names = values.get('taxes_id').split(',')
									tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'sale')])
									if not tax:
										raise Warning(_('"%s" Tax not in your system') % tax_names)
									tax_id_lst.append(tax.id)

							supplier_taxes_id = []

							if values.get('supplier_taxes_id'):
								if ';' in values.get('supplier_taxes_id'):
									tax_names = values.get('supplier_taxes_id').split(';')
									for name in tax_names:
										tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
										if not tax:
											raise Warning(_('"%s" Tax not in your system') % name)
										supplier_taxes_id.append(tax.id)

								elif ',' in values.get('supplier_taxes_id'):
									tax_names = values.get('supplier_taxes_id').split(',')
									for name in tax_names:
										tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
										if not tax:
											raise Warning(_('"%s" Tax not in your system') % name)
										supplier_taxes_id.append(tax.id)

								else:
									tax_names = values.get('supplier_taxes_id').split(',')
									tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'purchase')])
									if not tax:
										raise Warning(_('"%s" Tax not in your system') % tax_names)
									supplier_taxes_id.append(tax.id)

							if (values.get('tracking') == 'By Lots') and (categ_type == 'product'):
								tracking = 'lot'
							elif (values.get('tracking') == 'By Unique Serial Number') and (categ_type == 'product'):
								tracking = 'serial'
							else:
								tracking = 'none'

							if self.product_search == 'by_code':

								if not values.get('default_code'):
									raise Warning(_('Please give Internal Reference for updating Products'))

								product_ids = self.env['product.template'].search([('default_code','=', values.get('default_code'))],limit=1)

								if product_ids:
									if categ_id != False:
										product_ids.write({'categ_id': categ_id[0].id or False})
									if categ_type != False:
										product_ids.write({'type': categ_type or False})
									if barcode != False:
										product_ids.write({'barcode': barcode[0] or False})
									if uom_id != False:
										product_ids.write({'uom_id': uom_id or False})
									if uom_po_id != False:
										product_ids.write({'uom_po_id': uom_po_id})
									if values.get('name'):
										product_ids.write({'name': values.get('name') or False})

									if values.get('sale_price'):
										product_ids.write({'lst_price': values.get('sale_price') or False})
									if values.get('cost_price'):
										product_ids.write({'standard_price': values.get('cost_price') or False})
									if values.get('weight'):
										product_ids.write({'weight': values.get('weight') or False})
									if values.get('volume'):
										product_ids.write({'volume': values.get('volume') or False})


									product_ids.write({
										'taxes_id':[(6,0,tax_id_lst)],
										'supplier_taxes_id':[(6,0,supplier_taxes_id)],
										'tracking': tracking,
										})
								else:
									raise Warning(_('"%s" Product not found.') % values.get('default_code')) 
							elif self.product_search == 'by_name':
								if not values.get('name'):
									raise Warning(_('Please give Name for updating Products'))

								product_ids = self.env['product.template'].search([('name','=', values.get('name'))],limit=1)

								if product_ids:
									if categ_id != False:
										product_ids.write({'categ_id': categ_id[0].id or False})
									if categ_type != False:
										product_ids.write({'type': categ_type or False})
									if barcode != False:
										product_ids.write({'barcode': barcode[0] or False})
									if uom_id != False:
										product_ids.write({'uom_id': uom_id or False})
									if uom_po_id != False:
										product_ids.write({'uom_po_id': uom_po_id})
									if values.get('default_code'):
										product_ids.write({'default_code': values.get('default_code') or False})
									if values.get('sale_price'):
										product_ids.write({'lst_price': values.get('sale_price') or False})
									if values.get('cost_price'):
										product_ids.write({'standard_price': values.get('cost_price') or False})
									if values.get('weight'):
										product_ids.write({'weight': values.get('weight') or False})
									if values.get('volume'):
										product_ids.write({'volume': values.get('volume') or False})

									product_ids.write({
										'taxes_id':[(6,0,tax_id_lst)],
										'supplier_taxes_id':[(6,0,supplier_taxes_id)],
										'tracking': tracking,
										})
								else:
									raise Warning(_('%s product not found.') %  values.get('name'))  
							else:
								if not barcode:
									raise Warning(_('Please give Barcode for updating Products'))
									
								product_ids = self.env['product.template'].search([('barcode','=', barcode[0])],limit=1)
								
								if product_ids:
									if categ_id != False:
										product_ids.write({'categ_id': categ_id[0].id or False})
									if categ_type != False:
										product_ids.write({'type': categ_type or False})
									if uom_id != False:
										product_ids.write({'uom_id': uom_id or False})
									if uom_po_id != False:
										product_ids.write({'uom_po_id': uom_po_id})
									if values.get('name'):
										product_ids.write({'name': values.get('name') or False})
									if values.get('default_code'):
										product_ids.write({'default_code': values.get('default_code') or False})
									if values.get('sale_price'):
										product_ids.write({'lst_price': values.get('sale_price') or False})
									if values.get('cost_price'):
										product_ids.write({'standard_price': values.get('cost_price') or False})
									if values.get('weight'):
										product_ids.write({'weight': values.get('weight') or False})
									if values.get('volume'):
										product_ids.write({'volume': values.get('volume') or False})


									product_ids.write({
										'taxes_id':[(6,0,tax_id_lst)],
										'supplier_taxes_id':[(6,0,supplier_taxes_id)],
										'tracking': tracking,
										})
								else:
									raise Warning(_('%s product not found.') % values.get('barcode'))  
			return res





		if self.import_option == 'xls':

			try:
				fp = tempfile.NamedTemporaryFile(delete=False,suffix=".xlsx")
				fp.write(binascii.a2b_base64(self.file))
				fp.seek(0)
				values = {}
				res = {}
				workbook = xlrd.open_workbook(fp.name)
				sheet = workbook.sheet_by_index(0)
			except Exception:
				raise Warning(_("Please give an Excel File for Importing Products!"))

			for row_no in range(sheet.nrows):
				val = {}
				if row_no <= 0:
					fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
				else:
					line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
					l1 = ['0','1','2','3','4','5','6','7','8','9', '.']
					flag = False
					for l in line[1]:
						if l not in l1:
							flag = True
							break;
 					
					if flag:
						code = line[1]
					else:
						code = line[1][:-2]
					
					if self.product_option == 'create':
						values.update( {
											'name':line[0],
											'default_code': code,
											'categ_id': line[2],
											'type': line[3],
											'barcode': line[4],
											'uom_id': line[5],
											'uom_po_id': line[6],
											'sale_price': line[7],
											'cost_price': line[8],
											'weight': line[9],
											'volume': line[10],
											'taxes_id':line[11],
											'supplier_taxes_id':line[12],
											'tracking':line[13],
										})
						if self.with_variant:
							values.update({'attributes': line[14],})
							
						res = self.create_product(values)
					else:
						product_obj = self.env['product.product']
						product_categ_obj = self.env['product.category']
						product_uom_obj = self.env['uom.uom']
						categ_id = False
						categ_type = False
						barcode = False
						uom_id = False
						uom_po_id = False
						if line[2]=='':
							pass
						else:
							categ_id = product_categ_obj.search([('name','=',line[2])],limit=1)
							if not categ_id:
								raise Warning(_('Category %s not found.' %line[2] ))
						if line[3]=='':
							pass
						else:
							if line[3] == 'Consumable':
								categ_type ='consu'
							elif line[3] == 'Service':
								categ_type ='service'
							elif line[3] == 'Stockable Product':
								categ_type ='product'
							else:
								categ_type = 'product'
								
						if line[4]=='':                             
							pass
						else:
							barcode = line[4].split(".")
						
						if line[5]=='':
							pass
						else:
							uom_search_id  = product_uom_obj.search([('name','=',line[5])])
							if not uom_search_id:
								raise Warning(_('UOM %s not found.' %line[5]))
							else:
								uom_id = uom_search_id.id
						
						if line[6]=='':
							pass
						else:
							uom_po_search_id  = product_uom_obj.search([('name','=',line[6])])
							if not uom_po_search_id:
								raise Warning(_('Purchase UOM %s not found' %line[6]))
							else:
								uom_po_id = uom_po_search_id.id
						
						tax_id_lst = []
						if line[11]:
							if ';' in line[11]:
								tax_names = line[11].split(';')
								for name in tax_names:
									tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'sale')])
									if not tax:
										raise Warning(_('"%s" Tax not in your system') % name)
									tax_id_lst.append(tax.id)

							elif ',' in line[11]:
								tax_names = line[11].split(',')
								for name in tax_names:
									tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'sale')])
									if not tax:
										raise Warning(_('"%s" Tax not in your system') % name)
									tax_id_lst.append(tax.id)

							else:
								tax_names = line[11].split(',')
								tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'sale')])
								if not tax:
									raise Warning(_('"%s" Tax not in your system') % tax_names)
								tax_id_lst.append(tax.id)

						supplier_taxes_id = []
						if line[12]:
							if ';' in line[12]:
								tax_names = line[12].split(';')
								for name in tax_names:
									tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
									if not tax:
										raise Warning(_('"%s" Tax not in your system') % name)
									supplier_taxes_id.append(tax.id)

							elif ',' in line[12]:
								tax_names = line[12].split(',')
								for name in tax_names:
									tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
									if not tax:
										raise Warning(_('"%s" Tax not in your system') % name)
									supplier_taxes_id.append(tax.id)

							else:
								tax_names = line[12].split(',')
								tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'purchase')])
								if not tax:
									raise Warning(_('"%s" Tax not in your system') % tax_names)
								supplier_taxes_id.append(tax.id)

						if (line[13] == 'By Lots') and (categ_type == 'product'):
							tracking = 'lot'
						elif (line[13] == 'By Unique Serial Number') and (categ_type == 'product'):
							tracking = 'serial'
						else:
							tracking = 'none'

						if self.product_search == 'by_code':
							if not line[1]:
								raise Warning(_('Please give Internal Reference for updating Products'))

							product_ids = self.env['product.template'].search([('default_code','=', code)],limit=1)

							if product_ids:
								if categ_id != False:
									product_ids.write({'categ_id': categ_id[0].id or False})
								if categ_type != False:
									product_ids.write({'type': categ_type or False})
								if barcode != False:
									product_ids.write({'barcode': barcode[0] or False})
								if uom_id != False:
									product_ids.write({'uom_id': uom_id or False})
								if uom_po_id != False:
									product_ids.write({'uom_po_id': uom_po_id})
								if line[0]:
									product_ids.write({'name': line[0] or False})
								if line[7]:
									product_ids.write({'lst_price': line[7] or False})
								if line[8]:
									product_ids.write({'standard_price': line[8] or False})
								if line[9]:
									product_ids.write({'weight': line[9] or False})
								if line[10]:
									product_ids.write({'volume': line[10] or False})

								product_ids.write({
									'taxes_id':[(6,0,tax_id_lst)],
									'supplier_taxes_id':[(6,0,supplier_taxes_id)],
									'tracking': tracking,
									})
							else:
								raise Warning(_('"%s" Product not found.') % line[1]) 
						elif self.product_search == 'by_name':
							if not line[0]:
								raise Warning(_('Please give Name for updating Products'))

							product_ids = self.env['product.template'].search([('name','=', line[0])],limit=1)

							if product_ids:
								if categ_id != False:
									product_ids.write({'categ_id': categ_id[0].id or False})
								if categ_type != False:
									product_ids.write({'type': categ_type or False})
								if barcode != False:
									product_ids.write({'barcode': barcode[0] or False})
								if uom_id != False:
									product_ids.write({'uom_id': uom_id or False})
								if uom_po_id != False:
									product_ids.write({'uom_po_id': uom_po_id})
								if line[1]:
									product_ids.write({'default_code': code or False})
								if line[7]:
									product_ids.write({'lst_price': line[7] or False})
								if line[8]:
									product_ids.write({'standard_price': line[8] or False})
								if line[9]:
									product_ids.write({'weight': line[9] or False})
								if line[10]:
									product_ids.write({'volume': line[10] or False})

								product_ids.write({
									'taxes_id':[(6,0,tax_id_lst)],
									'supplier_taxes_id':[(6,0,supplier_taxes_id)],
									'tracking': tracking,
									})
							else:
								raise Warning(_('%s product not found.') % line[0])  
						else:
							if not barcode:
								raise Warning(_('Please give Barcode for updating Products'))
								
							product_ids = self.env['product.template'].search([('barcode','=', barcode[0])],limit=1)
							
							if product_ids:
								if categ_id != False:
									product_ids.write({'categ_id': categ_id[0].id or False})
								if categ_type != False:
									product_ids.write({'type': categ_type or False})
								if uom_id != False:
									product_ids.write({'uom_id': uom_id or False})
								if uom_po_id != False:
									product_ids.write({'uom_po_id': uom_po_id})
								if line[0]:
									product_ids.write({'name': line[0] or False})
								if line[1]:
									product_ids.write({'default_code': code or False})
								if line[7]:
									product_ids.write({'lst_price': line[7] or False})
								if line[8]:
									product_ids.write({'standard_price': line[8] or False})
								if line[9]:
									product_ids.write({'weight': line[9] or False})
								if line[10]:
									product_ids.write({'volume': line[10] or False})

								product_ids.write({
									'taxes_id':[(6,0,tax_id_lst)],
									'supplier_taxes_id':[(6,0,supplier_taxes_id)],
									'tracking': tracking,
									})
							else:
								raise Warning(_('%s product not found.') % line[4])  
			return res

