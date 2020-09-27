# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
import tempfile
import binascii
import xlrd
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
import logging
_logger = logging.getLogger(__name__)
import io
from io import StringIO

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

class import_task(models.TransientModel):
	_name = "import.task"
	
	file = fields.Binary('File')
	import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')

	
	def create_task(self, values):
		project_task_obj = self.env['project.task']
		
		project_id = self.find_project(values.get('project_id'))
		user_id  = self.find_user(values.get('user_id'))
		tag_ids = self.find_tags(values.get('tag_ids'))
		deadline_date = self.find_deadline_date(values.get('date_deadline'))
		
		vals = {
				  'name':values.get('name'),
				  'project_id':project_id.id,
				  'user_id': user_id.id,
				  'tag_ids': [(6,0,[x.id for x in tag_ids])],
				  'date_deadline': deadline_date,
				  'description' : values.get('description'),
				  }
		res = project_task_obj.create(vals)
		return res

	
	def find_project(self, name):
		project_obj = self.env['project.project']
		project_search = project_obj.search([('name', '=', name)])
		if project_search:
			return project_search
		else:
			project_id = project_obj.create({
											 'name' : name})
			return project_id
			
	
	def find_tags(self, name):
		project_tags_obj = self.env['project.tags']
		project_tags_search = project_tags_obj.search([('name', '=', name)])
		if project_tags_search:
			return project_tags_search
		else:
			raise Warning(_(' "%s" Tags is not available.') % name)
			
	
	def find_user(self, name):
		user_obj = self.env['res.users']
		user_search = user_obj.search([('name', '=', name)])
		if user_search:
			return user_search
		else:
			raise Warning(_(' "%s" User is not available.') % name)
			
	
	
	def find_deadline_date(self, date):
		project_task_obj = self.env['project.task']
		DATETIME_FORMAT = "%Y-%m-%d"
		i_date = datetime.strptime(date, DATETIME_FORMAT)
		return i_date
				
	
	def import_task(self):
 
		if self.import_option == 'csv': 
			try:       
				keys = ['name','project_id','user_id','tag_ids','date_deadline','description']
				csv_data = base64.b64decode(self.file)
				data_file = io.StringIO(csv_data.decode("utf-8"))
				data_file.seek(0)
				file_reader = []
				csv_reader = csv.reader(data_file, delimiter=',')
				file_reader.extend(csv_reader)
			except Exception:
				raise exceptions.Warning(_("Please select CSV/XLS file or You have selected invalid file"))
			values = {}
			for i in range(len(file_reader)):
				field = list(map(str, file_reader[i]))
				values = dict(zip(keys, field))
				if values:
					if i == 0:
						continue
					else:
						res = self.create_task(values)
		else:
			try:
				fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
				fp.write(binascii.a2b_base64(self.file))
				fp.seek(0)
				values = {}
				workbook = xlrd.open_workbook(fp.name)
				sheet = workbook.sheet_by_index(0)

			except Exception:
				raise exceptions.Warning(_("Please select CSV/XLS file or You have selected invalid file")) 
			for row_no in range(sheet.nrows):
				val = {}
				if row_no <= 0:
					fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
				else:
					line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
					a1 = int(float(line[4]))
					a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
					date_string = a1_as_datetime.date().strftime('%Y-%m-%d')

					values.update( {'name':line[0],
									'project_id': line[1],
									'user_id': line[2],
									'tag_ids':line[3],
									'date_deadline':date_string,
									'description':line[5],
									})
					res = self.create_task(values)
			           
			return res
		

