##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError



class part_sms(models.TransientModel):
    _name = 'part.sms'

    def _default_get_gateway(self):
        if self._context is None:
            self._context = {}
        sms_obj = self.env['sms.smsclient']
        gateway_ids = sms_obj.search( [], limit=1)
        return gateway_ids and gateway_ids[0] or False



    @api.onchange('gateway_id')
    def onchange_gateway_mass(self):
        if context is None:
            context = {}
        if not gateway_id:
            return {}
        sms_obj = self.pool.get('sms.smsclient')
        gateway = sms_obj.browse(self.gateway_id)
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

    def _merge_message(self, cr, uid, message, object, partner, context=None):
        def merge(match):
            exp = str(match.group()[2: -2]).strip()
            result = eval(exp, {'object': object, 'partner': partner})
            if result in (None, False):
                return str("--------")
            return str(result)
        com = re.compile('(\[\[.+?\]\])')
        msg = com.sub(merge, message)
        return msg

    def sms_mass_send(self):
        datas = {}
        gateway_id = self.gateway.id
        client_obj = self.env['sms.smsclient']
        partner_obj = self.env['res.partner']
        active_ids = self._context.get('active_ids')
        for data in self:
            if not data.gateway:
                raise UserError(_('You can only select one partner'))

            else:
                for partner in partner_obj.browse(active_ids ):
                    data.mobile_to = partner.mobile
                    client_obj._send_message(data)
        return True

    gateway = fields.Many2one('sms.smsclient', 'SMS Gateway', required=True)
    text  = fields.Text('Text', required=True)
    validity  = fields.Integer('Validity',
            help='The maximum time -in minute(s)- before the message is dropped')
    classes = fields.Selection([
                ('0', 'Flash'),
                ('1', 'Phone display'),
                ('2', 'SIM'),
                ('3', 'Toolkit'),
            ], 'Class',
            help='The sms class: flash(0),phone display(1),SIM(2),toolkit(3)')
    deferred = fields.Integer('Deferred',
            help='The time -in minute(s)- to wait before sending the message')
    priority = fields.Selection([
                ('0', '0'),
                ('1', '1'),
                ('2', '2'),
                ('3', '3')
            ], 'Priority', help='The priority of the message')
    coding  = fields.Selection([
                ('1', '7 bit'),
                ('2', 'Unicode')
            ], 'Coding', help='The sms coding: 1 for 7 bit or 2 for unicode')
    tag  = fields.Char('Tag', size=256, help='An optional tag')
    nostop = fields.Selection([
                ('0', '0'),
                ('1', '1')
            ], 'NoStop',
            help='Do not display STOP clause in the message, this requires that this is not an advertising message')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
