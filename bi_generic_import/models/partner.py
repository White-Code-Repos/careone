# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import tempfile
import binascii
import xlrd
from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
import time
from datetime import date, datetime
import io
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

class gen_partner(models.TransientModel):
    _name = "gen.partner"

    file = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='csv')
    partner_option = fields.Selection([('create','Create Partner'),('update','Update Partner')],string='Option', required=True,default="create")

    
    def find_country(self,val):
        if type(val) == dict:
            country_search = self.env['res.country'].search([('name','=',val.get('country'))])
            if country_search:
                return country_search.id
            else:
                country = self.env['res.country'].create({'name':val.get('country')})
                return country.id
        else:
            country_search = self.env['res.country'].search([('name','=',val[9])])
            if country_search:
                return country_search.id
            else:
                country = self.env['res.country'].create({'name':val[9]})
                return country.id

    
    def find_state(self,val):
        if type(val) == dict:
            if val.get('country'):
                country_search = self.env['res.country'].search([('name','=',val.get('country'))],limit=1)
                state_search = self.env['res.country.state'].search([('name','=',val.get('state')),('country_id','=',country_search.id)])
            else:
                state_search = self.env['res.country.state'].search([('name','=',val.get('state'))])
            
            if state_search:
                if len(state_search.ids)> 1:
                    raise Warning('Multiple States of name %s found. Please provide Country.'%val.get('state'))
                else:
                    return state_search.id
            else:
                if not val.get('country'):
                    raise Warning('State is not available in system And without country you can not create state')
                else:
                    country_search = self.env['res.country'].search([('name','=',val.get('country'))])
                    if not country_search:
                        country_crt = self.env['res.country'].create({'name':val.get('country')})
                        country = country_crt
                    else:
                        country = country_search

                    states = self.env['res.country.state'].search([['code','=',val.get('state')[:3]],['country_id','=',country.id]])
                    if states:
                        if not val.get('state_code'):
                            raise Warning(_('Another State with code "%s" found in country "%s". Please Provide State Code in XLS/CSV.'%(val.get('state')[:3],country.name) ))
                        else:
                            code = str(val.get('state_code'))
                    else:
                        code = val.get('state')[:3]

                    state = self.env['res.country.state'].create({
                                                      'name':val.get('state'),
                                                      'code':code,
                                                     'country_id':country.id
                                                      })
                    return state.id
        else:
            if val[9]:
                country_search = self.env['res.country'].search([('name','=',val[9])],limit=1)
                state_search = self.env['res.country.state'].search([('name','=',val[6]),('country_id','=',country_search.id)])
            else:
                state_search = self.env['res.country.state'].search([('name','=',val[6])])
            
            if state_search:
                if len(state_search.ids)> 1:
                    raise Warning('Multiple States of name %s found. Please provide Country.'%val[6])
                else:
                    return state_search.id
            else:
                if not val[9]:
                    raise Warning('State is not available in system And without country you can not create state')
                else:
                    country_search = self.env['res.country'].search([('name','=',val[9])])
                    if not country_search:
                        country_crt = self.env['res.country'].create({'name':val[9]})
                        country = country_crt
                        
                    else:
                        country = country_search

                    states = self.env['res.country.state'].search([['code','=',val[6][:3] ],['country_id','=',country.id]])
                    if states:
                        if not val[7]:
                            raise Warning(_('Another State with code "%s" found in country "%s". Please Provide State Code in XLS/CSV.'%(val[6][:3],country.name) ))
                        else:
                            code = str(val[7])
                    else:
                        code = val[6][:3]

                    state = self.env['res.country.state'].create({
                                                      'name':val[6],
                                                      'code':code,
                                                     'country_id':country.id
                                                      })
                    return state.id   


    
    def create_partner(self, values):
        parent = state = country = saleperson =  vendor_pmt_term = cust_pmt_term = False
        
        if values.get('type').lower() == 'company':
            if values.get('parent'):
                raise Warning('You can not give parent if you have select type is company')
            var_type =  'company'
        else:
            var_type =  'person'

            if values.get('parent'):
                parent_search = self.env['res.partner'].search([('name','=',values.get('parent'))])
                if parent_search:
                    parent =  parent_search.id
                else:
                    raise Warning("Parent contact  not available")
        if values.get('state'):
            state = self.find_state(values)
        if values.get('country'):
            country = self.find_country(values)
        if values.get('saleperson'):
            saleperson_search = self.env['res.users'].search([('name','=',values.get('saleperson'))])
            if not saleperson_search:
                raise Warning("Salesperson not available in system")
            else:
                saleperson = saleperson_search.id
        if values.get('cust_pmt_term'):
            cust_payment_term_search = self.env['account.payment.term'].search([('name','=',values.get('cust_pmt_term'))])
            if cust_payment_term_search:
                cust_pmt_term = cust_payment_term_search.id
        if values.get('vendor_pmt_term'):
            vendor_payment_term_search = self.env['account.payment.term'].search([('name','=',values.get('vendor_pmt_term'))])
            
            if vendor_payment_term_search:
                vendor_pmt_term = vendor_payment_term_search.id
        customer = values.get('customer')
        supplier = values.get('vendor')
        is_customer = False
        is_supplier = False
        if ((values.get('customer')) in ['1','1.0','True']):
        	is_customer = True
        	
        if ((values.get('vendor')) in ['1','1.0','True']):
        	is_supplier = True
        
        vals = {
                  'name':values.get('name'),
                  'company_type':var_type,
                  'parent_id':parent,
                  'street':values.get('street'),
                  'street2':values.get('street2'),
                  'city':values.get('city'),
                  'state_id':state,
                  'zip':values.get('zip'),
                  'country_id':country,
                  'website':values.get('website'),
                  'phone':values.get('phone'),
                  'mobile':values.get('mobile'),
                  'email':values.get('email'),
                  'user_id':saleperson,
                  'ref':values.get('ref'),
                  'property_payment_term_id':cust_pmt_term,
                  'property_supplier_payment_term_id':vendor_pmt_term,
                  }
        if is_customer:
            vals.update({
                'customer_rank' : 1
                })

        if is_supplier:
            vals.update({
                'customer_rank' : 1
                })            
        partner_search = self.env['res.partner'].search([('name','=',values.get('name'))]) 
        if partner_search:
            raise Warning(_('"%s" Customer/Vendor already exist.') % values.get('name'))  
        else:
            res = self.env['res.partner'].create(vals)

    def import_partner(self):
        if self.import_option == 'csv':  
            try:
                keys = ['name','type','parent','street','street2','city','state','state_code','zip','country','website','phone','mobile','email','customer','vendor','saleperson','ref','cust_pmt_term','vendor_pmt_term']
                csv_data = base64.b64decode(self.file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                file_reader = []
                res = {}
                csv_reader = csv.reader(data_file, delimiter=',')
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))

            for i in range(len(file_reader)):
                values = {}
                field = map(str, file_reader[i])
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        values.update({'option':self.import_option})
                        if self.partner_option == 'create':
                            res = self.create_partner(values)
                        else:
                            search_partner = self.env['res.partner'].search([('name','=',values.get('name'))])
                            parent = False
                            state = False
                            country = False
                            saleperson = False
                            vendor_pmt_term = False
                            cust_pmt_term = False

                            is_customer = False
                            is_supplier = False
                            if ((values.get('customer')) in ['1','1.0','True']):
                                is_customer = True
                                
                            if ((values.get('vendor')) in ['1','1.0','True']):
                                is_supplier = True
                           
                            if values.get('type').lower() == 'company':
                                if values.get('parent'):
                                    raise Warning('You can not give parent if you have select type is company')
                                type =  'company'
                            else:
                                type =  'person'

                                if values.get('parent'):
                                    parent_search = self.env['res.partner'].search([('name','=',values.get('parent'))])
                                    if parent_search:
                                        parent =  parent_search.id
                                    else:
                                        raise Warning("Parent contact  not available")
                            
                            if values.get('state'):
                                state = self.find_state(values)
                            if values.get('country'):
                                country = self.find_country(values)
                            if values.get('saleperson'):
                                saleperson_search = self.env['res.users'].search([('name','=',values.get('saleperson'))])
                                if not saleperson_search:
                                    raise Warning("Salesperson not available in system")
                                else:
                                    saleperson = saleperson_search.id
                            if values.get('cust_pmt_term'):
                                cust_payment_term_search = self.env['account.payment.term'].search([('name','=',values.get('cust_pmt_term'))])
                                if not cust_payment_term_search:
                                    raise Warning("Payment term not available in system")
                                else:
                                    cust_pmt_term = cust_payment_term_search.id
                            if values.get('vendor_pmt_term'):
                                vendor_payment_term_search = self.env['account.payment.term'].search([('name','=',values.get('vendor_pmt_term'))])
                                if not vendor_payment_term_search:
                                    raise Warning("Payment term not available in system")
                                else:
                                    vendor_pmt_term = vendor_payment_term_search.id
                            
                            if search_partner:
                                search_partner.company_type = type
                                search_partner.parent_id = parent or False
                                search_partner.street = values.get('street')
                                search_partner.street2 = values.get('street2')
                                search_partner.city = values.get('city')
                                search_partner.state_id = state
                                search_partner.zip = values.get('zip')
                                search_partner.country_id = country
                                search_partner.website = values.get('website')
                                
                                search_partner.phone = values.get('phone')
                                search_partner.mobile = values.get('mobile')
                                search_partner.email = values.get('email')
                                search_partner.customer = is_customer
                                search_partner.supplier = is_supplier
                                search_partner.user_id = saleperson
                                search_partner.ref = values.get('ref')
                                search_partner.property_payment_term_id = cust_pmt_term or False
                                search_partner.property_supplier_payment_term_id = vendor_pmt_term or False
                            else:
                                raise Warning(_('%s partner not found.') % values.get('name'))
        else:
            try:
                fp = tempfile.NamedTemporaryFile(delete=False,suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.Warning(_("Invalid file!"))

            for row_no in range(sheet.nrows):
                values = {}
                res = {}
                if row_no <= 0:
                    fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    if self.partner_option == 'create':
                        values.update( {'name':line[0],
                                        'type': line[1],
                                        'parent': line[2],
                                        'street': line[3],
                                        'street2': line[4],
                                        'city': line[5],
                                        'state': line[6],
                                        'state_code': line[7],
                                        'zip': line[8],
                                        'country': line[9],
                                        'website': line[10],
                                        'phone': line[11],
                                        'mobile': line[12],
                                        'email': line[13],
                                        'customer': str(line[14]),
                                        'vendor': str(line[15]),
                                        'saleperson': line[16],
                                        'ref': line[17],
                                        'cust_pmt_term': line[18],
                                        'vendor_pmt_term': line[19],
                                        
                                        })
                        res = self.create_partner(values)
                    else:
                        search_partner = self.env['res.partner'].search([('name','=',line[0])])
                        parent = False
                        state = False
                        country = False
                        saleperson = False
                        vendor_pmt_term = False
                        cust_pmt_term = False

                        is_customer = False
                        is_supplier = False
                        if line[14]:
                            if int(float(line[14])) == 1:
                               is_customer = True

                        if line[15]:
                            if int(float(line[15])) == 1:
                               is_supplier = True
                               
                        if line[1] == 'company':
                            if line[2]:
                                raise Warning('You can not give parent if you have select type is company')
                            type =  'company'
                        else:
                            type =  'person'
                            
                            if line[2]:
                                parent_search = self.env['res.partner'].search([('name','=',line[2])])
                                if parent_search:
                                    parent =  parent_search.id
                                else:
                                    raise Warning("Parent contact  not available")
                        
                        if line[6]:
                            state = self.find_state(line)
                        if line[9]:
                            country = self.find_country(line)
                        if line[16]:
                            saleperson_search = self.env['res.users'].search([('name','=',line[16])])
                            if not saleperson_search:
                                raise Warning("Salesperson not available in system")
                            else:
                                saleperson = saleperson_search.id
                        if line[18]:
                            cust_payment_term_search = self.env['account.payment.term'].search([('name','=',line[18])])
                            if not cust_payment_term_search:
                                raise Warning("Payment term not available in system")
                            else:
                                cust_pmt_term = cust_payment_term_search.id
                        if line[19]:
                            vendor_payment_term_search = self.env['account.payment.term'].search([('name','=',line[19])])
                            if not vendor_payment_term_search:
                                raise Warning("Payment term not available in system")
                            else:
                                vendor_pmt_term = vendor_payment_term_search.id
                        
                        if search_partner:
                            search_partner.company_type = type
                            search_partner.parent_id = parent or False
                            search_partner.street = line[3]
                            search_partner.street2 = line[4]
                            search_partner.city = line[5]
                            search_partner.state_id = state
                            search_partner.zip = line[8]
                            search_partner.country_id = country
                            search_partner.website = line[10]
                            
                            search_partner.phone = line[11]
                            search_partner.mobile = line[12]
                            search_partner.email = line[13]
                            search_partner.customer = is_customer
                            search_partner.supplier = is_supplier
                            search_partner.user_id = saleperson
                            search_partner.ref = line[17]
                            search_partner.property_payment_term_id = cust_pmt_term or False
                            search_partner.property_supplier_payment_term_id = vendor_pmt_term or False
                        else:
                            raise Warning(_('%s partner not found.') % line[0])
        
        return res

