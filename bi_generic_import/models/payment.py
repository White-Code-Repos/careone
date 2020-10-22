# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime
import tempfile
import binascii
import logging
from odoo.exceptions import Warning
from odoo import models, fields, api, _,exceptions
_logger = logging.getLogger(__name__)
import re
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')

class account_payment_inherit(models.Model):
    _inherit = "account.payment"

    is_import = fields.Boolean(string = " Is Imported data" , default = False)

class gen_salereceipt(models.TransientModel):
    _name = "gen.salepayment"
    _description = "Gen Sale Payement"

    file = fields.Binary('File')
    payment_option = fields.Selection([('customer', 'Customer Payment'),('supplier', 'Supplier Pament')],string='Payment',default='customer')

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
    
    def import_fle(self):
        try:
            fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except Exception:
            raise exceptions.Warning(_("Invalid file!"))

        for row_no in range(sheet.nrows):
            if row_no <= 0:
                line_fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                if line[3] != '':
                    a1 = int(float(line[3]))
                    a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                    date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                else:
                    raise Warning(_("Please assign a Date"))

                values.update( {'partner_id':line[0],
                                'amount': line[1],
                                'journal_id': line[2],
                                 'payment_date': date_string,
                                'communication': line[4],
                                'payment_option':self.payment_option
                                })
                count = 0
                for l_fields in line_fields:
                    if(count > 6):
                        values.update({l_fields : line[count]})                        
                    count+=1                    
                res = self._create_customer_payment(values)
                        
        return res

    
    def _create_customer_payment(self,values):
        name = self._find_customer(values.get('partner_id'))
        payment_journal =self._find_journal_id(values.get('journal_id'))
        pay_date = self.find_date(values.get('payment_date'))
        pay_id =self.find_payment_method()
        
        if values['payment_option'] == 'customer' :
        	partner_type = 'customer'
        	payment_type = 'inbound'
        else:
        	partner_type = 'supplier'
        	payment_type = 'outbound'
        
        vals = {
                'partner_id':name,
                 'amount': values.get('amount'),
                 'journal_id':payment_journal,
                 'partner_type':partner_type,
                 'communication':values.get('communication'),
                 'payment_date':pay_date,
                 'payment_method_id': pay_id,
                 'payment_type' : payment_type,
                 'is_import' : True
               }
        main_list = values.keys()
        for i in main_list:
            model_id = self.env['ir.model'].search([('model','=','account.payment')])           
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
        res = self.env['account.payment'].create(vals)
        return res
    
   
    def _find_customer(self,name):
        partner_search = self.env['res.partner'].search([('name','=',name)])
        if not partner_search:
            raise Warning (_("%s Customer Not Found") % name)
        return partner_search.id

    
    def _find_journal_id(self,journal):
        journal_search =self.env['account.journal'].search([('name','=',journal)])
        if not journal_search:
            raise Warning(_("%s Journal Not Found") % journal)
        return journal_search.id

    
    def find_date(self,date):
        DATETIME_FORMAT = "%Y-%m-%d"
        p_date = datetime.strptime(date,DATETIME_FORMAT)
        return p_date
    
    
    def find_payment_method(self,  payment_type_id=None):
        payment_option_selection = self.env['account.payment.method'].search([('name','=','Manual'),('payment_type','=','inbound')])
        if not payment_option_selection:
            if payment_type_id == 'supplier':
                payment_type_id = self.env['account.payment'].search([('name','=','Manual'),('payment_type','=','outbound')])
                payment_option_selection = payment_type_id
            else:
                pass

        return payment_option_selection.id

