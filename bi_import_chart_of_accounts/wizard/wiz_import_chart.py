# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime
import tempfile
import binascii
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, _
import logging
_logger = logging.getLogger(__name__)
import io
try:
	import xlrd
except ImportError:
	_logger.debug('Cannot `import xlrd`.')
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

class ImportChartAccount(models.TransientModel):
	_name = "import.chart.account"

	File_slect = fields.Binary(string="Select Excel File")
	import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')

	
	def imoport_file(self):

# -----------------------------
		if self.import_option == 'csv':

			keys = ['code', 'name', 'user_type_id']

			try:
				csv_data = base64.b64decode(self.File_slect)
				data_file = io.StringIO(csv_data.decode("utf-8"))
				data_file.seek(0)
				file_reader = []
				values = {}
				csv_reader = csv.reader(data_file, delimiter=',')
				file_reader.extend(csv_reader)

			except:

				raise Warning(_("Invalid file!"))

			for i in range(len(file_reader)):
				field = list(map(str, file_reader[i]))
				values = dict(zip(keys, field))
				if values:
					if i == 0:
						continue
					else:
						values.update({
										'code' : field[0],
										'name' : field[1],
										'user' : field[2],
										'tax'  : field[3],
										'tag'  : field[4],
										'group': field[5],
										'currency' :field[6],
										'reconcile':field[7],
										'deprecat' :field[8],

										})
						res = self.create_chart_accounts(values)

# ---------------------------------------
		elif self.import_option == 'xls':
			try:
				fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
				fp.write(binascii.a2b_base64(self.File_slect))
				fp.seek(0)
				values = {}
				workbook = xlrd.open_workbook(fp.name)
				sheet = workbook.sheet_by_index(0)

			except:
				raise Warning(_("Invalid file!"))

			for row_no in range(sheet.nrows):
				val = {}
				if row_no <= 0:
					fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
				else:
					
					line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))

					values.update( {'code' : line[0],
									'name' : line[1],
									'user' : line[2],
									'tax'  : line[3],
									'tag'  : line[4],
									'group': line[5],
									'currency' :line[6],
									'reconcile':line[7],
									'deprecat' :line[8],
									})

					res = self.create_chart_accounts(values)
# ------------------------------------------------------------						
		else:
			raise Warning(_("Please select any one from xls or csv formate!"))

		return res
	
	def create_chart_accounts(self,values):

		if values.get("code") == "":
			raise Warning(_('Code field cannot be empty.') )

		if values.get("name") == "":
			raise Warning(_('Name field cannot be empty.') )

		if values.get("user") == "":
			raise Warning(_('type field cannot be empty.'))

		if values.get("code"):
			s = str(values.get("code"))
			code_no = s.rstrip('0').rstrip('.') if '.' in s else s

		account_obj = self.env['account.account']
		account_search = account_obj.search([
			('code', '=', values.get('code'))
			])
		
		is_reconcile = False
		is_deprecated= False

		if values.get("reconcile") == 'TRUE' or values.get("reconcile") == "1":
			is_reconcile = True

		if values.get("deprecat") == 'TRUE'  or values.get("deprecat") == "1":
			is_deprecated = True

		user_id = self.find_user_type(values.get('user'))
		currency_get = self.find_currency(values.get('currency'))
		# tag_ids = self.find_tags(values.get('tag'))
		group_get = self.find_group(values.get('group'))

# --------tax-
		tax_ids = []
		if values.get('tax'):
			if ';' in  values.get('tax'):
				tax_names = values.get('tax').split(';')
				for name in tax_names:
					tax= self.env['account.tax'].search([('name', '=', name)])
					if not tax:
						raise Warning(_('%s Tax not in your system') % name)
					for t in tax:
						tax_ids.append(t)

			elif ',' in  values.get('tax'):
				tax_names = values.get('tax').split(',')
				for name in tax_names:
					tax= self.env['account.tax'].search([('name', '=', name)])
					if not tax:
						raise Warning(_('%s Tax not in your system') % name)
					for t in tax:
						tax_ids.append(t)
			else:
				tax_names = values.get('tax').split(',')
				tax= self.env['account.tax'].search([('name', '=', tax_names)])
				if not tax:
					raise Warning(_('"%s" Tax not in your system') % tax_names)
				for t in tax:
					tax_ids.append(t)

# ------------tags
		tag_ids = []
		if values.get('tag'):
			if ';' in  values.get('tag'):
				tag_names = values.get('tag').split(';')
				for name in tag_names:
					tag= self.env['account.account.tag'].search([('name', '=', name)])
					if not tag:
						raise Warning(_('"%s" Tag not in your system') % name)
					tag_ids.append(tag)

			elif ',' in  values.get('tag'):
				tag_names = values.get('tag').split(',')
				for name in tag_names:
					tag= self.env['account.account.tag'].search([('name', '=', name)])
					if not tag:
						raise Warning(_('"%s" Tag not in your system') % name)
					tag_ids.append(tag)
			else:
				tag_names = values.get('tag').split(',')
				tag= self.env['account.account.tag'].search([('name', '=', tag_names)])
				if not tag:
					raise Warning(_('"%s" Tag not in your system') % tag_names)
				tag_ids.append(tag)

		data={
				'code' : code_no,
				'name' : values.get('name'),
				'user_type_id':user_id.id,
				'tax_ids':[(6,0,[y.id for y in tax_ids])]if values.get('tax') else False,	
				'tag_ids':[(6,0,[x.id for x in tag_ids])]if values.get('tag') else False,
				'group_id':group_get.id,
				'currency_id':currency_get or False,
				'reconcile':is_reconcile,
				'deprecated':is_deprecated,

				}
		chart_id = account_obj.create(data)		

		return chart_id

# ---------------------------user-----------------

	
	def find_user_type(self,user):
		user_type=self.env['account.account.type']
		user_search = user_type.search([('name','=',user)])
		if user_search:
			return user_search
		else:
			raise Warning(_('Field User is not correctly set.'))

# --------------------currency------------------

	
	def find_currency(self, name):
		currency_obj = self.env['res.currency']
		currency_search = currency_obj.search([('name', '=', name)])
		if currency_search:
			return currency_search.id
		else:
			if name == "":
				pass
			else:
				raise Warning(_(' %s currency are not available.') % name)

# -----------------group-------

	
	def find_group(self,group):
		group_type=self.env['account.group']
		group_search = group_type.search([('name','=',group)])

		if group_search:
			return group_search
		else:
			group_id = group_type.create({
				'name' : group
				})
			return group_id
