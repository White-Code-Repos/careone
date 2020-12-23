# -*- coding: utf-8 -*-

import operator
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import except_orm


class move_attendance_wizard(models.Model):
    
    _name = "move.draft.attendance.wizard"
    
    date1 = fields.Datetime('From', required=True)
    date2 = fields.Datetime('To', required=True)
    employee_ids = fields.Many2many('hr.employee', 'move_att_employee_rel', 'employee_id', 'wiz_id')
    
    @api.one
    def move_confirm(self):
        hr_attendance_adjusment = self.env['hr.draft.attendance']
        hr_attendance = self.env['hr.attendance']
        hr_employee = self.env['hr.employee']
        employees = []
        if self.employee_ids:
            employees = self.employee_ids
        else:
            employees = hr_employee.search([])
            
        atten = {}
        all_attendances = []
        for employee in employees:
            attendance_ids = hr_attendance_adjusment.search([('employee_id','=',employee.id),
                                                              ('attendance_status','!=','sign_none'),
                                                              ('name','>=',self.date1),
                                                              ('name','<=',self.date2)], order='name asc')
            if attendance_ids:
                all_attendances += attendance_ids
                atten[employee.id] = {}
                for att in attendance_ids:
                    if att.date in atten[employee.id]:
                        atten[employee.id][att.date].append(att)
                    else:
                        atten[employee.id][att.date] = []
                        atten[employee.id][att.date].append(att)
                        
        if atten:
            for emp in atten:
                if emp:
                    employee_dic = atten[emp]
                    sorted_employee_dic = sorted(employee_dic.items(), key=operator.itemgetter(0))
                    last_action = False
                    for attendance_day in sorted_employee_dic:
                        day_dict = attendance_day[1]
                        for line in day_dict:
                            if line.attendance_status != 'sign_none':
                                if line.attendance_status == 'sign_in':
                                    check_in = line.name
                                    vals = {
                                            'employee_id': line.employee_id.id,
                                            'name': line.name,
                                            'day': line.date,
                                            'check_in':check_in,
                                            }
                                    hr_attendance = hr_attendance.search([('name','=', str(line.name)), ('employee_id','=',line.employee_id.id)])
                                    if not hr_attendance:
                                        if last_action != line.attendance_status:
                                            created_rec = hr_attendance.create(vals)
                                            _logger.info('Create Attendance '+ str(created_rec) +' for '+ str(line.employee_id.name)+' on ' + str(line.name))
                                            
                                elif line.attendance_status == 'sign_out':
                                    check_out = line.name
                                    hr_attendance_ids = hr_attendance.search([('employee_id','=',line.employee_id.id), ('day','=',line.date)])
                                    if hr_attendance_ids:
                                        for attend_id in hr_attendance_ids:
                                            if attend_id.day == line.date and attend_id.check_in and not attend_id.check_out:
                                                attend_id.write({'check_out':check_out})
                                                _logger.info('Updated '+str(attend_id.day)+ "'s Attendance, "+str(line.employee_id.name)+ ' Checked Out at: '+ str(check_out))
                                else:
                                    raise except_orm(_('Warning !'), _('Error ! Sign in (resp. Sign out) must follow Sign out (resp. Sign in) at '+str(line.name)+' for '+str(line.employee_id.name)))
                                last_action = line.attendance_status
                                
move_attendance_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
