# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
import tempfile
import binascii
import xlrd
import io
import re
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning ,ValidationError
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

class gen_inv(models.TransientModel):
    _inherit = "gen.invoice"
    _description = "Generic Invoice"

    
   
    
    def make_invoice(self, values):
        invoice_obj = self.env['account.move']
        if self.sequence_opt == "custom":
            if self.type == "in":
                invoice_search = invoice_obj.search([
                    ('name', '=', values.get('invoice')),
                    ('type', '=', 'out_invoice')
                ])
            elif self.type == 'out':
                invoice_search = invoice_obj.search([
                    ('name', '=', values.get('invoice')),
                    ('type', '=', 'in_invoice')
                ])
            elif self.type == 'cus_credit_note':
                invoice_search = invoice_obj.search([
                    ('name', '=', values.get('invoice')),
                    ('type', '=', 'out_refund')
                ])
            else:
                invoice_search = invoice_obj.search([
                    ('name', '=', values.get('invoice')),
                    ('type', '=', 'in_refund')
                ])
        else:
            if self.type == "in":
                invoice_search = invoice_obj.search([
                    ('invoice_name', '=', values.get('invoice')),
                    ('type', '=', 'out_invoice')
                ])
            elif self.type == 'out':
                invoice_search = invoice_obj.search([
                    ('invoice_name', '=', values.get('invoice')),
                    ('type', '=', 'in_invoice')
                ])
            elif self.type == 'cus_credit_note':
                invoice_search = invoice_obj.search([
                    ('invoice_name', '=', values.get('invoice')),
                    ('type', '=', 'out_refund')
                ])
            else:
                invoice_search = invoice_obj.search([
                    ('invoice_name', '=', values.get('invoice')),
                    ('type', '=', 'in_refund')
                ])
            
        if invoice_search:
            if invoice_search.partner_id.name == values.get('customer'):
                if  invoice_search.currency_id.name == values.get('currency'):
                    if  invoice_search.invoice_user_id.name == values.get('salesperson'):
                        self.make_invoice_line(values, invoice_search)
                        return invoice_search
                    else:
                        raise ValidationError(_('User(Salesperson) is different for "%s" .\n Please define same.') % (values.get('invoice')))
                else:
                    raise ValidationError(_('Currency is different for "%s" .\n Please define same.') % (values.get('invoice')))
            else:
                raise ValidationError(_('Customer name is different for "%s" .\n Please define same.') % (values.get('invoice')))
        else:
            partner_id = self.find_partner(values.get('customer'))
            currency_id = self.find_currency(values.get('currency'))
            salesperson_id = self.find_sales_person(values.get('salesperson'))
            inv_date = self.find_invoice_date(values.get('date'))

            if self.type == "in":
                type_inv = "out_invoice"
                if partner_id.property_account_receivable_id:
                    account_id = partner_id.property_account_receivable_id
                else:
                    account_search = self.env['ir.property'].search([('name', '=', 'property_account_receivable_id')],limit=1)
                    account_id = account_search.value_reference
                    if not account_id:
                        raise UserError(_('Please define Customer account.'))
                    account_id = account_id.split(",")[1]
                    account_id = self.env['account.account'].browse(account_id)
                    
            elif self.type == "out":
                type_inv = "in_invoice"
                if partner_id.property_account_payable_id:
                    account_id = partner_id.property_account_payable_id
                else:
                    account_search = self.env['ir.property'].search([('name', '=', 'property_account_payable_id')],limit=1)
                    account_id = account_search.value_reference
                    if not account_id:
                        raise UserError(_('Please define Vendor account.'))
                    account_id = account_id.split(",")[1]
                    account_id = self.env['account.account'].browse(account_id)
               
            elif self.type == "cus_credit_note":
                type_inv = "out_refund"
                if partner_id.property_account_receivable_id:
                    account_id = partner_id.property_account_receivable_id
                else:
                    account_search = self.env['ir.property'].search([('name', '=', 'property_account_receivable_id')],limit=1)
                    account_id = account_search.value_reference
                    if not account_id:
                        raise UserError(_('Please define Customer account.'))
                    account_id = account_id.split(",")[1]
                    account_id = self.env['account.account'].browse(account_id)
            else:
                type_inv = "in_refund"
                if partner_id.property_account_payable_id:
                    account_id = partner_id.property_account_payable_id
                else:
                    account_search = self.env['ir.property'].search([('name', '=', 'property_account_payable_id')],limit=1)
                    account_id = account_search.value_reference
                    if not account_id:
                        raise UserError(_('Please define Vendor account.'))
                    account_id = account_id.split(",")[1]
                    account_id = self.env['account.account'].browse(account_id)
                
                
            if type_inv == "in_invoice":
                journal_type = 'purchase'                   
            elif type_inv == "out_invoice":
                journal_type = 'sale'
            elif type_inv == "out_refund":
                journal_type = 'sale'
            else:
                journal_type = 'purchase'
                
            if self._context.get('default_journal_id', False):
                journal = self.env['account.journal'].browse(self._context.get('default_journal_id'))
            inv_type = journal_type
            inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
            company_id = self._context.get('company_id', self.env.user.company_id.id)
            domain = [
                ('type', 'in', [journal_type]),
                ('company_id', '=', company_id),
            ]
            journal = self.env['account.journal'].search(domain, limit=1)
            
            if values.get('seq_opt') == 'system':
                #journal = self.env['account.invoice']._default_journal()
                if self._context.get('default_journal_id', False):
                    journal = self.env['account.journal'].browse(self._context.get('default_journal_id'))
                inv_type = journal_type
                inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
                company_id = self._context.get('company_id', self.env.user.company_id.id)
                domain = [
                    ('type', 'in', [journal_type]),
                    ('company_id', '=', company_id),
                ]
                journal = self.env['account.journal'].search(domain, limit=1)
                if journal.sequence_id:
                    # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                    sequence = journal.sequence_id
                    name = sequence.with_context(ir_sequence_date=datetime.today().date().strftime("%Y-%m-%d")).next_by_id()
                else:
                    raise UserError(_('Please define a sequence on the journal.'))
            else:
                name = values.get('invoice')
                
            # inv_id = invoice_obj.create({
            #     'partner_id' : partner_id.id,
            #     'currency_id' : currency_id.id,
            #     'user_id':salesperson_id.id,
            #     'name':name,
            #     'is_import' : True,
            #     'custom_seq': True if values.get('seq_opt') == 'custom' else False,
            #     'system_seq': True if values.get('seq_opt') == 'system' else False,
            #     'type' : type_inv,
            #     'invoice_date':inv_date,
            #     'journal_id' : journal.id,
            #     'name' : values.get('invoice'),

            # })
            if 'l10n_in_export_type' in self.env['account.move']._fields:
                inv_id = self.env.cr.execute("""INSERT INTO account_move (partner_id,currency_id,name,is_import,custom_seq,system_seq,type,invoice_date,date,journal_id,invoice_name,company_id,state,l10n_in_export_type,invoice_user_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""" , (partner_id.id,currency_id.id,name,True,
                True if values.get('seq_opt') == 'custom' else False,True if values.get('seq_opt') == 'system' else False,
                type_inv,inv_date,inv_date,journal.id,values.get('invoice'),company_id,'draft','regular',salesperson_id.id))
            elif 'extract_state' in self.env['account.move']._fields:
                inv_id = self.env.cr.execute("""INSERT INTO account_move (partner_id,currency_id,name,is_import,custom_seq,system_seq,type,invoice_date,date,journal_id,invoice_name,company_id,state,invoice_user_id,extract_state) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""" , (partner_id.id,currency_id.id,name,True,
                True if values.get('seq_opt') == 'custom' else False,True if values.get('seq_opt') == 'system' else False,
                type_inv,inv_date,inv_date,journal.id,values.get('invoice'),company_id,'draft',salesperson_id.id,'no_extract_requested'))
            else:
                inv_id = self.env.cr.execute("""INSERT INTO account_move (partner_id,currency_id,name,is_import,custom_seq,system_seq,type,invoice_date,date,journal_id,invoice_name,company_id,state,invoice_user_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""" , (partner_id.id,currency_id.id,name,True,
                True if values.get('seq_opt') == 'custom' else False,True if values.get('seq_opt') == 'system' else False,
                type_inv,inv_date,inv_date,journal.id,values.get('invoice'),company_id,'draft',salesperson_id.id))
            

            inv_id = self.env['account.move'].search([],order='id desc', limit=1)
            if values.get('invoice_origin'):
                self.env.cr.execute("update account_move set invoice_origin=%s where id=%s", [values.get('invoice_origin'),inv_id.id])

            main_list = values.keys()
            # count = 0
            for i in main_list:
                model_id = self.env['ir.model'].search([('model','=','account.move')])           
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
                                            inv_id.update({
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
                                    inv_id.update({
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
                                inv_id.update({
                                    normal_details : values.get(i)
                                    })
                            elif normal_fields.ttype == 'char':
                                inv_id.update({
                                    normal_details : values.get(i)
                                    })                              
                            elif normal_fields.ttype == 'float':
                                if values.get(i) == '':
                                    float_value = 0.0
                                else:
                                    float_value = float(values.get(i)) 
                                inv_id.update({
                                    normal_details : float_value
                                    })                              
                            elif normal_fields.ttype == 'integer':
                                if values.get(i) == '':
                                    int_value = 0
                                else:
                                    int_value = int(values.get(i)) 
                                inv_id.update({
                                    normal_details : int_value
                                    })                            
                            elif normal_fields.ttype == 'selection':
                                inv_id.update({
                                    normal_details : values.get(i)
                                    })                              
                            elif normal_fields.ttype == 'text':
                                inv_id.update({
                                    normal_details : values.get(i)
                                    })                              
                        else:
                            raise Warning(_('"%s" This custom field is not available in system') % normal_details)            
            self.make_invoice_line(values, inv_id)
            return inv_id



    
    def make_invoice_line(self, values, inv_id):
        product_obj = self.env['product.product']
        invoice_line_obj = self.env['account.move.line']

        if self.import_prod_option == 'barcode':
          product_search = product_obj.search([('barcode',  '=',values['product'])])
        elif self.import_prod_option == 'code':
            product_search = product_obj.search([('default_code', '=',values['product'])])
        else:
            product_search = product_obj.search([('name', '=',values['product'])])

        product_uom = self.env['uom.uom'].search([('name', '=', values.get('uom'))])
        if not product_uom:
            raise Warning(_(' "%s" Product UOM category is not available.') % values.get('uom'))

        if product_search:
            product_id = product_search
        else:
            if self.import_prod_option == 'name':
                # product_id = product_obj.create({
                #                                     'name':values.get('product'),
                #                                     'lst_price':float(values.get('price')),
                #                                     'uom_id':product_uom.id,
                #                                  })
                temp = self.env.cr.execute("""INSERT INTO product_template (name,uom_id,type,categ_id,uom_po_id,tracking,purchase_line_warn,sale_line_warn,list_price,active) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""" , (values.get('product'),product_uom.id,'product',1,product_uom.id
                    ,'none','no-message','no-message',float(values.get('price')),True))
                tmpl_id = self.env['product.template'].search([('name','=',values.get('product'))],order='id desc', limit=1)
                product_id = self.env.cr.execute("""INSERT INTO product_product (product_tmpl_id, default_code,active)
                    VALUES (%s,%s,%s)""" ,
                    (tmpl_id.id,' ',True))
            else:
                raise Warning(_('%s product is not found" .\n If you want to create product then first select Import Product By Name option .') % values.get('product'))

        tax_ids = []
        if inv_id.type == 'out_invoice':
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
                    tax= self.env['account.tax'].search([('name', '=', tax_names),('type_tax_use','=','sale')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % tax_names)
                    tax_ids.append(tax.id)
        elif inv_id.type == 'in_invoice':
            if values.get('tax'):
                if ';' in values.get('tax'):
                    tax_names = values.get('tax').split(';')
                    for name in tax_names:
                        tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                        if not tax:
                            raise Warning(_('"%s" Tax not in your system') % name)
                        tax_ids.append(tax.id)

                elif ',' in values.get('tax'):
                    tax_names = values.get('tax').split(',')
                    for name in tax_names:
                        tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                        if not tax:
                            raise Warning(_('"%s" Tax not in your system') % name)
                        tax_ids.append(tax.id)
                else:
                    tax_names = values.get('tax').split(',')
                    tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % tax_names)
                    tax_ids.append(tax.id)
        elif inv_id.type == 'out_refund':
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
                    tax= self.env['account.tax'].search([('name', '=', tax_names),('type_tax_use','=','sale')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % tax_names)
                    tax_ids.append(tax.id)
        else:
            if values.get('tax'):
                if ';' in values.get('tax'):
                    tax_names = values.get('tax').split(';')
                    for name in tax_names:
                        tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                        if not tax:
                            raise Warning(_('"%s" Tax not in your system') % name)
                        tax_ids.append(tax.id)

                elif ',' in values.get('tax'):
                    tax_names = values.get('tax').split(',')
                    for name in tax_names:
                        tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                        if not tax:
                            raise Warning(_('"%s" Tax not in your system') % name)
                        tax_ids.append(tax.id)
                else:
                    tax_names = values.get('tax').split(',')
                    tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise Warning(_('"%s" Tax not in your system') % tax_names)
                    tax_ids.append(tax.id)
        tag_ids = []
        if values.get('Analytic_Tags_ids'):
            if ';' in  values.get('Analytic_Tags_ids'):
                tag_names = values.get('Analytic_Tags_ids').split(';')
                for name in tag_names:
                    tag= self.env['account.analytic.tag'].search([('name', '=', name)])
                    if not tag:
                        raise Warning(_('"%s" Analytic Tags not in your system') % name)
                    tag_ids.append(tag.id)

            elif ',' in  values.get('Analytic_Tags_ids'):
                tag_names = values.get('Analytic_Tags_ids').split(',')
                for name in tag_names:
                    tag= self.env['account.analytic.tag'].search([('name', '=', name)])
                    if not tag:
                        raise Warning(_('"%s" Analytic Tags not in your system') % name)
                    tag_ids.append(tag.id)
            else:
                tag_names = values.get('Analytic_Tags_ids').split(',')
                tag= self.env['account.analytic.tag'].search([('name', '=', tag_names)])
                if not tag:
                    raise Warning(_('"%s" Analytic Tags not in your system') % tag_names)
                tag_ids.append(tag.id)

        if self.account_opt == 'default':
            if inv_id.type == 'out_invoice':
                if product_id:
                    if product_id.property_account_income_id:
                        account = product_id.property_account_income_id
                    elif product_id.categ_id.property_account_income_categ_id:
                        account = product_id.categ_id.property_account_income_categ_id
                    else:
                        account_search = self.env['ir.property'].search([('name', '=', 'property_account_income_categ_id')],limit=1)
                        account = account_search.value_reference
                        if account:
                            account = account.split(",")[1]
                            account = self.env['account.account'].browse(account)
                            account = account.id
                        else:
                            account = False
            if inv_id.type == 'in_invoice':
                if product_id:
                    if product_id.property_account_expense_id:
                        account = product_id.property_account_expense_id
                    elif product_id.categ_id.property_account_expense_categ_id:
                        account = product_id.categ_id.property_account_expense_categ_id
                    else:
                        account_search = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id')],limit=1)
                        account = account_search.value_reference
                        if account:
                            account = account.split(",")[1]
                            account = self.env['account.account'].browse(account)
                            account = account.id
                        else:
                            account = False

            if inv_id.type == 'out_refund':
                if product_id:
                    if product_id.property_account_income_id:
                        account = product_id.property_account_income_id
                    elif product_id.categ_id.property_account_income_categ_id:
                        account = product_id.categ_id.property_account_income_categ_id
                    else:
                        account_search = self.env['ir.property'].search([('name', '=', 'property_account_income_categ_id')],limit=1)
                        account = account_search.value_reference
                        if account:
                            account = account.split(",")[1]
                            account = self.env['account.account'].browse(account)
                            account = account.id
                        else:
                            account = False
            if inv_id.type == 'in_refund':
                if product_id:
                    if product_id.property_account_expense_id:
                        account = product_id.property_account_expense_id
                    elif product_id.categ_id.property_account_expense_categ_id:
                        account = product_id.categ_id.property_account_expense_categ_id
                    else:
                        account_search = self.env['ir.property'].search([('name', '=', 'property_account_expense_categ_id')],limit=1)
                        account = account_search.value_reference
                        if account:
                            account = account.split(",")[1]
                            account = self.env['account.account'].browse(account)
                            account = account.id
                        else:
                            account = False
                
        else:
            if values.get('account') == '':
                raise Warning(_(' You can not left blank account field if you select Excel/CSV Account Option'))
            else:
                if self.import_option == 'csv':
                    account_id = self.env['account.account'].search([('code','=',values.get('account'))])
                else:
                    acc = values.get('account').split('.')
                    account_id = self.env['account.account'].search([('code','=',acc[0])])
                if account_id:
                    account = account_id
                else:
                    raise Warning(_(' "%s" Account is not available.') % values.get('account'))
        if product_id:
            product_id = product_id.id
        else:
            product_id = False
            account = False
        vals = {
            'product_id' : product_id,
            'quantity' : values.get('quantity'),
            'price_unit' :values.get('price'),
            'discount':values.get('disc'),
            'name' : values.get('description'),
            'account_id' : account,
            'product_uom_id' : product_uom.id,
        }

        if values.get('analytic_account_id'):
            analytic_account_id = self.env['account.analytic.account'].search([('name','=',values.get('analytic_account_id'))])
            if analytic_account_id:
                analytic_account_id = analytic_account_id
            else:
                raise Warning(_(' "%s" Analytic Account is not available.') % values.get('analytic_account_id'))

        if tag_ids:
            vals.update({'analytic_tag_ids' : [(6, 0, tag_ids)]})
        if values.get('analytic_account_id'):
            vals.update({'analytic_account_id' : analytic_account_id.id,})
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
            self.env.cr.execute("update account_move set vehicle_id=%s where id=%s", [vehicle_id.id,inv_id.id])

            vehicle_id.write({
                'license_plate' : license_plate
            })
        
        if tax_ids:
            vals.update({'tax_ids':([(6,0,tax_ids)])})

        inv_id.write({'invoice_line_ids' :([(0,0,vals)]) })
        return inv_id

    def create_payment(self,payment,values):
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
                    pay_rec = self.env.cr.execute("""INSERT INTO account_payment (amount,currency_id,payment_type,partner_id,partner_type,communication,journal_id,payment_difference_handling,payment_date,payment_method_id,is_import,state) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""" , (abs(float(amount)),res.currency_id.id,amount > 0 and 'inbound' or 'outbound',res.partner_id.commercial_partner_id.id,MAP_INVOICE_TYPE_PARTNER_TYPE[res.type]
                    ," ".join(i.invoice_payment_ref or i.ref or i.name for i in res),journal.id,'open',date_payment,payment_method.id,True,'draft'))
                    self.env.cr.execute('select id from account_payment ORDER BY id DESC limit 1;')

                    payment_id = self.env.cr.fetchone()
                    pay_rec_obj=self.env['account.payment'].browse(payment_id)
                    pay_rec_obj.write({'invoice_ids': [(6, 0, res.ids)],})
                elif self.partial_payment == 'writeoff':
                    pay_rec = self.env.cr.execute("""INSERT INTO account_payment (amount,currency_id,payment_type,partner_id,partner_type,communication,journal_id,payment_difference_handling,writeoff_label,writeoff_account_id,payment_date,payment_method_id,is_import,state) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""" , (abs(amount),res.currency_id.id,amount > 0 and 'inbound' or 'outbound',res.partner_id.commercial_partner_id.id,MAP_INVOICE_TYPE_PARTNER_TYPE[res.type]
                    ," ".join(i.invoice_payment_ref or i.ref or i.name for i in res),journal.id,'open','Write-Off',self.writeoff_account.id,date_payment,payment_method.id,True,'draft'))
                    self.env.cr.execute('select id from account_payment ORDER BY id DESC limit 1;')

                    payment_id = self.env.cr.fetchone()
                    pay_rec_obj=self.env['account.payment'].browse(payment_id)
                    pay_rec_obj.write({'invoice_ids': [(6, 0, res.ids)],})
            else:
                pay_rec = self.env.cr.execute("""INSERT INTO account_payment (amount,currency_id,payment_type,partner_id,partner_type,communication,journal_id,payment_date,payment_method_id,is_import,state) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""" , (abs(amount),res.currency_id.id,amount > 0 and 'inbound' or 'outbound',res.partner_id.commercial_partner_id.id,MAP_INVOICE_TYPE_PARTNER_TYPE[res.type]
                ," ".join(i.invoice_payment_ref or i.ref or i.name for i in res),journal.id,date_payment,payment_method.id,True,'draft'))
                self.env.cr.execute('select id from account_payment ORDER BY id DESC limit 1;')
                payment_id = self.env.cr.fetchone()
                pay_rec_obj=self.env['account.payment'].browse(payment_id)
                pay_rec_obj.write({'invoice_ids': [(6, 0, res.ids)],})

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
            pay_rec_obj.post()
            
    def find_currency(self, name):
        currency_obj = self.env['res.currency']
        currency_search = currency_obj.search([('name', '=', name)])
        if currency_search:
            return currency_search
        else:
            raise Warning(_(' "%s" Currency are not available.') % name)

    
    def find_sales_person(self, name):
        sals_person_obj = self.env['res.users']
        partner_search = sals_person_obj.search([('name', '=', name)])
        if partner_search:
            return partner_search[0]
        else:
            raise Warning(_('Not Valid Salesperson Name "%s"') % name)


    
    def find_partner(self, name):
        partner_obj = self.env['res.partner']
        partner_search = partner_obj.search([('name', '=', name)])
        if partner_search:
            return partner_search[0]
        else:
            partner_id = partner_obj.create({
                'name' : name})
            return partner_id

    
    def find_invoice_date(self, date):
        DATETIME_FORMAT = "%Y-%m-%d"
        i_date = datetime.strptime(date, DATETIME_FORMAT).date()
        return i_date

    
    def import_csv(self):
        """Load Inventory data from the CSV file."""
        if self.stage == 'payment':
            if self.import_option == 'csv':
                try:
                    keys = ['invoice', 'customer', 'currency', 'product','account', 'quantity', 'uom', 'description', 'price','salesperson','tax','date','disc','journal','amount','paymentdate','invoice_origin','vehicle_id','license_plate','analytic_account_id','Analytic_Tags_ids']
                    csv_data = base64.b64decode(self.file)
                    data_file = io.StringIO(csv_data.decode("utf-8"))
                    data_file.seek(0)
                    file_reader = []
                    csv_reader = csv.reader(data_file, delimiter=',')
                    file_reader.extend(csv_reader)
                except Exception:
                    raise exceptions.Warning(_("Invalid file!"))
                values = {}
                payment = {}
                invoice_ids=[]
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
                        self.create_payment(payment,values)
            else:
                try:
                    fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
                    fp.write(binascii.a2b_base64(self.file))
                    fp.seek(0)
                    values = {}
                    payment = {}
                    invoice_ids=[]
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
                        # if self.account_opt == 'default':
                        #     if len(line) == 13:
                        a1 = int(float(line[11]))
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
                                        'salesperson': line[9],
                                        'tax': line[10],
                                        'date': date_string,
                                        'seq_opt':self.sequence_opt,
                                        'disc':line[12],
                                        'analytic_account_id' : line[19],
                                        'Analytic_Tags_ids' : line[20],
                                        'invoice_origin' : line[16],
                                        'vehicle_id' : line[17],
                                        'license_plate' : line[18],
                                        })
                        count = 0
                        for l_fields in line_fields:
                            if(count > 12):
                                values.update({l_fields : line[count]})                        
                            count+=1                     
                        #     elif len(line) > 13:
                        #         raise Warning(_('Your File has extra column please refer sample file'))
                        #     else:
                        #         raise Warning(_('Your File has less column please refer sample file'))
                        # else:
                        #     if len(line) == 13:
                            #     a1 = int(float(line[11]))
                            #     a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                            #     date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                            #     values.update( {'invoice':line[0],
                            #                     'customer': line[1],
                            #                     'currency': line[2],
                            #                     'product': line[3].split('.')[0],
                            #                     'account': line[4],
                            #                     'quantity': line[5],
                            #                     'uom': line[6],
                            #                     'description': line[7],
                            #                     'price': line[8],
                            #                     'salesperson': line[9],
                            #                     'tax': line[10],
                            #                     'date': date_string,
                            #                     'seq_opt':self.sequence_opt,
                            #                     'disc':line[12]
                            #                     })
                            # elif len(line) > 13:
                            #     raise Warning(_('Your File has extra column please refer sample file'))
                            # else:
                            #     raise Warning(_('Your File has less column please refer sample file'))
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
                    self.create_payment(payment,values)
                return res
        else:
            if self.import_option == 'csv':
                try:
                    keys = ['invoice', 'customer', 'currency', 'product','account', 'quantity', 'uom', 'description', 'price','salesperson','tax','date','disc','invoice_origin','vehicle_id','license_plate','analytic_account_id','Analytic_Tags_ids']
                    csv_data = base64.b64decode(self.file)
                    data_file = io.StringIO(csv_data.decode("utf-8"))
                    data_file.seek(0)
                    file_reader = []
                    csv_reader = csv.reader(data_file, delimiter=',')
                    file_reader.extend(csv_reader)
                except Exception:
                    raise exceptions.Warning(_("Invalid file!"))
                values = {}
                payment = {}
                invoice_ids=[]
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
                        self.create_payment(payment,values)
            else:
                try:
                    fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
                    fp.write(binascii.a2b_base64(self.file))
                    fp.seek(0)
                    values = {}
                    payment = {}
                    invoice_ids=[]
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
                        # if self.account_opt == 'default':
                        #     if len(line) == 13:
                        a1 = int(float(line[11]))
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
                                        'salesperson': line[9],
                                        'tax': line[10],
                                        'date': date_string,
                                        'seq_opt':self.sequence_opt,
                                        'disc':line[12],
                                        'analytic_account_id' : line[16],
                                        'Analytic_Tags_ids' : line[17],
                                        'invoice_origin' : line[13],
                                        'vehicle_id' : line[14],
                                        'license_plate' : line[15],
                                        })
                        count = 0
                        for l_fields in line_fields:
                            if(count > 12):
                                values.update({l_fields : line[count]})                        
                            count+=1                     
                        #     elif len(line) > 13:
                        #         raise Warning(_('Your File has extra column please refer sample file'))
                        #     else:
                        #         raise Warning(_('Your File has less column please refer sample file'))
                        # else:
                        #     if len(line) == 13:
                            #     a1 = int(float(line[11]))
                            #     a1_as_datetime = datetime(*xlrd.xldate_as_tuple(a1, workbook.datemode))
                            #     date_string = a1_as_datetime.date().strftime('%Y-%m-%d')
                            #     values.update( {'invoice':line[0],
                            #                     'customer': line[1],
                            #                     'currency': line[2],
                            #                     'product': line[3].split('.')[0],
                            #                     'account': line[4],
                            #                     'quantity': line[5],
                            #                     'uom': line[6],
                            #                     'description': line[7],
                            #                     'price': line[8],
                            #                     'salesperson': line[9],
                            #                     'tax': line[10],
                            #                     'date': date_string,
                            #                     'seq_opt':self.sequence_opt,
                            #                     'disc':line[12]
                            #                     })
                            # elif len(line) > 13:
                            #     raise Warning(_('Your File has extra column please refer sample file'))
                            # else:
                            #     raise Warning(_('Your File has less column please refer sample file'))
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
                    self.create_payment(payment,values)
                return res

