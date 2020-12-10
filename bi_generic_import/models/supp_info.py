# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

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

class gen_suppinfo(models.TransientModel):
    _name = "gen.suppinfo"
    _description = "Gen suppinfo"

    file = fields.Binary('File')
    create_link_option = fields.Selection([('create', 'Create product template if not available'),('link', 'Link with available product template')],string='Product Option',default='link')

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
            fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
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
                values.update( {'vendor':line[0],
                                'product': line[1],
                                'delivery_time': line[2],
                                'quantity': line[3],
                                'price': line[4],
                                'create_link_option':self.create_link_option,
                                })
                count = 0
                for l_fields in line_fields:
                    if(count > 4):
                        values.update({l_fields : line[count]})                        
                    count+=1                  
                res = self._create_product_suppinfo(values)
        return res

    
    def _create_product_suppinfo(self,values):
        name = self._find_vendor(values.get('vendor'))
        product_tmpl_id = self._find_product_template(values.get('product'),values.get('create_link_option'))
        if values.get('quantity'):
            min_qty = int(float(values.get('quantity')))
        else:
            min_qty = False
        if values.get('delivery_time'):
            delay = int(float(values.get('delivery_time')))
        else:
            delay = False
        vals = {
               'name':name,
               'product_tmpl_id':product_tmpl_id,
               'product_name': self.env['product.template'].browse(product_tmpl_id).name,
               'min_qty': min_qty,
               'price': values.get('price'),
               'delay': delay
               }    
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
        res = self.env['product.supplierinfo'].create(vals)
        return res


    
    def _find_vendor(self,name):
        partner_search = self.env['res.partner'].search([('name','=',name)])
        if not partner_search:
            raise Warning (_("%s Vendor Not Found") % name)
        return partner_search.id

    
    def _find_product_template(self,product,create_opt):
        product_tmpl_search = self.env['product.template'].search([('name','=',product)])
        if not product_tmpl_search:
            if create_opt == 'create':
                product_id = self.env['product.template'].create({'name':product})
                product_tmpl_search = product_id
            else:
                raise Warning (_(" You have selected Link product template with existing product but %s Product template does not exist") % product)
        return product_tmpl_search.id

