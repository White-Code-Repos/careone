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


class gen_mrp(models.TransientModel):
    _name = "gen.mrp"

    file = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')
    bom_type = fields.Selection([('normal', 'Normal'),('phantom', 'Phantom')],default='normal') 
    import_prod_option = fields.Selection([('barcode', 'Barcode'),('code', 'Code'),('name', 'Name')],string='Import Product By ',default='name')    
    import_material_prod_option = fields.Selection([('barcode', 'Barcode'),('code', 'Code'),('name', 'Name')],string='Import Material Product By ',default='name') 
    
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
                   self.make_bom_line(values, bom_search[0])
                return bom_search
            else:
                raise Warning(_('Found Diffrent value same BOM %s') % values.get('ref'))
        else:
            bom_id = bom_obj.create({
                'product_tmpl_id' : product_tmpl_id.id,
                'code':values.get('ref'),
                'type':self.bom_type,
                'product_qty': values.get('qty')
            })
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
            
        res = mrp_line_obj.create({
            'product_id' : product_id.id,
            'product_qty' : values.get('qty_l'),
            'bom_id' : bom_id.id,
            'product_uom_id':product_uom.id,
            })
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
                    fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
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
                    res = self.make_bom(values)
        return res

