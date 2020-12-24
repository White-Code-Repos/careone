# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011 SYLEAM (<http://syleam.fr/>)
#    Copyright (C) 2013 Julius Network Solutions SARL <contact@julius.fr>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
import urllib
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


import logging
_logger = logging.getLogger(__name__)
try:
    from SOAPpy import WSDL
except :
    _logger.warning("ERROR IMPORTING SOAPpy, if not installed, please install it:"
    " e.g.: apt-get install python-soappy")


class SMSClient(models.Model):

    _name = 'sms.smsclient'
    _description = 'SMS Client'

    name = fields.Char('Gateway Name', size=256, required=True)
    url = fields.Char('Gateway URL', size=256,
            required=True, help='Base url for message')
    property_ids = fields.One2many('sms.smsclient.parms',
            'gateway_id', 'Parameters')
    history_line = fields.One2many('sms.smsclient.history',
            'gateway_id', 'History')
    method = fields.Selection([
                ('http', 'HTTP Method'),
                ('smpp', 'SMPP Method')
            ], 'API Method',  default = 'http')
    state = fields.Selection([
                ('new', 'Not Verified'),
                ('waiting', 'Waiting for Verification'),
                ('confirm', 'Verified'),
            ], 'Gateway Status',  default= 'new', readonly=True)
    users_id = fields.Many2many('res.users',
            'res_smsserver_group_rel', 'sid', 'uid', 'Users Allowed')
    code = fields.Char('Verification Code', size=256)
    body = fields.Text('Message',
            help="The message text that will be send along with the email which is send through this server")
    validity = fields.Integer('Validity',
            help='The maximum time -in minute(s)- before the message is dropped', default = 10)
    classes = fields.Selection([
                ('0', 'Flash'),
                ('1', 'Phone display'),
                ('2', 'SIM'),
                ('3', 'Toolkit')
            ], 'Class',
            help='The SMS class: flash(0),phone display(1),SIM(2),toolkit(3)', default ='1')
    deferred = fields.Integer('Deferred',
            help='The time -in minute(s)- to wait before sending the message', default = 0)
    priority = fields.Selection([
                ('0', '0'),
                ('1', '1'),
                ('2', '2'),
                ('3', '3')
            ], 'Priority', help='The priority of the message ')
    coding = fields.Selection([
                ('1', '7 bit'),
                ('2', 'Unicode')
            ],'Coding', help='The SMS coding: 1 for 7 bit or 2 for unicode')

    tag = fields.Char('Tag', size=256, help='an optional tag')
    nostop = fields.Boolean('NoStop', help='Do not display STOP clause in the message, this requires that this is not an advertising message', default = True )
    char_limit = fields.Boolean('Character Limit' , default = True)
    

    def _check_permissions(self):
        self._cr.execute('select * from res_smsserver_group_rel where  uid=%s' % ( self.env.uid))
        data = self._cr.fetchall()
        if len(data) <= 0:
            return False
        return True


    def _prepare_smsclient_queue(self, data, name):
        return {
            'name': name,
            'gateway_id': data.gateway.id,
            'state': 'draft',
            'mobile': data.mobile_to,
            'msg': data.text,
            'validity': data.validity, 
            'classes': data.classes1, 
            'deffered': data.deferred, 
            'priorirty': data.priority, 
            'coding': data.coding, 
            'tag': data.tag, 
            'nostop': data.nostop1,
        }

    def send_msg(self, data):
        if self._context is None:
            self._context = {}
        gateway = data.gateway
        if gateway:
            if not self._check_permissions():

                raise UserError(_('You have no permission to access %s') % (gateway.name,) )
            url = gateway.url
            name = url
            if gateway.method == 'http':
                prms = {}
                for p in data.gateway.property_ids:
                     if p.type == 'user':
                         
                         prms[p.name] = p.value
                     elif p.type == 'password':
                         prms[p.name] = p.value
                     elif p.type == 'to':
                         prms[p.name] = data.mobile_to
                     elif p.type == 'sms':
                         prms[p.name] = data.text
                     elif p.type == 'extra':
                         prms[p.name] = p.value
                
                params = urllib.urlencode(prms)
                name = url + "?" + params

            queue_obj = self.env['sms.smsclient.queue']
            vals = self._prepare_smsclient_queue(data, name )
            queue_obj.create(vals)
        return True

        
    def _check_queue(self):
        if self._context is None:
            self._context = {}
        queue_obj = self.env['sms.smsclient.queue']
        history_obj = self.env['sms.smsclient.history']
        sids = queue_obj.search( [
                ('state', '!=', 'send'),
                ('state', '!=', 'sending')
            ], limit=30)
        sids.write({'state': 'sending'})
        error_ids = []
        sent_ids = []
        
        
        for sms in sids:
            if sms.gateway_id.char_limit:
                if len(sms.msg) > 160:
                    error_ids.append(sms.id)
                    continue
            if sms.gateway_id.method == 'http':
                try:
                    urllib.urlopen(sms.name)
                except Exception:
                    
                    
                    raise UserError(_('Error %s') % (e) )                    
            if sms.gateway_id.method == 'smpp':
                for p in sms.gateway_id.property_ids:
                    if p.type == 'user':
                        login = p.value
                    elif p.type == 'password':
                        pwd = p.value
                    elif p.type == 'sender':
                        sender = p.value
                    elif p.type == 'sms':
                        account = p.value
                try:
                    soap = WSDL.Proxy(sms.gateway_id.url)
                    message = ''
                    if sms.coding == '2':
                        message = str(sms.msg).decode('iso-8859-1').encode('utf8')
                    if sms.coding == '1':
                        message = str(sms.msg)
                    result = soap.telephonySmsUserSend(str(login), str(pwd),
                        str(account), str(sender), str(sms.mobile), message,
                        int(sms.validity), int(sms.classes), int(sms.deferred),
                        int(sms.priority), int(sms.coding),str(sms.gateway_id.tag), int(sms.gateway_id.nostop))
                except Exception:
                    raise UserError(_('Error %s') % (e) )    
                
            history_obj.create( {
                            'name': _('SMS Sent'),
                            'gateway_id': sms.gateway_id.id,
                            'sms': sms.msg,
                            'to': sms.mobile,
                        })
            sent_ids.append(sms.id)
        for sent_id in sent_ids:
            browse_record = queue_obj.browse(sent_id)
            browse_record.state = 'send'
        for id in  error_ids:
          browse_record = queue_obj.browse(sent_id)     
          browse_record.state = 'error'
          browse_record.error =  'Size of SMS should not be more then 160 char'
        return True



