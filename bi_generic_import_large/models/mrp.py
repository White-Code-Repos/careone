# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime
import tempfile
import binascii
import xlrd
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, _
import logging
_logger = logging.getLogger(__name__)
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

class mrp_bom_inherit(models.Model):
    _inherit = "mrp.bom"

    is_import = fields.Boolean("import records" ,default = False)   

class gen_mrp(models.TransientModel):
    _inherit = "gen.mrp"
    _description = "Gen MRP"

    
    

    def make_bom(self, values):
        bom_obj = self.env['mrp.bom']
        product_tmpl_id = False
        bom_search = bom_obj.search([
                ('code', '=', values.get('ref'))
            ])
            
        if self.import_prod_option == 'barcode':
            product_obj_search=self.env['product.template'].search([('barcode',  '=',values.get('product_tmpl').split('.')[0])])
        elif self.import_prod_option == 'code':
            product_obj_search=self.env['product.template'].search([('default_code', '=',values.get('product_tmpl'))])
        else:
            product_obj_search=self.env['product.template'].search([('name', '=',values.get('product_tmpl'))])
            
        if product_obj_search:
            product_tmpl_id=product_obj_search
        else:
            raise Warning(_('%s product is not found.') % values.get('product_tmpl').split('.')[0])
            
        if bom_search:
            if  bom_search[0].code == values.get('ref'):
                if bom_search[0].product_tmpl_id.name != product_tmpl_id.name:
                   raise Warning(_('Found Diffrent value of product for same BOM %s') % product_tmpl_id)
                else:    
                    main_list = values.keys()
                    for i in main_list:
                        model_id = self.env['ir.model'].search([('model','=','mrp.bom')])           
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
                                                    bom_search[0].update({
                                                        technical_fields_name: fetch_m2o.id
                                                        })
                                                else:
                                                    raise Warning(_('"%s" This custom field value "%s" not available in system') % i , values.get(i))
                                        if many2x_fields.ttype =="many2many":
                                            m2m_value_lst = []
                                            if values.get(i):
                                                if ';' in values.get(i):
                                                    m2m_names = values.get(i).split(';')
                                                    for name in m2m_names:
                                                        m2m_id = self.env[many2x_fields.relation].search([('name', '=', name)])
                                                        if not m2m_id:
                                                            raise Warning(_('"%s" This custom field value "%s" not available in system') % i , name)
                                                        m2m_value_lst.append(m2m_id.id)

                                                elif ',' in values.get(i):
                                                    m2m_names = values.get(i).split(',')
                                                    for name in m2m_names:
                                                        m2m_id = self.env[many2x_fields.relation].search([('name', '=', name)])
                                                        if not m2m_id:
                                                            raise Warning(_('"%s" This custom field value "%s" not available in system') % i , name)
                                                        m2m_value_lst.append(m2m_id.id)

                                                else:
                                                    m2m_names = values.get(i).split(',')
                                                    m2m_id = self.env[many2x_fields.relation].search([('name', 'in', m2m_names)])
                                                    if not m2m_id:
                                                        raise Warning(_('"%s" This custom field value "%s" not available in system') % i , m2m_names)
                                                    m2m_value_lst.append(m2m_id.id)
                                            bom_search[0].update({
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
                                        bom_search[0].update({
                                            normal_details : values.get(i)
                                            })
                                    elif normal_fields.ttype == 'char':
                                        bom_search[0].update({
                                            normal_details : values.get(i)
                                            })                              
                                    elif normal_fields.ttype == 'float':
                                        if values.get(i) == '':
                                            float_value = 0.0
                                        else:
                                            float_value = float(values.get(i)) 
                                        bom_search[0].update({
                                            normal_details : float_value
                                            })                              
                                    elif normal_fields.ttype == 'integer':
                                        if values.get(i) == '':
                                            int_value = 0
                                        else:
                                            int_value = int(values.get(i)) 
                                        bom_search[0].update({
                                            normal_details : int_value
                                            })                            
                                    elif normal_fields.ttype == 'selection':
                                        bom_search[0].update({
                                            normal_details : values.get(i)
                                            })                              
                                    elif normal_fields.ttype == 'text':
                                        bom_search[0].update({
                                            normal_details : values.get(i)
                                            })                              
                                else:
                                    raise Warning(_('"%s" This custom field is not available in system') % normal_details)                                
                    self.make_bom_line(values, bom_search[0])
                return bom_search
            else:
                raise Warning(_('Found Diffrent value same BOM %s') % values.get('ref'))
        else:
            # bom_id = bom_obj.create({
            #     'product_tmpl_id' : product_tmpl_id.id,
            #     'code':values.get('ref'),
            #     'is_import' : True,
            #     'type':self.bom_type,
            #     'product_qty': values.get('qty')
            # })
            res = self.env.cr.execute("""INSERT INTO mrp_bom (product_tmpl_id,code,type,product_qty,product_uom_id,ready_to_produce,company_id,active,is_import) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""" , (product_tmpl_id.id, values.get('ref'),self.bom_type,
                    values.get('qty'),product_tmpl_id.uom_id.id,'asap',self.env.user.company_id.id,True,True))
            bom_id = self.env['mrp.bom'].search([],order='id desc', limit=1)
            main_list = values.keys()
            for i in main_list:
                model_id = self.env['ir.model'].search([('model','=','mrp.bom')])           
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
                                        bom_id.update({
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
                                bom_id.update({
                                    technical_fields_name : m2m_value_lst
                                    })                              
                        else:
                            raise Warning(_('"%s" This m2x custom field is not available in system') % technical_fields_name)
                    else:
                        normal_fields = self.env['ir.model.fields'].search([('name','=',normal_details),('state','=','manual'),('model_id','=',model_id.id)])
                        if normal_fields.id:
                            if normal_fields.ttype ==  'boolean':
                                bom_id.update({
                                    normal_details : values.get(i)
                                    })
                            elif normal_fields.ttype == 'char':
                                bom_id.update({
                                    normal_details : values.get(i)
                                    })                              
                            elif normal_fields.ttype == 'float':
                                if values.get(i) == '':
                                    float_value = 0.0
                                else:
                                    float_value = float(values.get(i)) 
                                bom_id.update({
                                    normal_details : float_value
                                    })                              
                            elif normal_fields.ttype == 'integer':
                                if values.get(i) == '':
                                    int_value = 0
                                else:
                                    int_value = int(values.get(i)) 
                                bom_id.update({
                                    normal_details : int_value
                                    })                             
                            elif normal_fields.ttype == 'selection':
                                bom_id.update({
                                    normal_details : values.get(i)
                                    })                              
                            elif normal_fields.ttype == 'text':
                                bom_id.update({
                                    normal_details : values.get(i)
                                    })                              
                        else:
                            raise Warning(_('"%s" This custom field is not available in system') % normal_details)            
            self.make_bom_line(values, bom_id)
            return bom_id

    
    def make_bom_line(self, values, bom_id):
        product_id = False
        product_obj = self.env['product.product']
        mrp_line_obj = self.env['mrp.bom.line']
        product_uom = self.env['uom.uom'].search([('name', '=', values.get('uom'))])
        if self.import_material_prod_option == 'barcode':
            product_obj_search=self.env['product.product'].search([('barcode',  '=',values.get('product').split('.')[0])])
        elif self.import_material_prod_option == 'code':
            product_obj_search=self.env['product.product'].search([('default_code', '=',values.get('product'))])
        else:
            product_obj_search=self.env['product.product'].search([('name', '=',values.get('product'))])
    
        if product_obj_search:
            product_id=product_obj_search
        else:
            raise Warning(_('%s product is not found.') % values.get('product'))
                
        if not product_uom:
            raise Warning(_(' "%s" Product UOM category is not available.') % values.get('uom'))
            
        # res = mrp_line_obj.create({
        #     'product_id' : product_id.id,
        #     'product_qty' : values.get('qty_l'),
        #     'bom_id' : bom_id.id,
        #     'product_uom_id':product_uom.id,
        #     })
        res = self.env.cr.execute("""INSERT INTO mrp_bom_line (product_id,product_qty,bom_id,product_uom_id) VALUES (%s,%s,%s,%s)""" , (product_id.id, values.get('qty_l'),bom_id.id,
                product_uom.id))
        res = self.env['mrp.bom.line'].search([],order='id desc', limit=1)
        return True

    
    def import_csv(self):
        """Load Inventory data from the CSV file."""

        if not self.file:
            raise exceptions.Warning(_("Please select file.!"))

        if self.import_option == 'csv':
            keys = ['product_tmpl', 'ref', 'qty', 'product', 'qty_l', 'uom', ]
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
                        values.update({'type':self.bom_type})
                        res = self.make_bom(values)
        else:
            try:
                fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
                workbook = xlrd.open_workbook(fp.name)
            
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.Warning(_("Invalid file"))

            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    line_fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    values.update( {'product_tmpl':line[0],
                                            'ref': line[1],
                                            'qty': line[2],
                                            'product': line[3],
                                            'qty_l': line[4],
                                            'uom': line[5],
                                             'type':self.bom_type
                                               })
                    count = 0
                    for l_fields in line_fields:
                        if(count > 5):
                            values.update({l_fields : line[count]})                        
                        count+=1                              
                    res = self.make_bom(values)
        return res

