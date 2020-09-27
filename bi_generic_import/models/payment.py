# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime
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

class gen_salereceipt(models.TransientModel):
    _name = "gen.salepayment"

    file = fields.Binary('File')
    payment_option = fields.Selection([('customer', 'Customer Payment'),('supplier', 'Supplier Pament')],string='Payment',default='customer')

    
    def import_fle(self):
        try:
            fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
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
                if line[3] != '':
                    a1 = int(float(line[3]))
                    a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                    date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                else:
                    raise Warning(_("Please assign a Date"))

                values.update( {'partner_id':line[0],
                                'amount': line[1],
                                'journal_id': line[2],
                                 'payment_date': date_string,
                                'communication': line[4],
                                'payment_option':self.payment_option
                                })
                res = self._create_customer_payment(values)
                        
        return res

    
    def _create_customer_payment(self,val):
        name = self._find_customer(val.get('partner_id'))
        payment_journal =self._find_journal_id(val.get('journal_id'))
        pay_date = self.find_date(val.get('payment_date'))
        pay_id =self.find_payment_method()
        
        if val['payment_option'] == 'customer' :
        	partner_type = 'customer'
        	payment_type = 'inbound'
        else:
        	partner_type = 'supplier'
        	payment_type = 'outbound'
        
        res = self.env['account.payment'].create({
                                                        'partner_id':name,
                                                         'amount': val.get('amount'),
                                                         'journal_id':payment_journal,
                                                         'partner_type':partner_type,
                                                         'communication':val.get('communication'),
                                                         'payment_date':pay_date,
                                                         'payment_method_id': pay_id,
                                                         'payment_type' : payment_type
                                                       })
        return res
    
   
    def _find_customer(self,name):
        partner_search = self.env['res.partner'].search([('name','=',name)])
        if not partner_search:
            raise Warning (_("%s Customer Not Found") % name)
        return partner_search.id

    
    def _find_journal_id(self,journal):
        journal_search =self.env['account.journal'].search([('name','=',journal)])
        if not journal_search:
            raise Warning(_("%s Journal Not Found") % journal)
        return journal_search.id

    
    def find_date(self,date):
        DATETIME_FORMAT = "%Y-%m-%d"
        p_date = datetime.strptime(date,DATETIME_FORMAT)
        return p_date
    
    
    def find_payment_method(self,  payment_type_id=None):
        payment_option_selection = self.env['account.payment.method'].search([('name','=','Manual'),('payment_type','=','inbound')])
        if not payment_option_selection:
            if payment_type_id == 'supplier':
                payment_type_id = self.env['account.payment'].search([('name','=','Manual'),('payment_type','=','outbound')])
                payment_option_selection = payment_type_id
            else:
                pass

        return payment_option_selection.id

