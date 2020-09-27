# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import tempfile
import binascii
import logging
from odoo.exceptions import Warning
from odoo import models, fields, api, _,exceptions
_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')

class gen_suppinfo(models.TransientModel):
    _name = "gen.suppinfo"

    file = fields.Binary('File')
    create_link_option = fields.Selection([('create', 'Create product template if not available'),('link', 'Link with available product template')],string='Product Option',default='link')


    
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
                fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                values.update( {'vendor':line[0],
                                'product': line[1],
                                'delivery_time': line[2],
                                'quantity': line[3],
                                'price': line[4],
                                'create_link_option':self.create_link_option,
                                })
                res = self._create_product_suppinfo(values)
        return res

    
    def _create_product_suppinfo(self,val):
        name = self._find_vendor(val.get('vendor'))
        product_tmpl_id = self._find_product_template(val.get('product'),val.get('create_link_option'))
        res = self.env['product.supplierinfo'].create({
                                                       'name':name,
                                                       'product_tmpl_id':product_tmpl_id,
                                                       'product_name': self.env['product.template'].browse(product_tmpl_id).name,
                                                       'min_qty': int(float(val.get('quantity'))),
                                                       'price': val.get('price'),
                                                       'delay': int(float(val.get('delivery_time')))
                                                       })
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

