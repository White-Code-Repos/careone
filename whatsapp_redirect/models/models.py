# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nishad (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def send_msg(self):
        msg = """مرحبًا  باسم البلاجي%0a
نشكرك لإختيارك كير ون وإعطائنا الفرصة لخدمتك ، و نعدك أن نكون عند حسن ظنك ، و في حال وجود أي سؤال أو استفسار لا تتردد أبداً في التواصل معنا عبر :%0a
الجوال 0506068020%0a
أو الإيميل info@care1cc.com%0a
أو عبر مواقع التواصل  الإجتماعي @care1cc%0a
نتمنى لك يوم سعيد ،،،%0a
"""


        return {'type': 'ir.actions.act_window',
                'name': _('Whatsapp Message'),
                'res_model': 'whatsapp.message.wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_user_id': self.id,
                            'default_message':msg
                            },
                }

class AccountMove(models.Model):
    _inherit = 'account.move'


    def send_msg(self):

        msg = "مرحبًا  باسم البلاجي\n%0aنأمل أن تكون خدماتنا حازت على رضاك ،،\n%0a"
        msg +=  self.name+" ونود إشعارك بفاتورتك رقم %0a\n"
        msg += self.invoice_date.strftime("%m/%d/%Y")+" التي تم إنشاؤها بتاريخ \n%0a"
        msg += "بقيمة إجمالية"+str(self.amount_total) +" ريال ، فيما يلي تفاصيل طلبك.%0a\n"

        for line in self.invoice_line_ids:
            msg += "الوصف :" + line.name + "\n%0a"
            msg += "الكمية :" + str(line.quantity) + "\n%0a"
            msg += "سعر الوحدة :" + str(line.price_unit) + "\n%0a"
            msg += "المجموع الفرعي :" + str(line.price_subtotal) + "\n%0a"
            msg += "-------------------------------\n%0a"
        msg += """مرفق لك مستند الفاتورة والذي سيساعدك في الحصول على معلومات مفصلة
كما يمكنك الإطلاع  و دفع هذه الفاتورة عن طريق الرابط التالي :
https://careone.odoo.com
        """
        return {'type': 'ir.actions.act_window',
                'name': _('Whatsapp Message'),
                'res_model': 'whatsapp.message.wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_user_id': self.partner_id.id,
                            'default_message':msg
                            },
                }

class SaleOrder(models.Model):
    _inherit = 'sale.order'



    def send_msg(self):
        msg = "مرحبًا  باسم البلاجي\n%0aنأمل أن تكون خدماتنا حازت على رضاك ،،\n%0a"
        msg +=  self.name+" ونود إشعارك بعرض الأسعار الخاص بك برقم %0a\n"
        msg += self.date_order.strftime("%m/%d/%Y")+" الذي تم إنشاؤه بتاريخ \n%0a"
        msg += "بقيمة إجمالية"+str(self.amount_total) +" ريال ، فيما يلي تفاصيل طلبك.%0a\n"

        for line in self.order_line:
            msg += "الوصف :" + line.name + "\n%0a"
            msg += "الكمية :" + str(line.product_uom_qty) + "\n%0a"
            msg += "سعر الوحدة :" + str(line.price_unit) + "\n%0a"
            msg += "المجموع الفرعي :" + str(line.price_subtotal) + "\n%0a"
            msg += "-------------------------------\n%0a"
        msg += """مرفق لك مستند أمر البيع  والذي سيساعدك في الحصول على معلومات مفصلة
كما يمكنك الإطلاع  وإعتماد الطلب عن طريق الرابط التالي :
https://careone.odoo.com
    """


        return {'type': 'ir.actions.act_window',
                'name': _('Whatsapp Message'),
                'res_model': 'whatsapp.message.wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_user_id': self.partner_id.id,
                            'default_message':msg
                            },
                }


class AccountPayment(models.Model):
    _inherit = 'account.payment'


    def send_msg(self):
        msg = "مرحبًا  باسم البلاجي\n%0a"
        msg += "نشكرك على سدادك مبلغ "+str(self.amount)+"ريال على حسابك لدينا  ، بإيصال سداد رقم " +self.name +"\n%0a"
        # msg += "بقيمة إجمالية"+str(self.amount_total) +" ريال ، فيما يلي تفاصيل طلبك.%0a\n"
        msg += "فيما يلي تفاصيل الدفع الخاصة بك.\n%0a"
        msg += "نوع الدفع  :" + self.payment_type + "\n%0a"
        msg += "تاريخ الدفع  :" + str(self.payment_date) + "\n%0a"
        msg += "مذكرة  :" + str(self.communication) + "\n%0a"
        msg += """مرفق لك مستند السداد والذي سيساعدك في الحصول على معلومات مفصلة """


        return {'type': 'ir.actions.act_window',
                'name': _('Whatsapp Message'),
                'res_model': 'whatsapp.message.wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_user_id': self.partner_id.id,
                            'default_message':msg
                            },
                }
