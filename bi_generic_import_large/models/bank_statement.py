# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import tempfile
import binascii
import logging
from datetime import datetime
from odoo.exceptions import Warning
from odoo import models, fields, api, exceptions, _
_logger = logging.getLogger(__name__)
from io import StringIO
import io
import re
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


try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class account_bank_statement_wizard(models.TransientModel):
    _inherit= "account.bank.statement.wizard"
    _description = "Account Bank Statement Wizard"

    file = fields.Binary('File')
    file_opt = fields.Selection([('excel','Excel'),('csv','CSV')])

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

    
    def import_file(self):
        if self.file_opt == 'csv':
            try:
                keys = ['date','ref','partner','memo','amount','currency']                    
                data = base64.b64decode(self.file)
                file_input = io.StringIO(data.decode("utf-8"))
                file_input.seek(0)
                reader_info = []
                reader = csv.reader(file_input, delimiter=',')
                reader_info.extend(reader)
            except Exception:
                raise exceptions.Warning(_("Not a valid file!"))
            values = {}
            for i in range(len(reader_info)):
                field = list(map(str, reader_info[i]))
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
                        res = self._create_statement_lines(values)
        elif self.file_opt == 'excel':
            try:
                fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.Warning(_("Not a valid file!"))

            for row_no in range(sheet.nrows):
                if row_no <= 0:
                    line_fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
                else:
                    line = list(map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    if not line[0]:
                        raise Warning('Please Provide Date Field Value')
                    a1 = int(float(line[0]))
                    a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                    date_string = a1_as_datetime.date().strftime('%Y-%m-%d')

                    ref =''
                    memo =''
                    if line[1] == '':
                        ref  == ''

                    else:
                        ref = line[1].decode("utf-8")
                    if line[3]  == '':
                        memo =''
                    else:
                        memo = line[3].decode("utf-8")
         
                    values.update( {'date':date_string,
                                    'ref': ref,
                                    'partner': line[2],
                                    'memo': memo,
                                    'amount': line[4],
                                    'currency' : line[5],
                                    })
                    count = 0
                    for l_fields in line_fields:
                        if(count > 5):
                            values.update({l_fields : line[count]})                        
                        count+=1                        
                    res = self._create_statement_lines(values)
        else:
            raise Warning('Please Select File Type')
        self.env['account.bank.statement'].browse(self._context.get('active_id'))._end_balance()
        return res
    
    def _create_statement_lines(self,values):
        account_bank_statement_line_obj = self.env['account.bank.statement.line']
        partner_id = self._find_partner(values.get('partner'))
        if values.get('currency'):
            currency_id = self._find_currency(values.get('currency'))
        else:
            currency_id = False
        if not values.get('date'):
            raise Warning('Please Provide Date Field Value')
        if not values.get('memo'):
            raise Warning('Please Provide Memo Field Value')
        vals = {
                'date':values.get('date'),
                'ref':values.get('ref'),
                'partner_id':partner_id,
                'name':values.get('memo'),
                'amount':values.get('amount'),
                'currency_id':currency_id,
                'statement_id':self._context.get('active_id'),
                }
        main_list = values.keys()
        for i in main_list:
            model_id = self.env['ir.model'].search([('model','=','account.bank.statement.line')])           
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
        tech_tuple= []
        val_tuple = []
        store_tuple = []

        
        for tech_name in vals :
            tech_tuple.append(tech_name)
            val_tuple.append(vals[tech_name])
            store_tuple.append("%s")

        tech_tuple = tuple(tech_tuple) 
        val_tuple = tuple(val_tuple) 
        store_tuple = tuple(store_tuple) 

        tec_str = "("
        store_str = "("
        
        for i in range (0,len(tech_tuple)) :
            if i == len(tech_tuple) - 1 :
                tec_str = tec_str + str(tech_tuple[i]) + ')'
                store_str = store_str + "%s" + ')'

            else :

                tec_str = tec_str + str(tech_tuple[i]) + ','
                store_str = store_str + "%s" + ','

        print(tec_str)
        print(store_str)
        select_queru = """INSERT INTO account_bank_statement_line """ + tec_str + """ VALUES """ + store_str
                    

        bank_statement_lines = self.env.cr.execute(select_queru,val_tuple)
            
        
        #bank_statement_lines = account_bank_statement_line_obj.create(vals)
        return True
    def _find_partner(self,name):
        partner_id = self.env['res.partner'].search([('name','=',name)])
        if partner_id:
            return partner_id.id
        else:
            return

    def _find_currency(self,currency):
        currency_id = self.env['res.currency'].search([('name','=',currency)])
        if currency_id:
            return currency_id.id
        else:
            raise Warning(_(' "%s" Currency are not available.') % currency.decode("utf-8"))


