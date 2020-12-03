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
import re 
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
    _inherit = "gen.partner"
    _description = "Gen Partner"

    

    
    
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
                  #'company_type':var_type,
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
                  'is_import' : True,
                  'active':True
                  # 'property_payment_term_id':cust_pmt_term,
                  # 'property_supplier_payment_term_id':vendor_pmt_term,
                  }

        if not parent:
             vals = {
                  'name':values.get('name'),
                  #'company_type':var_type,
                  #'parent_id':parent,
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
                  'is_import' : True,
                  'active':True
                  # 'property_payment_term_id':cust_pmt_term,
                  # 'property_supplier_payment_term_id':vendor_pmt_term,
                  }

        if is_customer:
            vals.update({
                'customer_rank' : 1
                })

        if is_supplier:
            vals.update({
                'customer_rank' : 1
                })

        main_list = values.keys()
        count = 0
        for i in main_list:
            model_id = self.env['ir.model'].search([('model','=','res.partner')])           
            if count > 19:
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
                                            vals.update({
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
                                    vals.update({
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
                                vals.update({
                                    normal_details : values.get(i)
                                    })
                            elif normal_fields.ttype == 'char':
                                vals.update({
                                    normal_details : values.get(i)
                                    })                              
                            elif normal_fields.ttype == 'float':
                                if values.get(i) == '':
                                    float_value = 0.0
                                else:
                                    float_value = float(values.get(i)) 
                                vals.update({
                                    normal_details : float_value
                                    })                              
                            elif normal_fields.ttype == 'integer':
                                if values.get(i) == '':
                                    int_value = 0
                                else:
                                    int_value = int(values.get(i)) 
                                vals.update({
                                    normal_details : int_value
                                    })                             
                            elif normal_fields.ttype == 'selection':
                                vals.update({
                                    normal_details : values.get(i)
                                    })                              
                            elif normal_fields.ttype == 'text':
                                vals.update({
                                    normal_details : values.get(i)
                                    })                              
                        else:
                            raise Warning(_('"%s" This custom field is not available in system') % normal_details)
            count+= 1
        partner_search = self.env['res.partner'].search([('name','=',values.get('name'))]) 
        if partner_search:
            raise Warning(_('"%s" Customer/Vendor already exist.') % values.get('name'))  
        else:

            tech_tuple= []
            val_tuple = []
            store_tuple = []

            
            for tech_name in vals :
                tech_tuple.append(tech_name)
                val_tuple.append(vals[tech_name])
                store_tuple.append("%s")

            tech_tuple = tuple(tech_tuple) 
            val_tuple = tuple(val_tuple) 
            store_tuple = tuple(store_tuple) 

            tec_str = "("
            store_str = "("
            
            for i in range (0,len(tech_tuple)) :
                if i == len(tech_tuple) - 1 :
                    tec_str = tec_str + str(tech_tuple[i]) + ')'
                    store_str = store_str + "%s" + ')'

                else :

                    tec_str = tec_str + str(tech_tuple[i]) + ','
                    store_str = store_str + "%s" + ','

            print(tec_str)
            print(store_str)
            select_queru = """INSERT INTO res_partner """ + tec_str + """ VALUES """ + store_str
                        

            res = self.env.cr.execute(select_queru,val_tuple)
                
            # res = self.env['res.partner'].create(vals)

    