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

   

class gen_purchase(models.TransientModel):
    _inherit = "gen.purchase"
    _description = "Gen Purchase"

    
    
    
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
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
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

            # pur_id = purchase_obj.create({
            #     'partner_id' : partner_id.id,
            #     'currency_id' : currency_id.id,
            #     'name':name,
            #     'date_order':pur_date,
            #     'custom_seq': True if values.get('seq_opt') == 'custom' else False,
            #     'system_seq': True if values.get('seq_opt') == 'system' else False,
            #     'purchase_name' : values.get('purchase_no'),
            #     'is_import' :True
            # })
            res = self.env.cr.execute("""INSERT INTO purchase_order (partner_id,currency_id,name,date_order,custom_seq,system_seq,purchase_name,company_id,state,picking_type_id,is_import) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""" , 
                (partner_id.id,currency_id.id,name,pur_date,True if values.get('seq_opt') == 'custom' else False,True if values.get('seq_opt') == 'system' else False,values.get('purchase_no'),company_id,'draft',types[:1].id,True))                                         
            pur_id = purchase_obj.search([],order='id desc', limit=1)
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
                # po_order_lines = purchase_line_obj.create({
                #                                     'order_id':pur_id.id,
                #                                     'product_id':product_id.id,
                #                                     'name':values.get('description'),
                #                                     'date_planned':current_time,
                #                                     'product_qty':values.get('quantity'),
                #                                     'product_uom':product_uom.id,
                #                                     'price_unit':values.get('price')
                #                                     })

                res = self.env.cr.execute("""INSERT INTO purchase_order_line (order_id,product_id,name,date_planned,product_qty,product_uom,price_unit,company_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""" , 
                (pur_id.id,product_id.id,values.get('description'),current_time,values.get('quantity'),product_uom.id,values.get('price'),pur_id.company_id.id) )                                        
                po_order_lines = purchase_line_obj.search([],order='id desc', limit=1)

        elif pur_id.state == 'sent':
            # po_order_lines = purchase_line_obj.create({
            #                                     'order_id':pur_id.id,
            #                                     'product_id':product_id.id,
            #                                     'name':values.get('description'),
            #                                     'date_planned':current_time,
            #                                     'product_qty':values.get('quantity'),
            #                                     'product_uom':product_uom.id,
            #                                     'price_unit':values.get('price')
            #                                     })

            res = self.env.cr.execute("""INSERT INTO purchase_order_line (order_id,product_id,name,date_planned,product_qty,product_uom,price_unit,company_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""" , 
                (pur_id.id,product_id.id,values.get('description'),current_time,values.get('quantity'),product_uom.id,values.get('price'),pur_id.company_id.id) )                                        
            po_order_lines = purchase_line_obj.search([],order='id desc', limit=1)
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

        if tax_ids:
            po_order_lines.write({'taxes_id':([(6, 0, tax_ids)])})

        return True

   
    