# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from xlrd import open_workbook
import xlrd
import os
import tempfile
import binascii
from xlwt import Workbook
import xlwt
import logging
_logger = logging.getLogger(__name__)
from io import StringIO
import io

try:
    import xmlrpclib
except ImportError:
    _logger.debug('Cannot `import xmlrpclib`.')

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
# for xls 
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')

class gen_inv(models.TransientModel):
    _name = "gen.inv"
    _description = "Gen Inv"

    file = fields.Binary('File')
    inv_name = fields.Char('Inventory Name')
    location_ids = fields.Many2many('stock.location','rel_location_wizard',string= "Location")
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')
    import_prod_option = fields.Selection([('barcode', 'Barcode'),('code', 'Code'),('name', 'Name')],string='Import Product By ',default='code')
    lot_option = fields.Boolean(string="Import Serial/Lot number with Expiry Date")
    location_id_option = fields.Boolean(string="Allow to Import Location on inventory line from file")

    
    def import_csv(self):

        """Load Inventory data from the CSV file."""
        if self.import_option == 'csv': 
            """Load Inventory data from the CSV file."""
            try:
                if self.lot_option == True:
                    if self.location_id_option == True:
                        keys=['code', 'quantity','UOM','lot','life_date','line_location_id'] 
                    else:
                        keys=['code', 'quantity','UOM','lot','life_date']
                elif self.location_id_option == True:
                    keys=['code', 'quantity','UOM','lot','line_location_id']
                else:
                    keys=['code', 'quantity','UOM','lot'] 
                ctx = self._context
                stloc_obj = self.env['stock.location']
                inventory_obj = self.env['stock.inventory']
                product_obj = self.env['product.product']
                stock_lot_obj = self.env['stock.production.lot']
                csv_data = base64.b64decode(self.file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                file_reader = []
                csv_reader = csv.reader(data_file, delimiter=',')
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))
            values = {}
            inventory_id = self.env['stock.inventory'].create({'name':self.inv_name,'location_ids':self.location_ids.ids,'company_id' : self.env.user.company_id.id,'is_import' : True})
            product_list = []
            for i in range(len(file_reader)):
                val = {}
                try:
                     field = list(map(str, file_reader[i]))
                except ValueError:
                     raise exceptions.Warning(_("Don't Use Character only use numbers"))
                
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        if self.import_prod_option == 'barcode':
                            prod_lst = product_obj.search([('barcode',  '=',values['code'])]) 
                            if not prod_lst:
                                raise UserError(_('"%s" Product Barcode is not available.')%(values['code'] ))
                        
                        elif self.import_prod_option == 'code':
                            prod_lst = product_obj.search([('default_code', '=', values['code'])])
                            if not prod_lst:
                                raise UserError(_('"%s" Product Code is not available.')%(values['code'] ))
                        
                        else:
                            prod_lst = product_obj.search([('name', '=', values['code'])]) 

                        if prod_lst.id:
                            product_list.append(prod_lst.id)        
                        
                        if self.lot_option == True:
                            if self.location_id_option == True:
                                if prod_lst:
                                    val['product'] = prod_lst[0].id
                                    val['quantity'] = values['quantity']
                                    val['UOM'] = values['UOM']
                                    val['lot'] = values['lot']
                                    val['life_date'] = values['life_date']
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                                    if not product_uom_id:
                                        raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                        
                                    stock_location_id = self.env['stock.location'].search([('name','=',values['line_location_id'])])
                                    if not stock_location_id:
                                        raise UserError(_('"%s" Location is not available.')%(values['line_location_id']))

                                    lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)
                                        
                                    if not lot_id:
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                              'product_id': val['product'],
                                                                'life_date': val['life_date'],
                                                                'company_id' : self.env.user.company_id.id})
                                        lot_id = lot


                                    inventory_id.action_open_inventory_lines()
                                    lines = self.env['stock.inventory.line'].create({'product_id':val['product'] , 'inventory_id' : inventory_id.id ,'location_id' : stock_location_id.id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})

                                else:
                                    continue
                            else:
                                if prod_lst:
                                    val['product'] = prod_lst[0].id
                                    val['quantity'] = values['quantity']
                                    val['UOM'] = values['UOM']
                                    val['lot'] = values['lot']
                                    val['life_date'] = values['life_date']
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                                    if not product_uom_id:
                                        raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                        
                                    lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)
                                        
                                    if not lot_id:
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                              'product_id': val['product'],
                                                                'life_date': val['life_date'],
                                                                'company_id' : self.env.user.company_id.id})
                                        lot_id = lot

                                    inventory_id.action_open_inventory_lines()
                                    for l_id in self.location_ids:
                                        lines = self.env['stock.inventory.line'].create({'product_id':val['product'] , 'inventory_id' : inventory_id.id , 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id,'location_id':l_id.id})
                                
                                else:
                                    continue
                        else:
                            if self.location_id_option == True:
                                if prod_lst:
                                    val['product'] = prod_lst[0].id
                                    val['quantity'] = values['quantity']
                                    val['UOM'] = values['UOM']
                                    val['lot'] = values['lot']
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                                    if not product_uom_id:
                                        raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                        
                                    stock_location_id = self.env['stock.location'].search([('name','=',values['line_location_id'])])
                                    if not stock_location_id:
                                        raise UserError(_('"%s" Location is not available.')%(values['line_location_id']))

                                    lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)
                                        
                                    if not lot_id:
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                              'product_id': val['product'],
                                                              'company_id' : self.env.user.company_id.id})
                                        lot_id = lot


                                    inventory_id.action_open_inventory_lines()
                                    lines = self.env['stock.inventory.line'].create({'product_id':val['product'] , 'inventory_id' : inventory_id.id ,'location_id' : stock_location_id.id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})
                                
                                else:
                                    continue 
                            else:   
                                if prod_lst:
                                    val['product'] = prod_lst[0].id
                                    val['quantity'] = values['quantity']
                                    val['UOM'] = values['UOM']
                                    val['lot'] = values['lot']
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                                    if not product_uom_id:
                                        raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                        
                                    lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)
                                        
                                    if not lot_id:
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                              'product_id': val['product'],
                                                              'company_id' : self.env.user.company_id.id})
                                        lot_id = lot



                                    inventory_id.action_open_inventory_lines()
                                    for l_id in self.location_ids:
                                        lines = self.env['stock.inventory.line'].create({'product_id':val['product'] , 'inventory_id' : inventory_id.id , 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id,'location_id':l_id.id})
                                else:
                                    continue 
            inventory_id.product_ids = product_list
            res = inventory_obj.with_context(ids=inventory_id).prepare_inventory()
            return res
        else:
            try:
                fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))

            inventory_id = self.env['stock.inventory'].create({'name':self.inv_name,'location_ids':self.location_ids.ids,'company_id' : self.env.user.company_id.id,'is_import' : True})
            product_obj = self.env['product.product']
            stock_lot_obj = self.env['stock.production.lot']
            product_list= []
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    if self.lot_option == True:
                        if self.location_id_option == True:
                            if line:
                                values.update({'code':line[0],'quantity':line[1],'UOM':line[2],'lot':line[3],'life_date':line[4],'line_location_id':line[5]})
                                a1 = int(float(line[4]))
                                a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                                date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                                if self.import_prod_option == 'barcode':
                                    res = values['code'].replace('.', '', 1).isdigit() 
                                    if res == True:
                                        prod_lst = product_obj.search([('barcode','=',int(float(values['code'])))])
                                    else:
                                        prod_lst = product_obj.search([('barcode', '=', values['code'])]) 
                                
                                    if not prod_lst:
                                        raise UserError(_('"%s" Product Barcode is not available.')%(values['code'] ))
                                elif self.import_prod_option == 'code':
                                    res = values['code'].replace('.', '', 1).isdigit() 
                                    if res == True:
                                        prod_lst = product_obj.search([('default_code','=',int(float(values['code'])))])
                                    else:
                                        prod_lst = product_obj.search([('default_code', '=', values['code'])]) 
                                
                                    if not prod_lst:
                                        raise UserError(_('"%s" Product Code is not available.')%(values['code'] ))
                                else:
                                    prod_lst = product_obj.search([('name', '=', values['code'])])

                                if prod_lst:
                                    val['product'] = prod_lst[0].id
                                    val['quantity'] = values['quantity']
                                    val['UOM'] = values['UOM']
                                    val['lot'] = values['lot']
                                    val['life_date'] = date_string
                                    product_list.append(prod_lst.id)
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                                    if not product_uom_id:
                                        raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                        
                                    stock_location_id = self.env['stock.location'].search([('name','=',values['line_location_id'])])
                                    if not stock_location_id:
                                        raise UserError(_('"%s" Location is not available.')%(values['line_location_id']))

                                    lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)
                                
                                    if not lot_id:
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                      'product_id': val['product'],
                                                              'life_date': date_string,
                                                              'company_id' : self.env.user.company_id.id})
                                        lot_id = lot
                                    inventory_id.action_open_inventory_lines()
                                    lines = self.env['stock.inventory.line'].create({'product_id':val['product'] ,'inventory_id' : inventory_id.id, 'location_id' : stock_location_id.id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})
                                
                                else:
                                    continue
                        else:
                            if line:
                                values.update({'code':line[0],'quantity':line[1],'UOM':line[2],'lot':line[3],'life_date':line[4]})
                                if line[4]:
                                    a1 = int(float(line[4]))
                                    a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                                    date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                                else:
                                    date_string = False
                                if self.import_prod_option == 'barcode':
                                    res = values['code'].replace('.', '', 1).isdigit() 
                                    if res == True:
                                        prod_lst = product_obj.search([('barcode','=',int(float(values['code'])))])
                                    else:
                                        prod_lst = product_obj.search([('barcode', '=', values['code'])]) 
                                
                                    if not prod_lst:
                                        raise UserError(_('"%s" Product Barcode is not available.')%(values['code'] ))
                                elif self.import_prod_option == 'code':
                                    res = values['code'].replace('.', '', 1).isdigit() 
                                    if res == True:
                                        prod_lst = product_obj.search([('default_code','=',int(float(values['code'])))])
                                    else:
                                        prod_lst = product_obj.search([('default_code', '=', values['code'])]) 
                                
                                    if not prod_lst:
                                        raise UserError(_('"%s" Product Code is not available.')%(values['code'] ))
                                else:
                                    prod_lst = product_obj.search([('name', '=', values['code'])])            
                                if prod_lst:
                                    val['product'] = prod_lst[0].id
                                    val['quantity'] = values['quantity']
                                    val['UOM'] = values['UOM']
                                    val['lot'] = values['lot']
                                    val['life_date'] = date_string
                                    product_list.append(prod_lst.id)
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                                    if not product_uom_id:
                                        raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                        
                                    lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)
                                
                                    if not lot_id:
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                      'product_id': val['product'],
                                                              'life_date': date_string,
                                                              'company_id' : self.env.user.company_id.id})
                                        lot_id = lot


                                    inventory_id.action_open_inventory_lines()
                                    for l_id in self.location_ids:
                                        lines = self.env['stock.inventory.line'].create({'product_id':val['product'] ,'inventory_id' : inventory_id.id ,'location_id' : l_id.id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})
                                
                                else:
                                    continue
                    else:
                        if self.location_id_option == True:
                            if line:
                                values.update({'code':line[0],'quantity':line[1],'UOM':line[2],'lot':line[3],'line_location_id':line[4]})
                                if self.import_prod_option == 'barcode':
                                    res = values['code'].replace('.', '', 1).isdigit() 
                                    if res == True:
                                        prod_lst = product_obj.search([('barcode','=',int(float(values['code'])))])
                                    else:
                                        prod_lst = product_obj.search([('barcode', '=', values['code'])]) 
                                
                                    if not prod_lst:
                                        raise UserError(_('"%s" Product Barcode is not available.')%(values['code'] ))
                                elif self.import_prod_option == 'code':
                                    res = values['code'].replace('.', '', 1).isdigit() 
                                    if res == True:
                                        prod_lst = product_obj.search([('default_code','=',int(float(values['code'])))])
                                    else:
                                        prod_lst = product_obj.search([('default_code', '=', values['code'])]) 
                                
                                    if not prod_lst:
                                        raise UserError(_('"%s" Product Code is not available.')%(values['code'] ))
                                else:
                                    prod_lst = product_obj.search([('name', '=', values['code'])])            
                                if prod_lst:
                                    val['product'] = prod_lst[0].id
                                    val['quantity'] = values['quantity']
                                    val['UOM'] = values['UOM']
                                    val['lot'] = values['lot']
                                    product_list.append(prod_lst.id)
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                                    if not product_uom_id:
                                        raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                        
                                    stock_location_id = self.env['stock.location'].search([('name','=',values['line_location_id'])])
                                    if not stock_location_id:
                                        raise UserError(_('"%s" Location is not available.')%(values['line_location_id']))

                                    lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)
                                
                                    if not lot_id:
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                      'product_id': val['product'],
                                                      'company_id' : self.env.user.company_id.id})
                                        lot_id = lot

                                    inventory_id.action_open_inventory_lines()
                                    lines = self.env['stock.inventory.line'].create({'product_id':val['product'] ,'inventory_id' : inventory_id.id , 'location_id' : stock_location_id.id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})
                                
                                   
                                else:
                                    continue 
                        else:
                            if line:
                                values.update({'code':line[0],'quantity':line[1],'UOM':line[2],'lot':line[3]})
                                if self.import_prod_option == 'barcode':
                                    res = values['code'].replace('.', '', 1).isdigit() 
                                    if res == True:
                                        prod_lst = product_obj.search([('barcode','=',int(float(values['code'])))])
                                    else:
                                        prod_lst = product_obj.search([('barcode', '=', values['code'])]) 
                                
                                    if not prod_lst:
                                        raise UserError(_('"%s" Product Barcode is not available.')%(values['code'] ))
                                elif self.import_prod_option == 'code':
                                    res = values['code'].replace('.', '', 1).isdigit() 
                                    if res == True:
                                        prod_lst = product_obj.search([('default_code','=',int(float(values['code'])))])
                                    else:
                                        prod_lst = product_obj.search([('default_code', '=', values['code'])]) 
                                
                                    if not prod_lst:
                                        raise UserError(_('"%s" Product Code is not available.')%(values['code'] ))
                                else:
                                    prod_lst = product_obj.search([('name', '=', values['code'])])            
                                if prod_lst:
                                    val['product'] = prod_lst[0].id
                                    val['quantity'] = values['quantity']
                                    val['UOM'] = values['UOM']
                                    val['lot'] = values['lot']
                                    product_list.append(prod_lst.id)
                                if bool(val):
                                    product_uom_obj = self.env['uom.uom']
                                    product_uom_id = product_uom_obj.search([('name','=',val['UOM'])])
                                    if not product_uom_id:
                                        raise UserError(_('"%s" Product UOM category is not available.')%(val['UOM'] ))
                                        
                                    lot_id = stock_lot_obj.search([('product_id','=',val['product']),('name','=',val['lot'])])
                                    for lot in lot_id:
                                        lot_obj = stock_lot_obj.browse(lot_id)
                                
                                    if not lot_id:
                                        lot = stock_lot_obj.create({'name': val['lot'],
                                                      'product_id': val['product'],
                                                      'company_id' : self.env.user.company_id.id})
                                        lot_id = lot


                                    inventory_id.action_open_inventory_lines()
                                    for l_id in self.location_ids:
                                        lines = self.env['stock.inventory.line'].create({'product_id':val['product'] ,'inventory_id' : inventory_id.id , 'location_id' : l_id.id, 'product_uom_id' : product_uom_id.id  ,'product_qty': val['quantity'],'prod_lot_id':lot_id.id})
                                
                                else:
                                    continue    
            inventory_id.product_ids = product_list                        
            res = self.env['stock.inventory'].with_context(ids=inventory_id).prepare_inventory()
            return res

class stock_inventory(models.Model):
    _inherit = "stock.inventory"

    is_import = fields.Boolean(string = " Is Imported data" , default = False)
    
    def action_start(self):
        if self._context.get('ids'):
            self = self._context.get('ids')
            for inventory in self:
                vals = {'state': 'confirm', 'date': fields.Datetime.now()}
                vals.update({'line_ids': inventory.line_ids.ids})
                inventory.write(vals)
        else:
            super(stock_inventory, self).action_start()
        return True
    prepare_inventory = action_start

