# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _,exceptions
from datetime import datetime
from odoo.exceptions import Warning
import binascii
import tempfile
from tempfile import TemporaryFile
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
import io
import re
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')
try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')
    
class import_po_line_wizard(models.TransientModel):

    _inherit='import.po.line.wizard'
    _description = "Import Po Line Wizard"

    purchase_order_file=fields.Binary(string="Select File")
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')
    import_prod_option = fields.Selection([('barcode', 'Barcode'),('code', 'Code'),('name', 'Name')],string='Import Product By ',default='name')
    product_details_option = fields.Selection([('from_product','Take Details From The Product'),('from_xls','Take Details From The XLS File'),('from_pricelist','Take Details With Adapted Pricelist')],default='from_xls')

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
    
    def import_pol(self):
        if self.import_option == 'csv':
            try:
                keys = ['code', 'quantity', 'uom','description', 'price', 'tax']
                csv_data = base64.b64decode(self.purchase_order_file)
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
                        res = self.create_po_line(values)
        else:
            try:
                fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.purchase_order_file))
                fp.seek(0)
                values = {}
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))

            product_obj = self.env['product.product']
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    line_fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    if self.product_details_option == 'from_product':
                        values.update({
                                'code' : line[0].split('.')[0],
                                'quantity' : line[1]
                        })
                    elif self.product_details_option == 'from_xls':
                        values.update({
                           'code':line[0].split('.')[0],
                           'quantity':line[1],
                           'uom':line[2],
                           'description':line[3],
                           'price':line[4],
                           'tax':line[5],
                             })
                    else:
                        values.update({
                                        'code' : line[0].split('.')[0],
                                        'quantity' : line[1],
                                    })                        
                    count = 0
                    for l_fields in line_fields:
                        if(count > 6):
                            values.update({l_fields : line[count]})                        
                        count+=1    

                    res = self.create_po_line(values)
        return res

    
    def create_po_line(self,values):
        purchase_order_brw=self.env['purchase.order'].browse(self._context.get('active_id'))
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        product=values.get('code')
        po_order_lines = False

        if self.product_details_option == 'from_product':
            if self.import_prod_option == 'barcode':
              product_obj_search=self.env['product.product'].search([('barcode',  '=',values['code'])])
            elif self.import_prod_option == 'code':
                product_obj_search=self.env['product.product'].search([('default_code', '=',values['code'])])
            else:
                product_obj_search=self.env['product.product'].search([('name', '=',values['code'])])
    
            if product_obj_search:
                product_id=product_obj_search
            else:
                raise Warning(_('%s product is not found".') % values.get('code'))

            if purchase_order_brw.state in ('draft','sent'):
                for line in purchase_order_brw.order_line:
                    if line.product_id.id == product_id.id:
                        po_order_lines = line

                if po_order_lines:
                    if values.get('quantity') != '':
                        po_order_lines.write({
                            'product_qty': po_order_lines.product_qty + float(values.get('quantity')),
                            })
                else:
                    # po_order_lines=self.env['purchase.order.line'].create({
                    #                                     'order_id':purchase_order_brw.id,
                    #                                     'product_id':product_id.id,
                    #                                     'name':product_id.name,
                    #                                     'date_planned':current_time,
                    #                                     'product_qty':values.get('quantity'),
                    #                                     'product_uom':product_id.uom_id.id,
                    #                                     'price_unit':product_id.lst_price
                    #                                     })  

                    res = self.env.cr.execute("""INSERT INTO purchase_order_line (product_id,product_qty,order_id,name,price_unit,product_uom,date_planned) VALUES (%s,%s,%s,%s,%s,%s,%s)""" , (product_id.id, values.get('quantity'),purchase_order_brw.id,
                    product_id.name,product_id.lst_price,product_id.uom_id.id,current_time))
                    po_order_lines = self.env['purchase.order.line'].search([],order='id desc', limit=1)                 


                    main_list = values.keys()
                    for i in main_list:
                        model_id = self.env['ir.model'].search([('model','=','purchase.order.line')])           
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
                                                    po_order_lines.update({
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
                                            po_order_lines.update({
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
                                        po_order_lines.update({
                                            normal_details : values.get(i)
                                            })
                                    elif normal_fields.ttype == 'char':
                                        po_order_lines.update({
                                            normal_details : values.get(i)
                                            })                              
                                    elif normal_fields.ttype == 'float':
                                        if values.get(i) == '':
                                            float_value = 0.0
                                        else:
                                            float_value = float(values.get(i)) 
                                        po_order_lines.update({
                                            normal_details : float_value
                                            })                              
                                    elif normal_fields.ttype == 'integer':
                                        if values.get(i) == '':
                                            int_value = 0
                                        else:
                                            int_value = int(values.get(i)) 
                                        po_order_lines.update({
                                            normal_details : int_value
                                            })                               
                                    elif normal_fields.ttype == 'selection':
                                        po_order_lines.update({
                                            normal_details : values.get(i)
                                            })                              
                                    elif normal_fields.ttype == 'text':
                                        po_order_lines.update({
                                            normal_details : values.get(i)
                                            })                              
                                else:
                                    raise Warning(_('"%s" This custom field is not available in system') % normal_details)                                                                    
            else:
                raise UserError(_('We cannot import data in validated or confirmed order.'))

        elif self.product_details_option == 'from_xls':
            uom=values.get('uom')
            if self.import_prod_option == 'barcode':
              product_obj_search=self.env['product.product'].search([('barcode',  '=',values['code'])])
            elif self.import_prod_option == 'code':
                product_obj_search=self.env['product.product'].search([('default_code', '=',values['code'])])
            else:
                product_obj_search=self.env['product.product'].search([('name', '=',values['code'])])

            uom_obj_search=self.env['uom.uom'].search([('name','=',uom)])
            tax_id_lst=[]
            if values.get('tax'):
                if ';' in values.get('tax'):
                    tax_names = values.get('tax').split(';')
                    for name in tax_names:
                        tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                        if not tax:
                            raise Warning(_('"%s" Tax not in your system') % name)
                        tax_id_lst.append(tax.id)

                elif ',' in values.get('tax'):
                    tax_names = values.get('tax').split(',')
                    for name in tax_names:
                        tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                        if not tax:
                            raise Warning(_('"%s" Tax not in your system') % name)
                        tax_id_lst.append(tax.id)
                else:
                    tax_names = values.get('tax').split(',')
                    tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % tax_names)
                    tax_id_lst.append(tax.id)

            if not uom_obj_search:
                raise Warning(_('UOM "%s" is Not Available') % uom)

            if product_obj_search:
                product_id=product_obj_search
            else:
                if self.import_prod_option == 'name':
                    product_id=self.env['product.product'].create({'name':product,'lst_price':values.get('price')})
                else:
                    raise Warning(_('%s product is not found" .\n If you want to create product then first select Import Product By Name option .') % values.get('code'))
            

            if purchase_order_brw.state in ('draft','sent'):
                for line in purchase_order_brw.order_line:
                    if line.product_id.id == product_id.id:
                        po_order_lines = line

                if po_order_lines:
                    if values.get('quantity') != '':
                        po_order_lines.write({
                                'name': values.get('description'),
                                'product_qty': po_order_lines.product_qty + float(values.get('quantity')),
                                'product_uom':uom_obj_search.id or False,
                                'date_planned':current_time,
                                'price_unit':float(values.get('price'))
                            })
                        main_list = values.keys()
                        for i in main_list:
                            model_id = self.env['ir.model'].search([('model','=','purchase.order.line')])           
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
                                        if many2x_fields.ttype =="many2one":
                                            if values.get(i):
                                                fetch_m2o = self.env[many2x_fields.relation].search([('name','=',values.get(i))])
                                                if fetch_m2o.id:
                                                    po_order_lines.update({
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
                                            po_order_lines.update({
                                                technical_fields_name : m2m_value_lst
                                                })                              
                                    else:
                                        raise Warning(_('"%s" This m2x custom field is not available in system') % technical_fields_name)
                                else:
                                    normal_fields = self.env['ir.model.fields'].search([('name','=',normal_details),('state','=','manual'),('model_id','=',model_id.id)])
                                    if normal_fields.id:
                                        if normal_fields.ttype ==  'boolean':
                                            po_order_lines.update({
                                                normal_details : values.get(i)
                                                })
                                        elif normal_fields.ttype == 'char':
                                            po_order_lines.update({
                                                normal_details : values.get(i)
                                                })                              
                                        elif normal_fields.ttype == 'float':
                                            if values.get(i) == '':
                                                float_value = 0.0
                                            else:
                                                float_value = float(values.get(i)) 
                                            po_order_lines.update({
                                                normal_details : float_value
                                                })                              
                                        elif normal_fields.ttype == 'integer':
                                            if values.get(i) == '':
                                                int_value = 0
                                            else:
                                                int_value = int(values.get(i)) 
                                            po_order_lines.update({
                                                normal_details : int_value
                                                })                         
                                        elif normal_fields.ttype == 'selection':
                                            po_order_lines.update({
                                                normal_details : values.get(i)
                                                })                              
                                        elif normal_fields.ttype == 'text':
                                            po_order_lines.update({
                                                normal_details : values.get(i)
                                                })                              
                                    else:
                                        raise Warning(_('"%s" This custom field is not available in system') % normal_details)                        
                else:
                    # po_order_lines=self.env['purchase.order.line'].create({
                    #                                     'order_id':purchase_order_brw.id,
                    #                                     'product_id':product_id.id,
                    #                                     'name':values.get('description'),
                    #                                     'date_planned':current_time,
                    #                                     'product_qty':values.get('quantity'),
                    #                                     'product_uom':uom_obj_search.id or False,
                    #                                     'price_unit':values.get('price')
                    #                                     })

                    res = self.env.cr.execute("""INSERT INTO purchase_order_line (product_id,product_qty,order_id,name,price_unit,product_uom,date_planned) VALUES (%s,%s,%s,%s,%s,%s,%s)""" , (product_id.id, values.get('quantity'),purchase_order_brw.id,
                    product,float(values.get('price')),uom_obj_search.id,current_time))
                    po_order_lines = self.env['purchase.order.line'].search([],order='id desc', limit=1)

                    main_list = values.keys()
                    for i in main_list:
                        model_id = self.env['ir.model'].search([('model','=','purchase.order.line')])           
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
                                    if many2x_fields.ttype =="many2one":
                                        if values.get(i):
                                            fetch_m2o = self.env[many2x_fields.relation].search([('name','=',values.get(i))])
                                            if fetch_m2o.id:
                                                po_order_lines.update({
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
                                        po_order_lines.update({
                                            technical_fields_name : m2m_value_lst
                                            })                              
                                else:
                                    raise Warning(_('"%s" This m2x custom field is not available in system') % technical_fields_name)
                            else:
                                normal_fields = self.env['ir.model.fields'].search([('name','=',normal_details),('state','=','manual'),('model_id','=',model_id.id)])
                                if normal_fields.id:
                                    if normal_fields.ttype ==  'boolean':
                                        po_order_lines.update({
                                            normal_details : values.get(i)
                                            })
                                    elif normal_fields.ttype == 'char':
                                        po_order_lines.update({
                                            normal_details : values.get(i)
                                            })                              
                                    elif normal_fields.ttype == 'float':
                                        if values.get(i) == '':
                                            float_value = 0.0
                                        else:
                                            float_value = float(values.get(i)) 
                                        po_order_lines.update({
                                            normal_details : float_value
                                            })                              
                                    elif normal_fields.ttype == 'integer':
                                        if values.get(i) == '':
                                            int_value = 0
                                        else:
                                            int_value = int(values.get(i)) 
                                        po_order_lines.update({
                                            normal_details : int_value
                                            })                            
                                    elif normal_fields.ttype == 'selection':
                                        po_order_lines.update({
                                            normal_details : values.get(i)
                                            })                              
                                    elif normal_fields.ttype == 'text':
                                        po_order_lines.update({
                                            normal_details : values.get(i)
                                            })                              
                                else:
                                    raise Warning(_('"%s" This custom field is not available in system') % normal_details)                                                                                        
            else:
                raise UserError(_('We cannot import data in validated or confirmed order.'))
            
            if tax_id_lst:
                po_order_lines.write({'taxes_id':([(6,0,tax_id_lst)])})
        else:
            if self.import_prod_option == 'barcode':
              product_obj_search=self.env['product.product'].search([('barcode',  '=',values['code'])])
            elif self.import_prod_option == 'code':
                product_obj_search=self.env['product.product'].search([('default_code', '=',values['code'])])
            else:
                product_obj_search=self.env['product.product'].search([('name', '=',values['code'])])

            if product_obj_search:
                product_id=product_obj_search
            else:
                if self.import_prod_option == 'name':
                    product_id=self.env['product.product'].create({'name':product,'lst_price':float(values.get('price'))})
                else:
                    raise Warning(_('%s product is not found" .\n If you want to create product then first select Import Product By Name option .') % values.get('code'))
            
            if purchase_order_brw.state in ('draft','sent'):
                for line in purchase_order_brw.order_line:
                    if line.product_id.id == product_id.id:
                        po_order_lines = line

                if po_order_lines:
                    if values.get('quantity') != '':
                        po_order_lines.write({
                                'name':values['code'],
                                'date_planned':current_time,
                                'product_qty': po_order_lines.product_qty + float(values.get('quantity')),
                                'product_uom':product_id.uom_id.id,
                                'price_unit':product_id.lst_price
                            })
                        main_list = values.keys()
                        for i in main_list:
                            model_id = self.env['ir.model'].search([('model','=','purchase.order.line')])           
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
                                        if many2x_fields.ttype =="many2one":
                                            if values.get(i):
                                                fetch_m2o = self.env[many2x_fields.relation].search([('name','=',values.get(i))])
                                                if fetch_m2o.id:
                                                    po_order_lines.update({
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
                                            po_order_lines.update({
                                                technical_fields_name : m2m_value_lst
                                                })                              
                                    else:
                                        raise Warning(_('"%s" This m2x custom field is not available in system') % technical_fields_name)
                                else:
                                    normal_fields = self.env['ir.model.fields'].search([('name','=',normal_details),('state','=','manual'),('model_id','=',model_id.id)])
                                    if normal_fields.id:
                                        if normal_fields.ttype ==  'boolean':
                                            po_order_lines.update({
                                                normal_details : values.get(i)
                                                })
                                        elif normal_fields.ttype == 'char':
                                            po_order_lines.update({
                                                normal_details : values.get(i)
                                                })                              
                                        elif normal_fields.ttype == 'float':
                                            if values.get(i) == '':
                                                float_value = 0.0
                                            else:
                                                float_value = float(values.get(i)) 
                                            po_order_lines.update({
                                                normal_details : float_value
                                                })                              
                                        elif normal_fields.ttype == 'integer':
                                            if values.get(i) == '':
                                                int_value = 0
                                            else:
                                                int_value = int(values.get(i)) 
                                            po_order_lines.update({
                                                normal_details : int_value
                                                })                              
                                        elif normal_fields.ttype == 'selection':
                                            po_order_lines.update({
                                                normal_details : values.get(i)
                                                })                              
                                        elif normal_fields.ttype == 'text':
                                            po_order_lines.update({
                                                normal_details : values.get(i)
                                                })                              
                                    else:
                                        raise Warning(_('"%s" This custom field is not available in system') % normal_details)                        

                else:
                    # po_order_lines=self.env['purchase.order.line'].create({
                    #                                 'order_id':purchase_order_brw.id,
                    #                                 'product_id':product_id.id,
                    #                                 'name':values['code'],
                    #                                 'date_planned':current_time,
                    #                                 'product_qty':values.get('quantity'),
                    #                                 'product_uom':product_id.uom_id.id,
                    #                                 'price_unit':product_id.lst_price
                    #                                 })

                    res = self.env.cr.execute("""INSERT INTO purchase_order_line (product_id,product_qty,order_id,name,price_unit,product_uom,date_planned) VALUES (%s,%s,%s,%s,%s,%s,%s)""" , (product_id.id, values.get('quantity'),purchase_order_brw.id,
                    values['code'],product_id.lst_price,uom_obj_search.id,current_time))
                    po_order_lines = self.env['purchase.order.line'].search([],order='id desc', limit=1)
                

                po_order_lines.onchange_product_id() 
                main_list = values.keys()
                for i in main_list:
                    model_id = self.env['ir.model'].search([('model','=','purchase.order.line')])           
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
                                if many2x_fields.ttype =="many2one":
                                    if values.get(i):
                                        fetch_m2o = self.env[many2x_fields.relation].search([('name','=',values.get(i))])
                                        if fetch_m2o.id:
                                            po_order_lines.update({
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
                                    po_order_lines.update({
                                        technical_fields_name : m2m_value_lst
                                        })                              
                            else:
                                raise Warning(_('"%s" This m2x custom field is not available in system') % technical_fields_name)
                        else:
                            normal_fields = self.env['ir.model.fields'].search([('name','=',normal_details),('state','=','manual'),('model_id','=',model_id.id)])
                            if normal_fields.id:
                                if normal_fields.ttype ==  'boolean':
                                    po_order_lines.update({
                                        normal_details : values.get(i)
                                        })
                                elif normal_fields.ttype == 'char':
                                    po_order_lines.update({
                                        normal_details : values.get(i)
                                        })                              
                                elif normal_fields.ttype == 'float':
                                    if values.get(i) == '':
                                        float_value = 0.0
                                    else:
                                        float_value = float(values.get(i)) 
                                    po_order_lines.update({
                                        normal_details : float_value
                                        })                              
                                elif normal_fields.ttype == 'integer':
                                    if values.get(i) == '':
                                        int_value = 0
                                    else:
                                        int_value = int(values.get(i)) 
                                    po_order_lines.update({
                                        normal_details : int_value
                                        })                             
                                elif normal_fields.ttype == 'selection':
                                    po_order_lines.update({
                                        normal_details : values.get(i)
                                        })                              
                                elif normal_fields.ttype == 'text':
                                    po_order_lines.update({
                                        normal_details : values.get(i)
                                        })                              
                            else:
                                raise Warning(_('"%s" This custom field is not available in system') % normal_details)                                                                                    
                po_order_lines.update({
                                    'product_qty':values.get('quantity'),
                    })                                                    
            else:
                raise UserError(_('We cannot import data in validated or confirmed order.'))              
        
        return True
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
