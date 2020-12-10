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

class import_project_task(models.Model):
    _inherit = "project.task"

    is_import = fields.Boolean(string = "imported data" , default = False)

class import_task(models.TransientModel):
	_name = "import.task"
	_description = "Import Task"
	
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
				  'is_import' : True
				  }
		main_list = values.keys()
		# count = 0
		for i in main_list:
			model_id = self.env['ir.model'].search([('model','=','project.task')])           
			# if count > 19:
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
										raise Warning(_('"%s" This custom field value "%s" not available in system') % (many2x_fields.name , values.get(i)))
							if many2x_fields.ttype =="many2many":
								m2m_value_lst = []
								if values.get(i):
									if ';' in values.get(i):
										m2m_names = values.get(i).split(';')
										for name in m2m_names:
											m2m_id = self.env[many2x_fields.relation].search([('name', '=', name)])
											if not m2m_id:
												raise Warning(_('"%s" This custom field value "%s" not available in system') % (many2x_fields.name , name))
											m2m_value_lst.append(m2m_id.id)

									elif ',' in values.get(i):
										m2m_names = values.get(i).split(',')
										for name in m2m_names:
											m2m_id = self.env[many2x_fields.relation].search([('name', '=', name)])
											if not m2m_id:
												raise Warning(_('"%s" This custom field value "%s" not available in system') % (many2x_fields.name , name))
											m2m_value_lst.append(m2m_id.id)

									else:
										m2m_names = values.get(i).split(',')
										m2m_id = self.env[many2x_fields.relation].search([('name', 'in', m2m_names)])
										if not m2m_id:
											raise Warning(_('"%s" This custom field value "%s" not available in system') % (many2x_fields.name , m2m_names))
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
					line_fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
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
					count = 0
					for l_fields in line_fields:
						if(count > 5):
							values.update({l_fields : line[count]})                        
						count+=1 
					res = self.create_task(values)
					   
			return res
		

