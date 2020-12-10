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


TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}

MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': -1,
    'in_invoice': -1,
    'out_refund': 1,
}

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}

class gen_inv_inherit(models.TransientModel):
    _inherit = "gen.invoice"

    stage = fields.Selection(
        [('draft', 'Import Draft Invoice'), ('confirm', 'Validate Invoice Automatically With Import'),('payment', 'Import Invoice with Payment')],
        string="Invoice Stage Option", default='draft')
    partial_payment = fields.Selection(
        [('keep','Keep Open'),('writeoff','Write-Off')],
        string="Partial Payment",default='keep')
    writeoff_account = fields.Many2one('account.account',string="Write-Off Account")


    def create_payment(self,payment):
        for res in payment: 
            if res.state in ['draft']:
                res.action_post()

            journal = self.env['account.journal'].search([('name','like',payment[res][0])],limit=1)
            if not journal:
                raise Warning(_('Journal %s does not exist.' %payment[res][0]))
                
            sign = res.type in ['in_refund', 'out_refund'] and -1 or 1
            date_payment = payment[res][2]

            amount = float(payment[res][1]) * MAP_INVOICE_TYPE_PAYMENT_SIGN[res.type] * sign
            if MAP_INVOICE_TYPE_PARTNER_TYPE[res.type] == 'customer':
                payment_method = journal.inbound_payment_method_ids[0]
            elif MAP_INVOICE_TYPE_PARTNER_TYPE[res.type] == 'supplier':
                payment_method = journal.outbound_payment_method_ids[0]


            if res.amount_total != amount:
                if self.partial_payment == 'keep':
                    pay_rec = self.env['account.payment'].create({
                        'amount': abs(float(amount)),
                        'currency_id': res.currency_id.id,
                        'payment_type': amount > 0 and 'inbound' or 'outbound',
                        'partner_id': res.commercial_partner_id.id,
                        'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[res.type],
                        'communication': " ".join(i.invoice_payment_ref or i.ref or i.name for i in res),
                        'invoice_ids': [(6, 0, res.ids)],
                        'journal_id':journal.id,
                        'payment_difference_handling': 'open',
                        'payment_date': date_payment,
                        'payment_method_id':payment_method.id,
                        'is_import' : True
                        })
                elif self.partial_payment == 'writeoff':
                    pay_rec = self.env['account.payment'].create({
                        'amount': abs(amount),
                        'currency_id': res.currency_id.id,
                        'payment_type': amount > 0 and 'inbound' or 'outbound',
                        'partner_id': res.commercial_partner_id.id,
                        'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[res.type],
                        'communication': " ".join(i.invoice_payment_ref or i.ref or i.name for i in res),
                        'invoice_ids': [(6, 0, res.ids)],
                        'journal_id':journal.id,
                        'payment_difference_handling': 'reconcile',
                        'writeoff_label': 'Write-Off',
                        'writeoff_account_id': self.writeoff_account.id,
                        'payment_date': date_payment,
                        'payment_method_id':payment_method.id,
                        'is_import' : True
                        })
            else:
                 pay_rec = self.env['account.payment'].create({
                        'amount': abs(amount),
                        'currency_id': res.currency_id.id,
                        'payment_type': amount > 0 and 'inbound' or 'outbound',
                        'partner_id': res.commercial_partner_id.id,
                        'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[res.type],
                        'communication': " ".join(i.invoice_payment_ref or i.ref or i.name for i in res),
                        'invoice_ids': [(6, 0, res.ids)],
                        'journal_id':journal.id,
                        'payment_date': date_payment,
                        'payment_method_id':payment_method.id,
                        'is_import' : True
                        })
            main_list = values.keys()
            # count = 0
            for i in main_list:
                model_id = self.env['ir.model'].search([('model','=','account.payment')])           
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
                                            pay_rec.update({
                                                technical_fields_name: fetch_m2o.id
                                                })
                                        else:
                                            raise Warning(_('"%s" This custom field value "%s" not available in system') % (many2x_fields.name , values.get(i)))
                                if many2x_fields.ttype =="many2many":
                                    m2m_value_lst = []
                                    if values.get(i):
                                        if ';' in values.get(i):
                                            m2m_names = values.get(i).split(';')
                                            for name in m2m_names:
                                                m2m_id = self.env[many2x_fields.relation].search([('name', '=', name)])
                                                if not m2m_id:
                                                    raise Warning(_('"%s" This custom field value "%s" not available in system') % (many2x_fields.name , name))
                                                m2m_value_lst.append(m2m_id.id)

                                        elif ',' in values.get(i):
                                            m2m_names = values.get(i).split(',')
                                            for name in m2m_names:
                                                m2m_id = self.env[many2x_fields.relation].search([('name', '=', name)])
                                                if not m2m_id:
                                                    raise Warning(_('"%s" This custom field value "%s" not available in system') % (many2x_fields.name , name))
                                                m2m_value_lst.append(m2m_id.id)

                                        else:
                                            m2m_names = values.get(i).split(',')
                                            m2m_id = self.env[many2x_fields.relation].search([('name', 'in', m2m_names)])
                                            if not m2m_id:
                                                raise Warning(_('"%s" This custom field value "%s" not available in system') % (many2x_fields.name , m2m_names))
                                            m2m_value_lst.append(m2m_id.id)
                                    pay_rec.update({
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
                                pay_rec.update({
                                    normal_details : values.get(i)
                                    })
                            elif normal_fields.ttype == 'char':
                                pay_rec.update({
                                    normal_details : values.get(i)
                                    })                              
                            elif normal_fields.ttype == 'float':
                                if values.get(i) == '':
                                    float_value = 0.0
                                else:
                                    float_value = float(values.get(i)) 
                                pay_rec.update({
                                    normal_details : float_value
                                    })                              
                            elif normal_fields.ttype == 'integer':
                                if values.get(i) == '':
                                    int_value = 0
                                else:
                                    int_value = int(values.get(i)) 
                                pay_rec.update({
                                    normal_details : int_value
                                    })                            
                            elif normal_fields.ttype == 'selection':
                                pay_rec.update({
                                    normal_details : values.get(i)
                                    })                              
                            elif normal_fields.ttype == 'text':
                                pay_rec.update({
                                    normal_details : values.get(i)
                                    })                              
                        else:
                            raise Warning(_('"%s" This custom field is not available in system') % normal_details)
            pay_rec.post()


    def import_csv(self):
        """Load Inventory data from the CSV file."""
        if self.stage == 'payment':

            if self.import_option == 'csv':

                keys = ['invoice', 'customer', 'currency', 'product','account', 'quantity', 'uom', 'description', 'price','discount','salesperson','tax','date','journal','amount','paymentdate']
                
                try:
                    csv_data = base64.b64decode(self.file)
                    data_file = io.StringIO(csv_data.decode("utf-8"))
                    data_file.seek(0)
                    file_reader = []
                    csv_reader = csv.reader(data_file, delimiter=',')
                    file_reader.extend(csv_reader)
                except Exception:
                    raise exceptions.Warning(_("Please select an CSV/XLS file or You have selected invalid file"))

                values = {}
                invoice_ids=[]
                payment = {}
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
                            values.update({'type':self.type,'option':self.import_option,'seq_opt':self.sequence_opt})
                            res = self.make_invoice(values)
                            res._recompute_dynamic_lines()
                            res._compute_amount()
                            invoice_ids.append(res)
                            if self.stage == 'payment':
                                if values.get('paymentdate') == '':
                                    raise Warning(_('Please assign a payment date'))

                                if values.get('journal') and values.get('amount'):
                                    if res in payment:
                                        if payment[res][0] != values.get('journal'):
                                            raise Warning(_('Please Use same Journal for Invoice %s' %values.get('invoice')))   
                                        else:
                                            payment.update({res:[values.get('journal'),float(values.get('amount'))+float(payment[res][1]),values.get('paymentdate') ]})
                                    else:
                                        payment.update({res:[values.get('journal'),values.get('amount'),values.get('paymentdate')]})
                                else:
                                    raise Warning(_('Please Specify Payment Journal and Amount for Invoice %s' %values.get('invoice')))

                if self.stage == 'confirm':
                    for res in invoice_ids: 
                        if res.state in ['draft']:
                            res.action_post()

                if self.stage == 'payment':
                    self.create_payment(payment)

            else:
                try:
                    fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
                    fp.write(binascii.a2b_base64(self.file))
                    fp.seek(0)
                    values = {}
                    invoice_ids=[]
                    payment = {}
                    workbook = xlrd.open_workbook(fp.name)
                    sheet = workbook.sheet_by_index(0)
                except Exception:
                    raise exceptions.Warning(_("Please select an CSV/XLS file or You have selected invalid file"))
                    
                for row_no in range(sheet.nrows):
                    val = {}
                    if row_no <= 0:
                        fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                    else:
                        line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))


                        if line[12]:
                            if line[12] == '':
                                raise Warning(_('Please assign a date'))
                            else:
                                a1 = int(float(line[12]))
                                a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                                date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                            values.update( {'invoice':line[0],
                                            'customer': line[1],
                                            'currency': line[2],
                                            'product': line[3].split('.')[0],
                                            'account': line[4],
                                            'quantity': line[5],
                                            'uom': line[6],
                                            'description': line[7],
                                            'price': line[8],
                                            'discount':line[9],
                                            'salesperson': line[10],
                                            'tax': line[11],
                                            'date': date_string,
                                            'seq_opt':self.sequence_opt,
                                            })
                            count = 0
                            for l_fields in line_fields:
                                if(count > 12):
                                    values.update({l_fields : line[count]})                        
                                count+=1 

                        res = self.make_invoice(values)
                        res._recompute_dynamic_lines()
                        res._compute_amount()
                        invoice_ids.append(res)

                        if self.stage == 'payment':
                            if line[15] == '':
                                raise Warning(_('Please assign a payment date'))
                            else:
                                a2 = int(float(line[15]))
                                a2_as_datetime = datetime(*xlrd.xldate_as_tuple(a2, workbook.datemode))
                                date_string2 = a2_as_datetime.date().strftime('%Y-%m-%d')

                                if line[13] and line[14]:
                                    if res in payment:
                                        if payment[res][0] != line[13]:
                                            raise Warning(_('Please Use same Journal for Invoice %s' %line[0]))   
                                        else:
                                            payment.update({res:[line[13],float(line[14])+float(payment[res][1]),date_string2 ]})
                                    else:
                                        payment.update({res:[line[13],line[14],date_string2 ]})
                                else:
                                    raise Warning(_('Please Specify Payment Journal and Amount for Invoice %s' %line[0]))

                if self.stage == 'confirm':
                    for res in invoice_ids: 
                        if res.state in ['draft']:
                            res.action_post()

                if self.stage == 'payment':
                    self.create_payment(payment)


                return res
        else:
            super(gen_inv_inherit,self).import_csv()
