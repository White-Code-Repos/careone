# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import logging
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




class gen_sale(models.TransientModel):
    _inherit = "gen.sale"
    _description = "Gen Sale"


    
    def make_sale(self, values):
        sale_obj = self.env['sale.order']
        if self.sequence_opt == "custom":
            sale_search = sale_obj.search([
                ('name', '=', values.get('order'))
            ])
        else:
            sale_search = sale_obj.search([
                ('sale_name', '=', values.get('order'))
            ])
        if sale_search:
            sale_search = sale_search[0]
            if sale_search.partner_id.name == values.get('customer'):
                if  sale_search.pricelist_id.name == values.get('pricelist'):
                    lines = self.make_order_line(values, sale_search)
                    vehicle= values.get('vehicle_id')
                    license_plate = values.get('license_plate')
                    vehicle_split = vehicle.split('/')

                    if len(vehicle_split) >= 2:
                        brand_id = self.env['fleet.vehicle.model.brand'].search([('name','=',vehicle_split[0])],limit=1)
                        model_id = self.env['fleet.vehicle.model'].search([('name','=',vehicle_split[1]),
                            ('brand_id','=',brand_id.id)],limit=1)
                        vehicle_id = self.env['fleet.vehicle'].search([
                            ('model_id','=',model_id.id),
                            ('license_plate','=',license_plate)])
                    elif len(vehicle_split) > 1:
                        vehicle_id = self.env['fleet.vehicle'].search([
                            ('model_id.name','ilike',vehicle_split[0]),
                            ('license_plate','=',license_plate)])
                    else:
                        vehicle_id = False

                    if vehicle_id:
                        self.env.cr.execute("update sale_order set vehicle_id=%s where id=%s", [vehicle_id.id,sale_search.id])
                        if vehicle_id:
                            vehicle_id.write({
                                'license_plate' : license_plate
                            })
                    return sale_search
                else:
                    raise Warning(_('Pricelist is different for "%s" .\n Please define same.') % values.get('order'))
            else:
                raise Warning(_('Customer name is different for "%s" .\n Please define same.') % values.get('order'))

        else:
            if values.get('seq_opt') == 'system':
                name = self.env['ir.sequence'].next_by_code('sale.order')
            elif values.get('seq_opt') == 'custom':
                name = values.get('order')
            partner_id = self.find_partner(values.get('customer'))
            currency_id = self.find_currency(values.get('pricelist'))
            user_id  = self.find_user(values.get('user'))
            order_date = self.make_order_date(values.get('date'))
            create_date = self.make_order_date(values.get('create_date',False))
            # sale_id = sale_obj.create({
            #     'partner_id' : partner_id.id,
            #     'pricelist_id' : currency_id.id,
            #     'name':name,
            #     'user_id': user_id.id,
            #     'date_order':order_date,
            #     'custom_seq': True if values.get('seq_opt') == 'custom' else False,
            #     'system_seq': True if values.get('seq_opt') == 'system' else False,
            #     'sale_name' : values.get('order'),
            #     'is_import' : True
            # })
            company = self.env.user.company_id.id
            warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
            res = self.env.cr.execute("""INSERT INTO sale_order (partner_id,pricelist_id,name,user_id,date_order,custom_seq,system_seq,sale_name,company_id,state,partner_invoice_id,partner_shipping_id,picking_policy,warehouse_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""" , 
                (partner_id.id,currency_id.id,name,user_id.id,order_date,True if values.get('seq_opt') == 'custom' else False,True if values.get('seq_opt') == 'system' else False,values.get('order'),
                    self.env.user.company_id.id,'draft',partner_id.id,partner_id.id,'direct',warehouse_ids.id))                                         
            sale_id = sale_obj.search([],order='id desc', limit=1)
            if create_date:
                self.env.cr.execute("update sale_order set create_date=%s where id=%s", [create_date,sale_id.id])
            
            main_list = values.keys()
            # count = 0
            for i in main_list:
                model_id = self.env['ir.model'].search([('model','=','sale.order')])           
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
                                            sale_id.update({
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
                                    sale_id.update({
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
                                sale_id.update({
                                    normal_details : values.get(i)
                                    })
                            elif normal_fields.ttype == 'char':
                                sale_id.update({
                                    normal_details : values.get(i)
                                    })                              
                            elif normal_fields.ttype == 'float':
                                if values.get(i) == '':
                                    float_value = 0.0
                                else:
                                    float_value = float(values.get(i)) 
                                sale_id.update({
                                    normal_details : float_value
                                    })                              
                            elif normal_fields.ttype == 'integer':
                                if values.get(i) == '':
                                    int_value = 0
                                else:
                                    int_value = int(values.get(i)) 
                                sale_id.update({
                                    normal_details : int_value
                                    })                              
                            elif normal_fields.ttype == 'selection':
                                sale_id.update({
                                    normal_details : values.get(i)
                                    })                              
                            elif normal_fields.ttype == 'text':
                                sale_id.update({
                                    normal_details : values.get(i)
                                    })                              
                        else:
                            raise Warning(_('"%s" This custom field is not available in system') % normal_details)
            # count+= 1         
            lines = self.make_order_line(values, sale_id)
            vehicle= values.get('vehicle_id')
            license_plate = values.get('license_plate')
            vehicle_split = vehicle.split('/')

            if len(vehicle_split) >= 2:
                brand_id = self.env['fleet.vehicle.model.brand'].search([('name','=',vehicle_split[0])],limit=1)
                model_id = self.env['fleet.vehicle.model'].search([('name','=',vehicle_split[1]),
                    ('brand_id','=',brand_id.id)],limit=1)
                vehicle_id = self.env['fleet.vehicle'].search([
                    ('model_id','=',model_id.id),
                    ('license_plate','=',license_plate)])
            elif len(vehicle_split) > 1:
                vehicle_id = self.env['fleet.vehicle'].search([
                    ('model_id.name','ilike',vehicle_split[0]),
                    ('license_plate','=',license_plate)])
            else:
                vehicle_id = False

            if vehicle_id:
                self.env.cr.execute("update sale_order set vehicle_id=%s where id=%s", [vehicle_id.id,sale_id.id])

                vehicle_id.write({
                    'license_plate' : license_plate
                })
            return sale_id

    
    def make_order_line(self, values, sale_id):
        product_obj = self.env['product.product']
        order_line_obj = self.env['sale.order.line']
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
            product_id = product_search[0]
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

        tax_ids = []
        if values.get('tax'):
            if ';' in  values.get('tax'):
                tax_names = values.get('tax').split(';')
                for name in tax_names:
                    tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    tax_ids.append(tax.id)

            elif ',' in  values.get('tax'):
                tax_names = values.get('tax').split(',')
                for name in tax_names:
                    tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    tax_ids.append(tax.id)
            else:
                tax_names = values.get('tax').split(',')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'sale')])
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

        # so_order_lines = order_line_obj.create({
        #                                     'order_id':sale_id.id,
        #                                     'product_id':product_id.id,
        #                                     'name':values.get('description'),
        #                                     'product_uom_qty':values.get('quantity'),
        #                                     'product_uom':product_uom.id,
        #                                     'price_unit':values.get('price'),
        #                                     'discount':values.get('disc')

        #                                     })
        res = self.env.cr.execute("""INSERT INTO sale_order_line (order_id,product_id,name,product_uom_qty,product_uom,price_unit,company_id,customer_lead,discount) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""" , 
                (sale_id.id,product_id.id,values.get('description'),values.get('quantity'),product_uom.id,values.get('price'),sale_id.company_id.id,0.0,values.get('disc')) )                                        
        so_order_lines = order_line_obj.search([],order='id desc', limit=1)
        if tag_ids:
            so_order_lines.write({'analytic_tag_ids' : [(6, 0, tag_ids)]})
        if values.get('analytic_account_id'):
            analytic_account_id = self.env['account.analytic.account'].search([('name','=',values.get('analytic_account_id'))])
            if analytic_account_id:
                analytic_account_id = analytic_account_id
                self.env.cr.execute("update sale_order set analytic_account_id=%s where id=%s", [analytic_account_id.id,sale_id.id])
                    
            else:
                raise Warning(_(' "%s" Analytic Account is not available.') % values.get('analytic_account_id'))

        if tax_ids:
            so_order_lines.write({'tax_id':([(6,0,tax_ids)])})
        return True

    def import_sale(self):

        """Load Inventory data from the CSV file."""
        if self.import_option == 'csv':
            try:
                keys = ['order', 'customer', 'pricelist','product', 'quantity', 'uom', 'description', 'price','user','tax','date','disc','create_date','vehicle_id','license_plate','analytic_account_id','analytic_Tag']
                csv_data = base64.b64decode(self.file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                file_reader = []
                sale_ids = []
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
                        if values.get('date') == '':
                            raise Warning(_("Please assign date."))

                        values.update({'seq_opt':self.sequence_opt})
                        res = self.make_sale(values)
                        date_string = values.get('date_string')
                        sale_ids.append([res,date_string])
            if self.stage == 'confirm':
                for res in sale_ids: 
                    if res[0].state in ['draft', 'sent']:
                        res[0].action_confirm()
                        self.env.cr.execute("update sale_order set date_order=%s where id=%s", [res[1],res[0].id])

        else:
            try:
                fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
                sale_ids = []
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))

            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    line_fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    if line[10] != '':                  
                        a1 = int(float(line[10]))
                        a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                        date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                    else:
                        raise Warning(_("Please assign date."))

                    if line[12] != '':                  
                        a1 = int(float(line[12]))
                        a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                        create_date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                    else:
                        create_date_string = ''
                    
                    
                    values.update( {'order':line[0],
                                    'customer': line[1],
                                    'pricelist': line[2],
                                    'product': line[3],
                                    'quantity': line[4],
                                    'uom': line[5],
                                    'description': line[6],
                                    'price': line[7],
                                    'user': line[8],
                                    'tax': line[9],
                                    'date':date_string,
                                    'create_date' : create_date_string,
                                    'seq_opt':self.sequence_opt,
                                    'disc':line[11],
                                    'vehicle_id' : line[13],
                                    'analytic_account_id' : line[15],
                                    'analytic_Tag' : line[16],
                                    'license_plate' : line[14],
                                    })
                    count = 0
                    for l_fields in line_fields:
                        if(count > 13):
                            values.update({l_fields : line[count]})                        
                        count+=1            
                    res = self.make_sale(values)
                    sale_ids.append([res,date_string])
            
            if self.stage == 'confirm':
                for res in sale_ids: 
                    if res[0].state in ['draft', 'sent']:
                        res[0].action_confirm()
                        self.env.cr.execute("update sale_order set date_order=%s where id=%s", [res[1],res[0].id])
        return res



    
    
