# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
import tempfile
import binascii
import xlrd
import io
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
import re
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

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    custom_seq = fields.Boolean('Custom Sequence')
    system_seq = fields.Boolean('System Sequence')
    purchase_name = fields.Char('Purchase Name')
    is_import = fields.Boolean("import records" ,default = False)    

class gen_purchase(models.TransientModel):
    _name = "gen.purchase"
    _description = "Gen Purchase"

    file = fields.Binary('File')
    sequence_opt = fields.Selection([('custom', 'Use Excel/CSV Sequence Number'), ('system', 'Use System Default Sequence Number')], string='Sequence Option',default='custom')
    import_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select', default='csv')
    stage = fields.Selection(
        [('draft', 'Import Draft Purchase'), ('confirm', 'Confirm Purchase Automatically With Import')],
        string="Purchase Stage Option", default='draft')
    import_prod_option = fields.Selection([('name', 'Name'),('code', 'Code'),('barcode', 'Barcode')],string='Import Product By ',default='name')        

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
    
    def make_purchase(self, values):
        purchase_obj = self.env['purchase.order']
        if self.sequence_opt == "custom":
            pur_search = purchase_obj.search([
		        ('name', '=', values.get('purchase_no')),
		    ])
        else:
            pur_search = purchase_obj.search([
		        ('purchase_name', '=', values.get('purchase_no')),
		    ])
		    
        if pur_search:
            if pur_search.partner_id.name == values.get('vendor'):
                if  pur_search.currency_id.name == values.get('currency'):
                    self.make_purchase_line(values, pur_search)
                    return pur_search
                else:
                    raise Warning(_('Currency is different for "%s" .\n Please define same.') % values.get('currency'))
            else:
                raise Warning(_('Customer name is different for "%s" .\n Please define same.') % values.get('vendor'))
        else:
            if values.get('seq_opt') == 'system':
                name = self.env['ir.sequence'].next_by_code('purchase.order')
            elif values.get('seq_opt') == 'custom':
                name = values.get('purchase_no')
            partner_id = self.find_partner(values.get('vendor'))
            currency_id = self.find_currency(values.get('currency'))
            if values.get('date'):
                pur_date = self.make_purchase_date(values.get('date'))
            else:
                pur_date = datetime.today()

            pur_id = purchase_obj.create({
                'partner_id' : partner_id.id,
                'currency_id' : currency_id.id,
                'name':name,
                'date_order':pur_date,
                'custom_seq': True if values.get('seq_opt') == 'custom' else False,
                'system_seq': True if values.get('seq_opt') == 'system' else False,
                'purchase_name' : values.get('purchase_no'),
                'is_import' :True
            })
            main_list = values.keys()
            # count = 0
            for i in main_list:
                model_id = self.env['ir.model'].search([('model','=','purchase.order')])           
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
                                            pur_id.update({
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
                                    pur_id.update({
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
                                pur_id.update({
                                    normal_details : values.get(i)
                                    })
                            elif normal_fields.ttype == 'char':
                                pur_id.update({
                                    normal_details : values.get(i)
                                    })                              
                            elif normal_fields.ttype == 'float':
                                if values.get(i) == '':
                                    float_value = 0.0
                                else:
                                    float_value = float(values.get(i)) 
                                pur_id.update({
                                    normal_details : float_value
                                    })                              
                            elif normal_fields.ttype == 'integer':
                                if values.get(i) == '':
                                    int_value = 0
                                else:
                                    int_value = int(values.get(i)) 
                                pur_id.update({
                                    normal_details : int_value
                                    })                               
                            elif normal_fields.ttype == 'selection':
                                pur_id.update({
                                    normal_details : values.get(i)
                                    })                              
                            elif normal_fields.ttype == 'text':
                                pur_id.update({
                                    normal_details : values.get(i)
                                    })                              
                        else:
                            raise Warning(_('"%s" This custom field is not available in system') % normal_details)            
        self.make_purchase_line(values, pur_id)
        return pur_id



    
    def make_purchase_date(self, date):
        DATETIME_FORMAT = "%Y-%m-%d"
        i_date = datetime.strptime(date, DATETIME_FORMAT)
        return i_date


    
    def make_purchase_line(self, values, pur_id):
        product_obj = self.env['product.product']
        account = False
        purchase_line_obj = self.env['purchase.order.line']
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if self.import_prod_option == 'barcode':
          product_search = product_obj.search([('barcode',  '=',values['product'])])
        elif self.import_prod_option == 'code':
            product_search = product_obj.search([('default_code', '=',values['product'])])
        else:
            product_search = product_obj.search([('name', '=',values['product'])])

        product_uom = self.env['uom.uom'].search([('name', '=', values.get('uom'))])
        if product_uom.id == False:
            raise Warning(_(' "%s" Product UOM category is not available.') % values.get('uom'))

        if product_search:
            product_id = product_search
        else:
            if self.import_prod_option == 'name':
                product_id = product_obj.create({
                                                    'name':values.get('product'),
                                                    'lst_price':values.get('price'),
                                                    'uom_id':product_uom.id,
                                                    'uom_po_id':product_uom.id
                                                 })
            else:
                raise Warning(_('%s product is not found" .\n If you want to create product then first select Import Product By Name option .') % values.get('product'))

        if pur_id.state == 'draft':
                po_order_lines = purchase_line_obj.create({
                                                    'order_id':pur_id.id,
                                                    'product_id':product_id.id,
                                                    'name':values.get('description'),
                                                    'date_planned':current_time,
                                                    'product_qty':values.get('quantity'),
                                                    'product_uom':product_uom.id,
                                                    'price_unit':values.get('price')
                                                    })
        elif pur_id.state == 'sent':
            po_order_lines = purchase_line_obj.create({
                                                'order_id':pur_id.id,
                                                'product_id':product_id.id,
                                                'name':values.get('description'),
                                                'date_planned':current_time,
                                                'product_qty':values.get('quantity'),
                                                'product_uom':product_uom.id,
                                                'price_unit':values.get('price')
                                                })
        elif pur_id.state != 'sent' or pur_id.state != 'draft':
            raise Warning(_('We cannot import data in validated or confirmed order.')) 

        tax_ids = []
        if values.get('tax'):
            if ';' in  values.get('tax'):
                tax_names = values.get('tax').split(';')
                for name in tax_names:
                    tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    tax_ids.append(tax.id)

            elif ',' in  values.get('tax'):
                tax_names = values.get('tax').split(',')
                for name in tax_names:
                    tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    tax_ids.append(tax.id)
            else:
                tax_names = values.get('tax').split(',')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    tax_ids.append(tax.id)
        tag_ids = []
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

        if tax_ids:
            po_order_lines.write({'taxes_id':([(6, 0, tax_ids)])})
        if tag_ids:
            po_order_lines.write({'analytic_tag_ids':([(6, 0, tag_ids)])})

        if values.get('analytic_account_id'):
            analytic_account_id = self.env['account.analytic.account'].search([('name','=',values.get('analytic_account_id'))])
            if analytic_account_id:
                analytic_account_id = analytic_account_id
                po_order_lines.write({
                'account_analytic_id' : analytic_account_id.id
                })
            else:
                raise Warning(_(' "%s" Analytic Account is not available.') % values.get('analytic_account_id'))
       

        return True

   
    def find_currency(self, name):
        currency_obj = self.env['res.currency']
        currency_search = currency_obj.search([('name', '=', name)])
        if currency_search:
            return currency_search
        else:
            raise Warning(_(' "%s" Currency are not available.') % name)

    
    def find_partner(self, name):
        partner_obj = self.env['res.partner']
        partner_search = partner_obj.search([('name', '=', name)])
        if partner_search:
            return partner_search
        else:
            partner_id = partner_obj.create({
                'name' : name})
            return partner_id

    
    def import_csv(self):
        """Load Inventory data from the CSV file."""
        if self.import_option == 'csv':
            try:
                keys = ['purchase_no', 'vendor', 'currency', 'product', 'quantity', 'uom', 'description', 'price','tax','date','analytic_account_id','analytic_Tag']
                csv_data = base64.b64decode(self.file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                file_reader = []
                purchase_ids = []
                csv_reader = csv.reader(data_file, delimiter=',')
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))
            values = {}
            for i in range(len(file_reader)):
                #                val = {}
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
                        values.update({'seq_opt':self.sequence_opt})
                        res = self.make_purchase(values)
                        purchase_ids.append(res)
                        
            if self.stage == 'confirm':
                for res in purchase_ids: 
                    if res.state in ['draft', 'sent']:
                        res.button_confirm()
        else:
            try:
                fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
                purchase_ids = []
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))

            product_obj = self.env['product.product']
            date_string = False
            for row_no in range(sheet.nrows):
                val = {}
                tax_line = ''
                if row_no <= 0:
                    line_fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    if line[9] != '':
                        a1 = int(float(line[9]))
                        a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                        date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                    values.update({'purchase_no':line[0],
                                   'vendor': line[1],
                                   'currency': line[2],
                                   'product': line[3].split('.')[0],
                                   'quantity': line[4],
                                   'uom': line[5],
                                   'description': line[6],
                                   'price': line[7],
                                   'tax': line[8],
                                   'analytic_account_id' : line[16],
                                    'analytic_Tag' : line[17],
                                   'date': date_string,
                                   'seq_opt':self.sequence_opt

                                   })
                    count = 0
                    for l_fields in line_fields:
                        if(count > 10):
                            values.update({l_fields : line[count]})                        
                        count+=1                        
                    res = self.make_purchase(values)
                    purchase_ids.append(res)
                    
            if self.stage == 'confirm':
                for res in purchase_ids: 
                    if res.state in ['draft', 'sent']:
                        res.button_confirm()
        return res

