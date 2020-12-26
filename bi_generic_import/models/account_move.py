# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
import io
import datetime
import tempfile
import binascii
import xlrd
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
import logging
_logger = logging.getLogger(__name__)
import re
try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')

try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')

class gen_journal_entry(models.TransientModel):
	_name = "gen.journal.entry"
	_description = "Generic Journal Entry"
	
	file_to_upload = fields.Binary('File')
	import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')

	
	def find_account_id(self, account_code ):	
		if account_code:
			account_ids	 = self.env['account.account'].search([('code', '=', account_code )])
			if account_ids:
				account_id = account_ids[0]  	   				
				return account_id
		else:
			raise Warning(_('Wrong Account Code') % account_code)

	def check_splcharacter(self ,test):
		# Make own character set and pass 
		# this as argument in compile method
 
		string_check= re.compile('@')
 
		# Pass the string in search 
		# method of regex object.
		if(string_check.search(str(test)) == None):
			return False
		else: 
			return True

	
	def check_desc(self, name):	
		if name:
			return name
		else:
			return  '/' 

	
	def find_account_analytic_id(self, analytic_account_name):
		analytic_account_id  = self.env['account.analytic.account'].search([('name', '=',analytic_account_name)])
		if analytic_account_id:
			analytic_account_id = analytic_account_id[0].id
			return analytic_account_id 	
		else: 
			raise Warning(_('Wrong Analytic Account Name %s') % analytic_account_name)

	
	def find_partner(self, partner_name):	
		partner_ids = self.env['res.partner'].search([('name', '=', partner_name)])
		if partner_ids:
			partner_id  = partner_ids[0]
			return partner_id
		else:
			partner_id = None 

	
	def check_currency(self, cur_name):	
		currency_ids = self.env['res.currency'].search([('name', '=', cur_name)])
		if currency_ids:
			currency_id  = currency_ids[0]
			return currency_id
		else:
			currency_id= None
			return  currency_id

	
	def create_import_move_lines(self, values):
		move_line_obj = self.env['account.move.line']
		move_obj = self.env['account.move']
		vals = {}
		tag_ids = []
		if values.get('partner'):
			partner_name = values.get('partner')  
			if self.find_partner(partner_name) != None:
				partner_id = self.find_partner(partner_name)
				vals.update({'partner_id': partner_id.id })

		if values.get('currency'):
			cur_name = values.get('currency')
			if cur_name  != '' and cur_name != None:    
				currency_id  = self.check_currency(cur_name)
				if currency_id != None :
					vals.update({'currency_id': currency_id.id  })
				else:
					raise Warning(_('Currency %s is not  in the system') % cur_name)

		if values.get('name'):
			desc_name = values.get('name')  
			name  = self.check_desc(desc_name)
			vals.update({'name': name })

		if values.get('date_maturity'):
			date = values.get('date_maturity')  
			vals.update({'date': date })

		if values.get('account_code'):
			account_code = values.get('account_code') 
			account_id  = self.find_account_id(str(account_code))
			if account_id != None:
				vals.update({'account_id': account_id.id })
			else:
				raise Warning(_('Wrong Account Code %s') % account_code)

		if values.get('debit') != '':
			vals.update({'debit' : float(values.get('debit')) })		
			if float(values.get('debit')) <0 :
				vals.update({'credit' : abs(values.get('debit')) })
				vals.update({'debit' : 0.0 })		
		else:
			vals.update({'debit' : float('0.0') })

		if values.get('name') == '':
			vals.update({'name' : '/' })		

		if values.get('credit') != '':
			vals.update({'credit' : float(values.get('credit')) })
			if float(values.get('credit')) <0 :
				vals.update({'debit' : abs(values.get('credit')) })
				vals.update({'credit':0.0})		
		else:
			vals.update({'credit' : float('0.0') })

		if values.get('amount_currency') != '':
			vals.update({'amount_currency' : float(values.get('amount_currency')) })

		if values.get('analytic_account_id') != '':
			account_anlytic_account = values.get('analytic_account_id')
			if account_anlytic_account != '' or account_anlytic_account == None:
				analytic_account_id  = self.find_account_analytic_id(account_anlytic_account)		 
				vals.update({'analytic_account_id' : analytic_account_id })
			else:
				raise Warning(_('Wrong Account Code %s') % account_anlytic_account)	
		
		if values.get('analytic_Tag'):
			if ';' in  values.get('analytic_Tag'):
				tag_names = values.get('analytic_Tag').split(';')
				for name in tag_names:
					tag= self.env['account.analytic.tag'].search([('name', '=', name)])
					if not tag:
						raise Warning(_('"%s" Analytic Tags not in your system') % name)
					tag_ids.append(tag.id)

			elif ',' in  values.get('analytic_Tag'):
				tag_names = values.get('analytic_Tag').split(',')
				for name in tag_names:
					tag= self.env['account.analytic.tag'].search([('name', '=', name)])
					if not tag:
						raise Warning(_('"%s" Analytic Tags not in your system') % name)
					tag_ids.append(tag.id)
			else:
				tag_names = values.get('analytic_Tag').split(',')
				tag= self.env['account.analytic.tag'].search([('name', '=', tag_names)])
				if not tag:
					raise Warning(_('"%s" Analytic Tags not in your system') % tag_names)
				tag_ids.append(tag.id)
			if tag_ids:
				vals.update({'analytic_tag_ids' : [(6, 0, tag_ids)]})


		main_list = values.keys()
		for i in main_list:
			model_id = self.env['ir.model'].search([('model','=','account.move.line')])           
			if type(i) == bytes:
					normal_details = i.decode('utf-8')
			else:
					normal_details = i
			if normal_details.startswith('x_'):
				any_special = self.check_splcharacter(normal_details)
				if any_special:
					split_fields_name = normal_details.split("@")
					technical_fields_name = split_fields_name[0]
					many2x_fields = self.env['ir.model.fields'].search([('name','=',technical_fields_name),('state','=','manual'),('model_id','=',model_id.id)])
					if many2x_fields.id:
						if many2x_fields.ttype in ['many2one','many2many']:						
							if many2x_fields.ttype =="many2one":
								if values.get(i):
									fetch_m2o = self.env[many2x_fields.relation].search([('name','=',values.get(i))])
									if fetch_m2o.id:
										vals.update({
												technical_fields_name: fetch_m2o.id
												})
									else:
										raise Warning(_('"%s" This custom field value "%s" not available in system') % (i , values.get(i)))
							if many2x_fields.ttype =="many2many":
								m2m_value_lst = []
								if values.get(i):
									if ';' in values.get(i):
										m2m_names = values.get(i).split(';')
										for name in m2m_names:
												m2m_id = self.env[many2x_fields.relation].search([('name', '=', name)])
												if not m2m_id:
													raise Warning(_('"%s" This custom field value "%s" not available in system') % (i , name))
												m2m_value_lst.append(m2m_id.id)

									elif ',' in values.get(i):
										m2m_names = values.get(i).split(',')
										for name in m2m_names:
											m2m_id = self.env[many2x_fields.relation].search([('name', '=', name)])
											if not m2m_id:
												raise Warning(_('"%s" This custom field value "%s" not available in system') % (i , name))
											m2m_value_lst.append(m2m_id.id)

									else:
										m2m_names = values.get(i).split(',')
										m2m_id = self.env[many2x_fields.relation].search([('name', 'in', m2m_names)])
										if not m2m_id:
											raise Warning(_('"%s" This custom field value "%s" not available in system') % (i , m2m_names))
										m2m_value_lst.append(m2m_id.id)
								vals.update({
										technical_fields_name : m2m_value_lst
										})                              
						else:
							raise Warning(_('"%s" This custom field type is not many2one/many2many') % technical_fields_name)                             
					else:
						raise Warning(_('"%s" This m2x custom field is not available in system') % technical_fields_name)
				else:
					normal_fields = self.env['ir.model.fields'].search([('name','=',normal_details),('state','=','manual'),('model_id','=',model_id.id)])
					if normal_fields.id:
						if normal_fields.ttype ==  'boolean':
							vals.update({
									normal_details : values.get(i)
									})
						elif normal_fields.ttype == 'char':
							vals.update({
									normal_details : values.get(i)
									})                              
						elif normal_fields.ttype == 'float':
							if values.get(i) == '':
								float_value = 0.0
							else:
								float_value = float(values.get(i)) 
							vals.update({
								normal_details : float_value
								})                              
						elif normal_fields.ttype == 'integer':
							if values.get(i) == '':
								int_value = 0
							else:
								int_value = int(values.get(i)) 
							vals.update({
								normal_details : int_value
								})                        
						elif normal_fields.ttype == 'selection':
							vals.update({
									normal_details : values.get(i)
									})                              
						elif normal_fields.ttype == 'text':
							vals.update({
									normal_details : values.get(i)
									})                              
					else:
						raise Warning(_('"%s" This custom field is not available in system') % normal_details)
		return vals

 
	def import_move_lines (self):
		if  self.import_option == 'csv':
			keys = ['name', 'partner' , 'analytic_account_id', 'account_code', 'date_maturity', 'debit', 'credit', 'amount_currency','currency','analytic_Tag']
			
			try:
				csv_data = base64.b64decode(self.file_to_upload)
				data_file = io.StringIO(csv_data.decode("utf-8"))
				data_file.seek(0)
				file_reader = []
				csv_reader = csv.reader(data_file, delimiter=',')
				file_reader.extend(csv_reader)
			except Exception:
				raise exceptions.Warning(_("Invalid file!"))

			values = {}
			lines = []	
			for i in range(len(file_reader)):
				field = list(map(str, file_reader[i]))
				count = 1
				count_keys = len(keys)
				if len(field) > count_keys:
					for new_fields in field:
						if count > count_keys :
							keys.append(new_fields)                
						count+=1 				
				values = dict(zip(keys, field))
				if values:
					if i == 0:
						continue
					else:
						res = self.create_import_move_lines(values)
						lines.append((0,0,res))
					
			if self._context:
					if self._context.get('active_id'):
						move_obj = self.env['account.move']
						move_record = move_obj.browse(self._context.get('active_id'))
						move_record.write({'line_ids' : lines})
		else:
			try:
				fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
				fp.write(binascii.a2b_base64(self.file_to_upload))
				fp.seek(0)
				values = {}
				workbook = xlrd.open_workbook(fp.name)
				sheet = workbook.sheet_by_index(0)
				product_obj = self.env['product.product']
				lines = []

			except Exception:
				raise exceptions.Warning(_("Invalid file!"))

			for row_no in range(sheet.nrows):
				val = {}
				if row_no <= 0:
					line_fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
				else:
					line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
					date  = False
					if line[4] != '':
						date1 = int(float(line[4]))
						line_datetime = datetime(*xlrd.xldate_as_tuple(date1, workbook.datemode))
						date_string = line_datetime.date().strftime('%Y-%m-%d')
						values =  {
								'name':line[0],
								'partner': line[1],
								'analytic_account_id': line[2],
								'account_code': line[3],
								'date_maturity':date_string,
								'debit': line[5],
								'credit': line[6],
								'amount_currency': line[7],
								'analytic_Tag' : line[9],
								'currency': line[8],
							}
						count = 0
						for l_fields in line_fields:
							if(count > 5):
								values.update({l_fields : line[count]})                        
							count+=1   							
					res = self.create_import_move_lines(values)
					lines.append((0,0,res))

			if self._context:
				if self._context.get('active_id'):
					move_obj = self.env['account.move']
					move_record = move_obj.browse(self._context.get('active_id'))
					move_record.write({'line_ids' : lines})
											 
