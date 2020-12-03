# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import tempfile
import binascii
import logging
from odoo.exceptions import Warning
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')

class gen_suppinfo(models.TransientModel):
    _inherit = "gen.suppinfo"

    
    @api.multi
    def import_fle(self):
        fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file))
        fp.seek(0)
        values = {}
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
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

    @api.multi
    def _create_product_suppinfo(self,val):
        name = self._find_vendor(val.get('vendor'))
        product_tmpl_id = self._find_product_template(val.get('product'),val.get('create_link_option'))
        # res = self.env['product.supplierinfo'].create({
        #                                                'name':name,
        #                                                'product_tmpl_id':product_tmpl_id,
        #                                                'product_name': self.env['product.template'].browse(product_tmpl_id).name,
        #                                                'min_qty': int(float(val.get('quantity'))),
        #                                                'price': val.get('price'),
        #                                                'delay': int(float(val.get('delivery_time')))
        #                                                })
        currency_id = self.env.user.company_id.currency_id.id
        self.env.cr.execute("""INSERT INTO product_supplierinfo (name,product_tmpl_id,product_name,min_qty,price,delay,currency_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (name, product_tmpl_id,self.env['product.template'].browse(product_tmpl_id).name,int(float(val.get('quantity'))),val.get('price'),int(float(val.get('delivery_time'))),currency_id ))
        res = self.env.cr.execute("select max(id) from product_supplierinfo;")
        res = self.env.cr.fetchall()
        res = self.env['product.supplierinfo'].browse(res)
    
        return res


    @api.multi
    def _find_vendor(self,name):
        partner_search = self.env['res.partner'].search([('name','=',name),('supplier','=',True)])
        if not partner_search:
            raise Warning (_("%s Vendor Not Found") % name)
        return partner_search.id

    @api.multi
    def _find_product_template(self,product,create_opt):
        product_tmpl_search = self.env['product.template'].search([('name','=',product)])
        if not product_tmpl_search:
            if create_opt == 'create':
                product_id = self.env['product.template'].create({'name':product})
                product_tmpl_search = product_id
            else:
                raise Warning (_(" You have selected Link product template with existing product but %s Product template does not exist") % product)
        return product_tmpl_search.id

