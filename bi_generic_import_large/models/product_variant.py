# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import tempfile
import binascii
import xlrd
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api,tools, _
import time
from datetime import date, datetime
import io
import logging

import urllib
import base64
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

class gen_product_variant(models.TransientModel):
    _name = "gen.product.variant"

    file = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')
    product_option = fields.Selection([('create','Create Product'),('update','Update Product')],string='Option', required=True,default="create")
    product_search = fields.Selection([('by_code','Search By Code'),('by_barcode','Search By Barcode')],string='Search Product')

    @api.multi
    def create_product_variant(self,values):
        product_tmpl_obj = self.env['product.template']
        # product_obj = self.env['product.product']
        product_categ_obj = self.env['product.category']
        product_uom_obj = self.env['uom.uom']
        taxes = self.env['account.tax']
        attribute_id = self.env['product.attribute']
        value_id = self.env['product.attribute.value']
        attibute_value = self.env['product.template.attribute.line']
        att_vals = []

        if values.get('sale_ok')=="1":
            sale_ok = True
        elif values.get('sale_ok')=="1.0":
            sale_ok = True
        else:
            sale_ok = False

        if values.get('purchase_ok')=="1":
            purchase_ok = True
        elif values.get('purchase_ok')=="1.0":
            purchase_ok = True
        else:
            purchase_ok = False

        if values.get('barcode') == '':
            barcode = False
        else:
            barcode = values.get('barcode')
            barcode = barcode.split('.')

        if values.get('attribute_id')=='':
            attribute_id = ''
        else:
            attribute_id =attribute_id.search([('name','=',values.get('attribute_id'))])

        if values.get('on_hand') == '':
            quantity = False
        else:
            quantity = values.get('on_hand')

        tax_id_lst = []
        if values.get('taxes_id'):
            if ';' in values.get('taxes_id'):
                tax_names = values.get('taxes_id').split(';')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'sale')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    tax_id_lst.append(tax.id)

            elif ',' in values.get('taxes_id'):
                tax_names = values.get('taxes_id').split(',')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'sale')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    tax_id_lst.append(tax.id)

            else:
                tax_names = values.get('taxes_id').split(',')
                tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'sale')])
                if not tax:
                    raise Warning(_('"%s" Tax not in your system') % tax_names)
                tax_id_lst.append(tax.id)

        if values.get('image'):
            # image_name = values.get('image').encode('ascii')


            image = urllib.request.urlopen(values.get('image')).read()

            image_base64 = base64.encodestring(image)

            image_medium = image_base64 
            # image_path = tools.image_resize_image_big(base64.b64encode(open(image_base64, 'rb').read()))
        else:
            image_medium = False

        supplier_taxes_id = []
        if values.get('supplier_taxes_id'):
            if ';' in values.get('supplier_taxes_id'):
                tax_names = values.get('supplier_taxes_id').split(';')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    supplier_taxes_id.append(tax.id)

            elif ',' in values.get('supplier_taxes_id'):
                tax_names = values.get('supplier_taxes_id').split(',')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    supplier_taxes_id.append(tax.id)

            else:
                tax_names = values.get('supplier_taxes_id').split(',')
                tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'purchase')])
                if not tax:
                    raise Warning(_('"%s" Tax not in your system') % tax_names)
                supplier_taxes_id.append(tax.id)
        

        res = product_tmpl_obj.search([('name','=',values.get('name'))])
        attrs = []
        val_list = False
        attr_list = []
        if res.attribute_line_ids:
            for i in res.attribute_line_ids:
                if i.value_ids:
                    val_list = i.value_ids.ids
        
        
        

        if res.attribute_line_ids:
            for i in res.attribute_line_ids:
                if i.attribute_id.id == attribute_id.id:
                    if values.get('value_id')=='':
                        value_id = ''
                    else:
                        value_id = value_id.search([('name','=',values.get('value_id'))])
                        val_list.append(value_id.id)
                        i.value_ids = [(6,0,val_list)]
                else:
                    if values.get('value_id')=='':
                        value_id = ''
                    else:
                        value_id = value_id.search([('name','=',values.get('value_id'))])
                        # value_id._set_product_template_value_ids()
                        att_vals.append(value_id.id)
                    attrs = []
                    attrs.append((0,0,{
                        'product_tmpl_id':res.id,
                        'attribute_id':attribute_id.id,
                        'value_ids':[(6,0,att_vals)]
                        }))
                    res.write({
                        'attribute_line_ids' : attrs 
                        })
        res.create_variant_ids()
        product_obj =self.env['product.product'].search([],order='id desc',limit=1)
        if product_obj.type=='product':
            company_user = self.env.user.company_id
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
            product = product_obj.with_context(location=warehouse.view_location_id.id)
            th_qty = product_obj.qty_available

            onhand_details = {
                   'product_qty': quantity,
                   'location_id': warehouse.lot_stock_id.id,
                   'product_id': product_obj.id,
                   'product_uom_id': product_obj.uom_id.id,
                   'theoretical_qty': th_qty,
            }

            Inventory = self.env['stock.inventory']

            inventory = Inventory.create({
                    'name': _('INV: %s') % tools.ustr(product_obj.display_name),
                    'filter': 'product',
                    'product_id': product_obj.id,
                    'location_id': warehouse.view_location_id.id,
                    'line_ids': [(0, 0, onhand_details)],
                })
            inventory.action_validate()

        product_obj.write({
                    'image_medium':image_medium,
                    'barcode':barcode[0],
                    'sale_ok':sale_ok,
                    "purchase_ok":purchase_ok,
                    # 'taxes_id':[(6,0,tax_id_lst)],
                    # 'supplier_taxes_id':[(6,0,supplier_taxes_id)],
                    # 'lst_price':values.get('sale_price'),
                    'default_code':values.get('default_code'),
                    'standard_price':values.get('cost_price'),
                    'weight':values.get('weight'),
                    'volume':values.get('volume'),
            })
        return res

    @api.multi
    def create_product(self, values):
        product_tmpl_obj = self.env['product.template']
        # product_obj = self.env['product.product']
        product_categ_obj = self.env['product.category']
        product_uom_obj = self.env['uom.uom']
        taxes = self.env['account.tax']
        attribute_id = self.env['product.attribute']
        value_id = self.env['product.attribute.value']
        attibute_value = self.env['product.template.attribute.line']
        att_vals = []
        if values.get('categ_id')=='':
            raise Warning(_('CATEGORY field can not be empty'))
        else:
            categ_id = product_categ_obj.search([('name','=',values.get('categ_id'))])
        
        if values.get('type') == 'Consumable':
            categ_type ='consu'
        elif values.get('type') == 'Service':
            categ_type ='service'
        elif values.get('type') == 'Stockable Product':
            categ_type ='product'
        else:
            categ_type = 'product'

        if values.get('sale_ok')=="1":
            sale_ok = True
        elif values.get('sale_ok')=="1.0":
            sale_ok = True
        else:
            sale_ok = False

        if values.get('purchase_ok')=="1":
            purchase_ok = True
        elif values.get('purchase_ok')=="1.0":
            purchase_ok = True
        else:
            purchase_ok = False

        tax_id_lst = []
        if values.get('taxes_id'):
            if ';' in values.get('taxes_id'):
                tax_names = values.get('taxes_id').split(';')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'sale')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    tax_id_lst.append(tax.id)

            elif ',' in values.get('taxes_id'):
                tax_names = values.get('taxes_id').split(',')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'sale')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    tax_id_lst.append(tax.id)

            else:
                tax_names = values.get('taxes_id').split(',')
                tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'sale')])
                if not tax:
                    raise Warning(_('"%s" Tax not in your system') % tax_names)
                tax_id_lst.append(tax.id)



        supplier_taxes_id = []
        if values.get('supplier_taxes_id'):
            if ';' in values.get('supplier_taxes_id'):
                tax_names = values.get('supplier_taxes_id').split(';')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    supplier_taxes_id.append(tax.id)

            elif ',' in values.get('supplier_taxes_id'):
                tax_names = values.get('supplier_taxes_id').split(',')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % name)
                    supplier_taxes_id.append(tax.id)

            else:
                tax_names = values.get('supplier_taxes_id').split(',')
                tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'purchase')])
                if not tax:
                    raise Warning(_('"%s" Tax not in your system') % tax_names)
                supplier_taxes_id.append(tax.id)
        
        if values.get('image'):
            # image_name = values.get('image').encode('ascii')
            # image_path = tools.image_resize_image_big(base64.b64encode(open(image_name, 'rb').read()))
            image = urllib.request.urlopen(values.get('image')).read()

            image_base64 = base64.encodestring(image)

            image_medium = image_base64 
        else:
            image_medium = False

        if values.get('invoice_policy')=='':
            invoice_policy = 'delivery'
        else:
            invoice_policy = values.get('invoice_policy')

        
        if values.get('attribute_id')=='':
            attribute_id = ''
        else:
            attribute_id =attribute_id.search([('name','=',values.get('attribute_id'))])

        if values.get('value_id')=='':
            value_id = ''
        else:
            value_id = value_id.search([('name','=',values.get('value_id'))])
            
            att_vals.append(value_id.id)

        if values.get('uom_id')=='':
            uom_id = 1
        else:
            uom_search_id  = product_uom_obj.search([('name','=',values.get('uom_id'))])
            uom_id = uom_search_id.id
        
        if values.get('uom_po_id')=='':
            uom_po_id = 1
        else:
            uom_po_search_id  = product_uom_obj.search([('name','=',values.get('uom_po_id'))])
            uom_po_id = uom_po_search_id.id

        if values.get('barcode') == '':
            barcode = False
        else:
            barcode = values.get('barcode')
            barcode = barcode.split('.')

        if values.get('on_hand') == '':
            quantity = False
        else:
            quantity = values.get('on_hand')

        attribute = {}
        vals = {
                  'name':values.get('name'),
                  # 'default_code':values.get('default_code'),
                  'sale_ok':sale_ok,
                  'purchase_ok':purchase_ok,
                  'categ_id':categ_id[0].id,
                  'type':categ_type,
                  'barcode':barcode[0],
                  'taxes_id':[(6,0,tax_id_lst)],
                  'supplier_taxes_id':[(6,0,supplier_taxes_id)],
                  'description_sale':values.get('description_sale'),
                  'uom_id':uom_id,
                  'uom_po_id':uom_po_id,
                  'invoice_policy':invoice_policy,
                  'lst_price':values.get('sale_price'),
                  'standard_price':values.get('cost_price'),
                  'weight':values.get('weight'),
                  'volume':values.get('volume'),
                  'image_medium':image_medium
              }
        res = product_tmpl_obj.create(vals)
        attrs = []
        product_obj =self.env['product.product'].search([],order='id desc',limit=1)
        product_obj.write({
            'default_code': values.get('default_code'),
            'image_medium':image_medium
            })


        if product_obj.type=='product':
            company_user = self.env.user.company_id
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
            product = product_obj.with_context(location=warehouse.view_location_id.id)
            th_qty = product_obj.qty_available

            onhand_details = {
                   'product_qty': quantity,
                   'location_id': warehouse.lot_stock_id.id,
                   'product_id': product_obj.id,
                   'product_uom_id': product_obj.uom_id.id,
                   'theoretical_qty': th_qty,
            }

            Inventory = self.env['stock.inventory']

            inventory = Inventory.create({
                    'name': _('INV: %s') % tools.ustr(product_obj.display_name),
                    'filter': 'product',
                    'product_id': product_obj.id,
                    'location_id': warehouse.view_location_id.id,
                    'line_ids': [(0, 0, onhand_details)],
                })
            inventory.action_validate()





        attrs.append((0,0,{
            'product_tmpl_id':res.id,
            'attribute_id':attribute_id.id,
            'value_ids':[(6,0,att_vals)]
            }))
        res.write({
            'attribute_line_ids' : attrs 
            })
        return res

    @api.multi
    def import_product_variant(self):
        lst=[]
        if self.import_option == 'csv':
            keys = ['name','default_code','categ_id','type','barcode','uom_id','uom_po_id','taxes_id','supplier_taxes_id','description_sale','invoice_policy','sale_price','cost_price','attribute_id','value_id','weight','volume','image','sale_ok','purchase_ok','on_hand']

            csv_data = base64.b64decode(self.file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            file_reader = []
            res = {}
            csv_reader = csv.reader(data_file, delimiter=',')
            
            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))
            values = {}
            for i in range(len(file_reader)):
                field = map(str, file_reader[i])
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        values.update({'option':self.import_option})
                        if self.product_option == 'create':
                            product_variant = self.env['product.product'].search([('name','=',values.get('name'))])
                            if product_variant.id == False:
                                res = self.create_product(values)
                            else:
                                res = self.create_product_variant(values)
                        else:
                            product_obj = self.env['product.product']
                            product_categ_obj = self.env['product.category']
                            product_uom_obj = self.env['uom.uom']
                            categ_id = False
                            categ_type = False
                            barcode = False
                            uom_id = False
                            uom_po_id = False
                            if values.get('categ_id')=='':
                                pass
                            else:
                                categ_id = product_categ_obj.search([('name','=',values.get('categ_id'))])
                                if not categ_id:
                                    raise Warning('CATEGORY field can not be empty')

                            tax_id_lst = []
                            if values.get('taxes_id'):
                                if ';' in values.get('taxes_id'):
                                    tax_names = values.get('taxes_id').split(';')
                                    for name in tax_names:
                                        tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'sale')])
                                        if not tax:
                                            raise Warning(_('"%s" Tax not in your system') % name)
                                        tax_id_lst.append(tax.id)

                                elif ',' in values.get('taxes_id'):
                                    tax_names = values.get('taxes_id').split(',')
                                    for name in tax_names:
                                        tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'sale')])
                                        if not tax:
                                            raise Warning(_('"%s" Tax not in your system') % name)
                                        tax_id_lst.append(tax.id)

                                else:
                                    tax_names = values.get('taxes_id').split(',')
                                    tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'sale')])
                                    if not tax:
                                        raise Warning(_('"%s" Tax not in your system') % tax_names)
                                    tax_id_lst.append(tax.id)



                            supplier_taxes_id = []
                            if values.get('supplier_taxes_id'):
                                if ';' in values.get('supplier_taxes_id'):
                                    tax_names = values.get('supplier_taxes_id').split(';')
                                    for name in tax_names:
                                        tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'purchase')])
                                        if not tax:
                                            raise Warning(_('"%s" Tax not in your system') % name)
                                        supplier_taxes_id.append(tax.id)

                                elif ',' in values.get('supplier_taxes_id'):
                                    tax_names = values.get('supplier_taxes_id').split(',')
                                    for name in tax_names:
                                        tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'purchase')])
                                        if not tax:
                                            raise Warning(_('"%s" Tax not in your system') % name)
                                        supplier_taxes_id.append(tax.id)

                                else:
                                    tax_names = values.get('supplier_taxes_id').split(',')
                                    tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'purchase')])
                                    if not tax:
                                        raise Warning(_('"%s" Tax not in your system') % tax_names)
                                    supplier_taxes_id.append(tax.id)

                            if values.get('type')=='':
                                pass
                            else:
                                if values.get('type') == 'Consumable':
                                    categ_type ='consu'
                                elif values.get('type') == 'Service':
                                    categ_type ='service'
                                elif values.get('type') == 'Stockable Product':
                                    categ_type ='product'
                                else:
                                    categ_type = 'product'
                            
                            if values.get('barcode') == '':
                                pass
                            else:
                                barcode = values.get('barcode')
                                barcode = barcode.split(".")

                            if values.get('uom_id')=='':
                                pass
                            else:
                                uom_search_id  = product_uom_obj.search([('name','=',values.get('uom_id'))])
                                if not uom_search_id:
                                    raise Warning(_('UOM field can not be empty'))
                                else:
                                    uom_id = uom_search_id.id
                            
                            if values.get('uom_po_id')=='':
                                pass
                            else:
                                uom_po_search_id  = product_uom_obj.search([('name','=',values.get('uom_po_id'))])
                                if not uom_po_search_id:
                                    raise Warning(_('Purchase UOM field can not be empty'))
                                else:
                                    uom_po_id = uom_po_search_id.id

                            if values.get('on_hand') == '':
                                quantity = False
                            else:
                                quantity = values.get('on_hand')
                             
                                
                            if self.product_search == 'by_code':
                                product_ids = self.env['product.product'].search([('default_code','=', values.get('default_code'))])
                                if product_ids:
                                    if categ_id != False:
                                        product_ids.write({'categ_id': categ_id[0].id or False})
                                    if categ_type != False:
                                        product_ids.write({'type': categ_type or False})
                                    if barcode != False:
                                        product_ids.write({'barcode': barcode[0] or False})
                                    if uom_id != False:
                                        product_ids.write({'uom_id': uom_id or False})
                                    if uom_po_id != False:
                                        product_ids.write({'uom_po_id': uom_po_id})
                                    if values.get('sale_price'):
                                        product_ids.write({'lst_price': values.get('sale_price') or False})
                                    if values.get('cost_price'):
                                        product_ids.write({'standard_price': values.get('cost_price') or False})
                                    if values.get('weight'):
                                        product_ids.write({'weight': values.get('weight') or False})
                                    if values.get('volume'):
                                        product_ids.write({'volume': values.get('volume') or False})
                                    product_ids.write({
                                    'taxes_id':[(6,0,tax_id_lst)],
                                    'supplier_taxes_id':[(6,0,supplier_taxes_id)],
                                    })


                                    if product_ids.type=='product':
                                        company_user = self.env.user.company_id
                                        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
                                        product = product_ids.with_context(location=warehouse.view_location_id.id)
                                        th_qty = product_ids.qty_available

                                        onhand_details = {
                                               'product_qty': quantity,
                                               'location_id': warehouse.lot_stock_id.id,
                                               'product_id': product_ids.id,
                                               'product_uom_id': product_ids.uom_id.id,
                                               'theoretical_qty': th_qty,
                                        }

                                        Inventory = self.env['stock.inventory']

                                        inventory = Inventory.create({
                                                'name': _('INV: %s') % tools.ustr(product_ids.display_name),
                                                'filter': 'product',
                                                'product_id': product_ids.id,
                                                'location_id': warehouse.view_location_id.id,
                                                'line_ids': [(0, 0, onhand_details)],
                                            })
                                        inventory.action_validate()

                                else:
                                    raise Warning(_('"%s" Product not found.') % values.get('default_code')) 
                            else:
                                product_ids = self.env['product.product'].search([('barcode','=', values.get('barcode'))])
                                if product_ids:
                                    if categ_id != False:
                                        product_ids.write({'categ_id': categ_id[0].id or False})
                                    if categ_type != False:
                                        product_ids.write({'type': categ_type or False})
                                    if uom_id != False:
                                        product_ids.write({'uom_id': uom_id or False})
                                    if uom_po_id != False:
                                        product_ids.write({'uom_po_id': uom_po_id})
                                    if values.get('sale_price'):
                                        product_ids.write({'lst_price': values.get('sale_price') or False})
                                    if values.get('cost_price'):
                                        product_ids.write({'standard_price': values.get('cost_price') or False})
                                    if values.get('weight'):
                                        product_ids.write({'weight': values.get('weight') or False})
                                    if values.get('volume'):
                                        product_ids.write({'volume': values.get('volume') or False})
                                    product_ids.write({
                                    'taxes_id':[(6,0,tax_id_lst)],
                                    'supplier_taxes_id':[(6,0,supplier_taxes_id)],
                                    })
                                    if product_ids.type=='product':
                                        company_user = self.env.user.company_id
                                        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
                                        product = product_ids.with_context(location=warehouse.view_location_id.id)
                                        th_qty = product_ids.qty_available

                                        onhand_details = {
                                               'product_qty': quantity,
                                               'location_id': warehouse.lot_stock_id.id,
                                               'product_id': product_ids.id,
                                               'product_uom_id': product_ids.uom_id.id,
                                               'theoretical_qty': th_qty,
                                        }

                                        Inventory = self.env['stock.inventory']

                                        inventory = Inventory.create({
                                                'name': _('INV: %s') % tools.ustr(product_ids.display_name),
                                                'filter': 'product',
                                                'product_id': product_ids.id,
                                                'location_id': warehouse.view_location_id.id,
                                                'line_ids': [(0, 0, onhand_details)],
                                            })
                                        inventory.action_validate()
                                else:
                                    raise Warning(_('%s product not found.') % values.get('barcode')) 
                        
        else:
            fp = tempfile.NamedTemporaryFile(delete=False,suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            res = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    lst.append(line[0])
                    product_variant = self.env['product.template'].search([('name','=',line[0])])
                    if self.product_option == 'create':
                        if product_variant.id == False:
                            
                            values.update( {'name':line[0],
                                            'default_code': line[1],
                                            'categ_id': line[2],
                                            'type': line[3],
                                            'barcode': line[4],
                                            'uom_id': line[5],
                                            'uom_po_id': line[6],
                                            'taxes_id':line[7],
                                            'supplier_taxes_id':line[8],
                                            'description_sale':line[9],
                                            'invoice_policy':line[10],
                                            'sale_price': line[11],
                                            'cost_price': line[12],
                                            'attribute_id':line[13],
                                            'value_id':line[14],
                                            'weight': line[15],
                                            'volume': line[16],
                                            'image':line[17],
                                            'sale_ok':line[18],
                                            'purchase_ok':line[19],
                                            'on_hand': line[20]
                                            })
                            res = self.create_product(values)
                        else:
                            values.update({
                                            'name':line[0],
                                            'default_code': line[1],
                                            'barcode': line[4],
                                            'taxes_id':line[7],
                                            'supplier_taxes_id':line[8],
                                            'sale_price': line[11],
                                            'cost_price': line[12],
                                            'attribute_id':line[13],
                                            'value_id':line[14],
                                            'weight': line[15],
                                            'volume': line[16],
                                            'image':line[17],
                                            'sale_ok':line[18],
                                            'purchase_ok':line[19],
                                            'on_hand': line[20]
                                            })
                            res = self.create_product_variant(values)
                    else:
                        product_tmpl_obj = self.env['product.template']
                        product_obj = self.env['product.product']
                        product_categ_obj = self.env['product.category']
                        product_uom_obj = self.env['uom.uom']
                        categ_id = False
                        categ_type = False
                        barcode = False
                        uom_id = False
                        uom_po_id = False
                        if line[2]=='':
                            pass
                        else:
                            categ_id = product_categ_obj.search([('name','=',line[2])])
                            if not categ_id:
                                raise Warning(_('CATEGORY field can not be empty'))
                        if line[3]=='':
                            pass
                        else:
                            if line[3] == 'Consumable':
                                categ_type ='consu'
                            elif line[3] == 'Service':
                                categ_type ='service'
                            elif line[3] == 'Stockable Product':
                                categ_type ='product'
                            else:
                                categ_type = 'product'
                                
                        if line[4]=='':                             
                            pass
                        else:
                            barcode = line[4]
                            barcode = barcode.split(".")
                        
                        if line[5]=='':
                            pass
                        else:
                            uom_search_id  = product_uom_obj.search([('name','=',line[5])])
                            if not uom_search_id:
                                raise Warning(_('UOM field can not be empty'))
                            else:
                                uom_id = uom_search_id.id
                        
                        if line[6]=='':
                            pass
                        else:
                            uom_po_search_id  = product_uom_obj.search([('name','=',line[6])])
                            if not uom_po_search_id:
                                raise Warning(_('Purchase UOM field can not be empty'))
                            else:
                                uom_po_id = uom_po_search_id.id

                        tax_id_lst = []
                        if line[7]:
                            if ';' in line[7]:
                                tax_names = line[7].split(';')
                                for name in tax_names:
                                    tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'sale')])
                                    if not tax:
                                        raise Warning(_('"%s" Tax not in your system') % name)
                                    tax_id_lst.append(tax.id)

                            elif ',' in line[7]:
                                tax_names = line[7].split(',')
                                for name in tax_names:
                                    tax = self.env['account.tax'].search([('name', 'in', name), ('type_tax_use', '=', 'sale')])
                                    if not tax:
                                        raise Warning(_('"%s" Tax not in your system') % name)
                                    tax_id_lst.append(tax.id)

                            else:
                                tax_names = line[7].split(',')
                                tax = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', 'sale')])
                                if not tax:
                                    raise Warning(_('"%s" Tax not in your system') % tax_names)
                                tax_id_lst.append(tax.id)



                        supplier_taxes_id = []
                        if line[8]:
                            if ';' in line[8]:
                                tax_names = line[8].split(';')
                                for name in tax_names:
                                    tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                                    if not tax:
                                        raise Warning(_('"%s" Tax not in your system') % name)
                                    supplier_taxes_id.append(tax.id)

                            elif ',' in line[8]:
                                tax_names = line[8].split(',')
                                for name in tax_names:
                                    tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                                    if not tax:
                                        raise Warning(_('"%s" Tax not in your system') % name)
                                    supplier_taxes_id.append(tax.id)

                            else:
                                tax_names = line[8].split(',')
                                tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
                                if not tax:
                                    raise Warning(_('"%s" Tax not in your system') % tax_names)
                                supplier_taxes_id.append(tax.id)
                        if line[20] == '':
                            quantity = False
                        else:
                            quantity = line[20]
                        
                        if self.product_search == 'by_code':
                            product_ids = self.env['product.product'].search([('default_code','=', line[1])])
                            if product_ids:
                                if categ_id != False:
                                    product_ids.write({'categ_id': categ_id[0].id or False})
                                if categ_type != False:
                                    product_ids.write({'type': categ_type or False})
                                if barcode != False:
                                    product_ids.write({'barcode': barcode[0] or False})
                                if uom_id != False:
                                    product_ids.write({'uom_id': uom_id or False})
                                if uom_po_id != False:
                                    product_ids.write({'uom_po_id': uom_po_id})
                                if line[11]:
                                    product_ids.write({'lst_price': line[11] or False})
                                if line[12]:
                                    product_ids.write({'standard_price': line[12] or False})
                                if line[5]:
                                    product_ids.write({'weight': line[15] or False})
                                if line[16]:
                                    product_ids.write({'volume': line[16] or False})
                                product_ids.write({
                                    'taxes_id':[(6,0,tax_id_lst)],
                                    'supplier_taxes_id':[(6,0,supplier_taxes_id)],
                                    })
                                if product_ids.type=='product':
                                    company_user = self.env.user.company_id
                                    warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
                                    product = product_ids.with_context(location=warehouse.view_location_id.id)
                                    th_qty = product_ids.qty_available

                                    onhand_details = {
                                           'product_qty': quantity,
                                           'location_id': warehouse.lot_stock_id.id,
                                           'product_id': product_ids.id,
                                           'product_uom_id': product_ids.uom_id.id,
                                           'theoretical_qty': th_qty,
                                    }

                                    Inventory = self.env['stock.inventory']

                                    inventory = Inventory.create({
                                            'name': _('INV: %s') % tools.ustr(product_ids.display_name),
                                            'filter': 'product',
                                            'product_id': product_ids.id,
                                            'location_id': warehouse.view_location_id.id,
                                            'line_ids': [(0, 0, onhand_details)],
                                        })
                                    inventory.action_validate()
                            else:
                                raise Warning(_('"%s" Product not found.') % line[1]) 
                        else:
                            product_ids = self.env['product.product'].search([('barcode','=', line[4])])
                            if product_ids:
                                if categ_id != False:
                                    product_ids.write({'categ_id': categ_id[0].id or False})
                                if categ_type != False:
                                    product_ids.write({'type': categ_type or False})
                                if uom_id != False:
                                    product_ids.write({'uom_id': uom_id or False})
                                if uom_po_id != False:
                                    product_ids.write({'uom_po_id': uom_po_id})
                                if line[7]:
                                    product_ids.write({'lst_price': line[7] or False})
                                if line[8]:
                                    product_ids.write({'standard_price': line[8] or False})
                                if line[9]:
                                    product_ids.write({'weight': line[9] or False})
                                if line[10]:
                                    product_ids.write({'volume': line[10] or False})
                                product_ids.write({
                                    'taxes_id':[(6,0,tax_id_lst)],
                                    'supplier_taxes_id':[(6,0,supplier_taxes_id)],
                                    })
                                if product_ids.type=='product':
                                    company_user = self.env.user.company_id
                                    warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
                                    product = product_ids.with_context(location=warehouse.view_location_id.id)
                                    th_qty = product_ids.qty_available

                                    onhand_details = {
                                           'product_qty': quantity,
                                           'location_id': warehouse.lot_stock_id.id,
                                           'product_id': product_ids.id,
                                           'product_uom_id': product_ids.uom_id.id,
                                           'theoretical_qty': th_qty,
                                    }

                                    Inventory = self.env['stock.inventory']

                                    inventory = Inventory.create({
                                            'name': _('INV: %s') % tools.ustr(product_ids.display_name),
                                            'filter': 'product',
                                            'product_id': product_ids.id,
                                            'location_id': warehouse.view_location_id.id,
                                            'line_ids': [(0, 0, onhand_details)],
                                        })
                                    inventory.action_validate()
                            else:
                                raise Warning(_('%s product not found.') % line[4])  
        return res