class SMSQueue(models.Model):

    _name = 'sms.smsclient.queue'
    
    _description = 'SMS Queue'


    name =  fields.Text('SMS Request', size=256,
            required=True, readonly=True,
            states={'draft': [('readonly', False)]})
    msg = fields.Text('SMS Text', size=256,
            required=True, readonly=True,
            states={'draft': [('readonly', False)]})
    mobile = fields.Char('Mobile No', size=256,
            required=True, readonly=True,
            states={'draft': [('readonly', False)]})
    gateway_id=  fields.Many2one('sms.smsclient',
            'SMS Gateway', readonly=True,
            states={'draft': [('readonly', False)]})
    state = fields.Selection([
            ('draft', 'Queued'),
            ('sending', 'Waiting'),
            ('send', 'Sent'),
            ('error', 'Error'),
        ], 'Message Status', readonly=True,  default  =  'draft')
    error = fields.Text('Last Error', size=256,
            readonly=True,
            states={'draft': [('readonly', False)]})
    date_create = fields.Datetime('Date', readonly=True,  default=lambda self: fields.Datetime.now())
    validity = fields.Integer('Validity',
            help='The maximum time -in minute(s)- before the message is dropped')
    priority= fields.Selection([
                ('0', '0'),
                ('1', '1'),
                ('2', '2'),
                ('3', '3')
            ], 'Priority', help='The priority of the message ')

    classes  = fields.Selection([
                ('0', 'Flash'),
                ('1', 'Phone display'),
                ('2', 'SIM'),
                ('3', 'Toolkit')
            ], 'Class', help='The sms class: flash(0), phone display(1), SIM(2), toolkit(3)')
    deferred = fields.Integer('Deferred',
            help='The time -in minute(s)- to wait before sending the message')
    coding = fields.Selection([
                ('1', '7 bit'),
                ('2', 'Unicode')
            ], 'Coding', help='The sms coding: 1 for 7 bit or 2 for unicode')
    tag = fields.Char('Tag',
            help='An optional tag')
    nostop=  fields.Boolean('NoStop', help='Do not display STOP clause in the message, this requires that this is not an advertising message')
        
  
