# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _, tools
import requests
import json
import re


_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    whatsapp_msg_id = fields.Char('Whatsapp id')

    @api.model
    def create(self, vals):
        res = super(ProjectTask, self).create(vals)
        res.send_message_on_whatsapp()
        return res

    def cleanhtml(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

    def convert_to_html(self, message):
        for data in re.findall(r'\*.*?\*', message):
            message = message.replace(data, "<strong>" + data.strip('*') + "</strong>")
        return message

    def send_message_on_whatsapp(self):
        Param = self.env['res.config.settings'].sudo().get_values()
        res_partner_id = self.env['res.partner'].search([('id', '=', self.user_id.partner_id.id)])
        res_user_id = self.env['res.users'].search([('id', '=', self.env.user.id)])
        if res_partner_id.country_id.phone_code and res_partner_id.mobile:
            msg = ''
            if self.project_id.name:
                msg += "*Project:* "+self.project_id.name
            if self.name:
                msg += "\n*Task name:* "+self.name
            if self.date_deadline:
                msg+= "\n*Deadline:* "+str(self.date_deadline)
            if len(self.description) > 11:
                msg += "\n*Description:* "+self.cleanhtml(self.description)
            msg = "Hello " + res_partner_id.name + "," + "\nNew task assigned to you" + "\n" + msg

            # msg = "Hello " + res_partner_id.name+","+ "\nNew task assigned to you"+"\n"+"*Project:* "+self.project_id.name+"\n*Task name:* "+self.name+"\n*Deadline:* "+str(
            #     self.date_deadline)+"\n*Description:* "+self.cleanhtml(self.description)
            if res_user_id.has_group('pragmatic_odoo_whatsapp_integration.group_project_enable_signature'):
                user_signature = self.cleanhtml(res_user_id.signature)
                msg += "\n\n" + user_signature

            url = 'https://api.chat-api.com/instance' + Param.get('whatsapp_instance_id') + '/sendMessage?token=' + Param.get('whatsapp_token')
            headers = {
                "Content-Type": "application/json",
            }
            whatsapp_msg_number = res_partner_id.mobile
            whatsapp_msg_number_without_space = whatsapp_msg_number.replace(" ", "");
            whatsapp_msg_number_without_code = whatsapp_msg_number_without_space.replace('+' + str(res_partner_id.country_id.phone_code), "")
            tmp_dict = {
                # "phone": "+" + str(res_partner_id.country_id.phone_code) + "" + res_partner_id.mobile,
                "phone": "+" + str(res_partner_id.country_id.phone_code) + "" + whatsapp_msg_number_without_code,
                # "body": "Hello "+res_partner_id.name+","+ "\nNew task assigned to you"+"\n"+"*"+"Project:"+"*"+self.project_id.name
               "body": msg

            }
            response = requests.post(url, json.dumps(tmp_dict), headers=headers)

            if response.status_code == 201 or response.status_code == 200:
                _logger.info("\nSend Message successfully")
                response_dict = response.json()
                self.whatsapp_msg_id = response_dict.get('id')
                mail_message_obj = self.env['mail.message']
                comment = "fa fa-whatsapp"
                body_html = tools.append_content_to_html('<div class = "%s"></div>' % tools.ustr(comment), msg)
                body_msg = self.convert_to_html(body_html)

                if self.env['ir.config_parameter'].sudo().get_param('pragmatic_odoo_whatsapp_integration.group_project_display_chatter_message'):
                    mail_message_id = mail_message_obj.sudo().create({
                        'res_id': self.id,
                        'model': 'project.task',
                        'body': body_msg,
                    })

    def _assigned_task_done(self):
        project_task_ids = self.env['project.task'].search([('whatsapp_msg_id', '!=', None)])
        Param = self.env['res.config.settings'].sudo().get_values()


        for project_task_id in project_task_ids:
            res_partner_id = self.env['res.partner'].search([('id', '=', project_task_id.user_id.partner_id.id)])
            whatsapp_msg_number = res_partner_id.mobile
            whatsapp_msg_number_without_space = whatsapp_msg_number.replace(" ", "");

            url = 'https://api.chat-api.com/instance' +Param.get('whatsapp_instance_id') + '/messages?lastMessageNumber=1&last=true&chatId='+ \
                  str(res_partner_id.country_id.phone_code) +''+whatsapp_msg_number_without_space[-10:] +'@c.us&limit=100&token='+ Param.get('whatsapp_token')
            response = requests.get(url)

            if response.status_code == 201 or response.status_code == 200:
                _logger.info("\nGet project task successfully")
                response_dict = response.json()
                for messages in response_dict['messages']:
                    current_whatsapp_msg_id = project_task_id.whatsapp_msg_id.partition("true_")[2].partition("_")[0]
                    if not messages['quotedMsgId'] == None and current_whatsapp_msg_id in messages['quotedMsgId']:
                        if messages['body'] == 'done' or messages['body'] == 'Done':
                            # task_type_done_id = project_task_id.env['project.task.type'].search([('name', '=', 'Done')])
                            # project_task_id.env.ref("base.res_partner_2").id
                            task_type_id = self.env.ref('project.project_stage_2').read()
                            stage_id = project_task_id.write({'stage_id': self.env.ref('project.project_stage_2').id})
