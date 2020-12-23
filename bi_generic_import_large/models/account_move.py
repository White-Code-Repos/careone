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

    file_to_upload = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')

    @api.multi
    def find_account_id(self, account_code ): 
      if account_code:
        account_ids   = self.env['account.account'].search([('code', '=', account_code )])
        if account_ids:
          account_id = account_ids[0]              
          return account_id
      else:
        raise Warning(_('Wrong Account Code') % account_code)


    @api.multi
    def check_desc(self, name): 
      if name:
        return name
      else:
        return  '/' 

    @api.multi
    def find_account_analytic_id(self, analytic_account_name):
      analytic_account_id  = self.env['account.analytic.account'].search([('name', '=',analytic_account_name)])
      if analytic_account_id:
        analytic_account_id = analytic_account_id[0].id
        return analytic_account_id   
      else: 
        raise Warning(_('Wrong Analytic Account Name %s') % analytic_account_name)

    @api.multi
    def find_partner(self, partner_name): 
      partner_ids = self.env['res.partner'].search([('name', '=', partner_name)])
      if partner_ids:
        partner_id  = partner_ids[0]
        return partner_id
      else:
        partner_id = None 

    @api.multi
    def check_currency(self, cur_name): 
      currency_ids = self.env['res.currency'].search([('name', '=', cur_name)])
      if currency_ids:
        currency_id  = currency_ids[0]
        return currency_id
      else:
        currency_id= None
        return  currency_id

    @api.multi
    def create_import_move_lines(self, values):
      move_line_obj = self.env['account.move.line']
      move_obj = self.env['account.move']

      if values.get('partner'):
        partner_name = values.get('partner')  
        if self.find_partner(partner_name) != None:
          partner_id = self.find_partner(partner_name)
          values.update({'partner_id': partner_id.id })

      if values.get('currency'):
        cur_name = values.get('currency')
        if cur_name  != '' and cur_name != None:    
          currency_id  = self.check_currency(cur_name)
          if currency_id != None :
            values.update({'currency_id': currency_id.id  })
          else:
            raise Warning(_('Currency %s is not  in the system') % cur_name)

      if values.get('name'):
        desc_name = values.get('name')  
        name  = self.check_desc(desc_name)
        values.update({'name': name })

      if values.get('date_maturity'):
        date = values.get('date_maturity')  
        values.update({'date': date })

      if values.get('account_code'):
        account_code = values.get('account_code') 
        account_id  = self.find_account_id(str(account_code))
        if account_id != None:
          values.update({'account_id': account_id.id })
        else:
          raise Warning(_('Wrong Account Code %s') % account_code)

      if values.get('debit') != '':
        values.update({'debit' : float(values.get('debit')) })   
        if float(values.get('debit')) <0 :
          values.update({'credit' : abs(values.get('debit')) })
          values.update({'debit' : 0.0 })    
      else:
        values.update({'debit' : float('0.0') })

      if values.get('name') == '':
        values.update({'name' : '/' })   

      if values.get('credit') != '':
        values.update({'credit' : float(values.get('credit')) })
        if float(values.get('credit')) <0 :
          values.update({'debit' : abs(values.get('credit')) })
          values.update({'credit':0.0})    
      else:
        values.update({'credit' : float('0.0') })

      if values.get('amount_currency') != '':
        values.update({'amount_currency' : float(values.get('amount_currency')) })

      if values.get('analytic_account_id') != '':
        account_anlytic_account = values.get('analytic_account_id')
        if account_anlytic_account != '' or account_anlytic_account == None:
          analytic_account_id  = self.find_account_analytic_id(account_anlytic_account)     
          values.update({'analytic_account_id' : analytic_account_id })
        else:
          raise Warning(_('Wrong Account Code %s') % account_anlytic_account)  
      return values

    @api.multi
    def import_move_lines (self):
      if  self.import_option == 'csv':
        try:
          keys = ['name', 'partner' , 'analytic_account_id', 'account_code', 'date_maturity', 'debit', 'credit', 'amount_currency','currency']
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
        except Exception:
          raise exceptions.Warning(_("Invalid file!"))

        product_obj = self.env['product.product']
        lines = []
        for row_no in range(sheet.nrows):
          val = {}
          if row_no <= 0:
            fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
          else:
            line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
            date  = False
            if line[4] != '':
              date1 = int(float(line[4]))
              line_datetime = datetime(*xlrd.xldate_as_tuple(date1, workbook.datemode))
              date_string = line_datetime.date().strftime('%Y-%m-%d')
              values =  {'name':line[0],
                    'partner': line[1],
                    'analytic_account_id': line[2],
                    'account_code': line[3],
                    'date_maturity':date_string,
                    'debit': line[5],
                    'credit': line[6],
                    'amount_currency': line[7],
                    'currency': line[8]}
              res = self.create_import_move_lines(values)
              lines.append((0,0,res))
        
            if self._context:
              if self._context.get('active_id'):
                move_obj = self.env['account.move']
                move_record = move_obj.browse(self._context.get('active_id'))
                move_record.write({'line_ids' : lines})
                       