class Properties(models.Model):

    _name = 'sms.smsclient.parms'
    _description = 'SMS Client Properties'

    name = fields.Char('Property name', size=256,
             help='Name of the property whom appear on the URL')
    value = fields.Char('Property value', size=256,
             help='Value associate on the property for the URL')
    gateway_id = fields.Many2one('sms.smsclient', 'SMS Gateway')
    type = fields.Selection([
                ('user', 'User'),
                ('password', 'Password'),
                ('sender', 'Sender Name'),
                ('to', 'Recipient No'),
                ('sms', 'SMS Message'),
                ('extra', 'Extra Info')
            ], 'API Method',
            help='If parameter concern a value to substitute, indicate it')

class HistoryLine(models.Model):

    _name = 'sms.smsclient.history'
    _description = 'SMS Client History'


    name = fields.Char('Description', size=160, required=True, readonly=True)
    date_create = fields.Datetime('Date', readonly=True)
    user_id = fields.Many2one('res.users', 'Username', readonly=True)
    gateway_id = fields.Many2one('sms.smsclient', 'SMS Gateway', ondelete='set null')
    to = fields.Char('Mobile No', size=15, readonly=True)
    sms = fields.Text('SMS', size=160, readonly=True)




class partner_sms_send(models.Model):

    _name = "partner.sms.send"


    @api.model
    def _default_get_mobile(self):
        if self._context is None:
            self._context = {}
        partner_pool = self.env['res.partner']
        active_ids = self._context.get('active_ids')
        res = {}
        i = 0
        for partner in partner_pool.browse(active_ids): 
            i += 1           
            res = partner.mobile
        if i > 1:
            raise UserError(_('You can only select one partner'))
        return res

    @api.model
    def _default_get_gateway(self):
        if self._context is None:
            self._context = {}
        sms_obj = self.env['sms.smsclient']
        gateway_ids = sms_obj.search([], limit=1)
        return gateway_ids and gateway_ids[0] or False



    @api.onchange('gateway_id')
    def onchange_gateway(self):
        if self._context is None:
            context = {}
        sms_obj = self.env['sms.smsclient']
        if not gateway_id:
            return {}
        gateway = sms_obj.browse( gateway_id, context=context)
        return {
            'value': {
                'validity': gateway.validity, 
                'classes': gateway.classes,
                'deferred': gateway.deferred,
                'priority': gateway.priority,
                'coding': gateway.coding,
                'tag': gateway.tag,
                'nostop': gateway.nostop,
            }
        }

  
    mobile_to = fields.Char('To', required=True, default = _default_get_mobile)

    app_id = fields.Char('API ID' )

    user = fields.Char('Login' )

    password = fields.Char('Password')

    text = fields.Text('SMS Message', required=True)

    gateway = fields.Many2one('sms.smsclient', 'SMS Gateway', default = _default_get_gateway)

    validity = fields.Integer('Validity',
            help='the maximum time -in minute(s)- before the message is dropped')

    classes1 = fields.Selection([
                ('0', 'Flash'),
                ('1', 'Phone display'),
                ('2', 'SIM'),
                ('3', 'Toolkit')
            ], 'Class', help='the sms class: flash(0), phone display(1), SIM(2), toolkit(3)')

    deferred = fields.Integer('Deferred',
            help='the time -in minute(s)- to wait before sending the message')

    priority = fields.Selection([
                ('0','0'),
                ('1','1'),
                ('2','2'),
                ('3','3')
            ], 'Priority', help='The priority of the message')

    coding = fields.Selection([
                ('1', '7 bit'),
                ('2', 'Unicode')
            ], 'Coding', help='The SMS coding: 1 for 7 bit or 2 for unicode')

    tag = fields.Char('Tag', help='an optional tag')

    nostop1 = fields.Boolean('NoStop', help='Do not display STOP clause in the message, this requires that this is not an advertising message')
    

    def sms_send(self):
        if self._context is None:
            self._context = {}
        client_obj = self.env['sms.smsclient']
        for data in self:
            if not data.gateway:
                raise UserError(_('You can only select one partner'))
            else:
                client_obj.send_msg(data)
        return True
     


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
