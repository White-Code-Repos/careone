# -*- coding: utf-8 -*-

import math
from pytz import timezone,all_timezones
from datetime import datetime,timedelta

from odoo import api, fields, models


class generate_missing_attendance(models.Model):
    
    _name = "generate.missing.draft.attendance"
    
    time_zone = fields.Selection('_tz_get', string='Timezone', required=True, default=lambda self: self.env.user.tz or 'UTC')
    
    @api.model
    def _tz_get(self):
        return [(x, x) for x in all_timezones]
    
    @api.one
    def get_local_utc(self,offset):
        hours = offset[1:3]
        minutes = offset[3:5]
        return [int(hours),int(minutes)]
    
    @api.one
    def generate_attendance(self):
        hr_attendance = self.env['hr.draft.attendance']
        atten = {}
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            attendance_ids = hr_attendance.search([('employee_id','=',employee.id)], order='name asc')
            if attendance_ids:
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
                    for attendance_day in atten[emp]:
                        day_dict = employee_dic[attendance_day]
                        is_shifted_employee = day_dict[0].employee_id.is_shift
                        if len(day_dict) == 1 and not is_shifted_employee:
                            date = day_dict[0].name
                            if day_dict[0].attendance_status == 'sign_in':
                                action = 'sign_out'
                                if date.strftime('%A') == 'Friday':
                                    hour = self.off_get_day_worktime(day_dict[0].employee_id, 
                                                      date.strftime('%A'), day_dict[0], 'out')[0]
                                else:
                                    hour = self.get_day_worktime(day_dict[0].employee_id, 
                                                      date.strftime('%A'), day_dict[0].date, 'out')[0]
                            else:
                                action = 'sign_in'
                                if date.strftime('%A') == 'Friday':
                                    hour = self.off_get_day_worktime(day_dict[0].employee_id, 
                                                      date.strftime('%A'), day_dict[0], 'in')[0]
                                else:
                                    hour = self.get_day_worktime(day_dict[0].employee_id, 
                                                      date.strftime('%A'), day_dict[0].date, 'in')[0]
                            if hour:
                                new_date_time = str(day_dict[0].date)+' '+hour
                                new_date = datetime.strptime(new_date_time, '%Y-%m-%d %H:%M:%S')
                                self.create_inverse_attendance(day_dict[0].employee_id, action, new_date)
                            # add inverse action of this one
                        elif len(day_dict) >= 2 and not is_shifted_employee:
                            f_action = day_dict[0].attendance_status
                            # check what missing in or out and create inverse
                            l_action = day_dict[len(day_dict)-1].attendance_status
                            if f_action == l_action:
                                if f_action == 'sign_in':
                                    last_date = day_dict[0]
                                else:
                                    last_date = day_dict[len(day_dict)-1]
                                
                                fl_date = datetime.strptime(last_date.name, '%Y-%m-%d %H:%M:%S')
                                    
                                if f_action == 'sign_in':
                                    action = 'sign_out'
                                    if fl_date.strftime('%A') == 'Friday':
                                        hour = self.off_get_day_worktime(last_date.employee_id, 
                                                          fl_date.strftime('%A'), last_date, 'out')[0]
                                    else:
                                        hour = self.get_day_worktime(last_date.employee_id, 
                                                          fl_date.strftime('%A'), last_date.date, 'out')[0]
                                else:
                                    action = 'sign_in'
                                    if fl_date.strftime('%A') == 'Friday':
                                        hour = self.off_get_day_worktime(last_date.employee_id, 
                                                          fl_date.strftime('%A'), last_date, 'in')[0]
                                    else:
                                        hour = self.get_day_worktime(last_date.employee_id, 
                                                          fl_date.strftime('%A'), last_date.date, 'in')[0]
                                
                                
                                if hour:
                                    new_date_time = str(last_date.date)+' '+hour
                                    new_date = datetime.strptime(new_date_time, '%Y-%m-%d %H:%M:%S')
                                    self.create_inverse_attendance(last_date.employee_id, action, new_date)
                        
                        # for shifted employees
                        if is_shifted_employee :
                            if len(day_dict) == 1: 
                                hour_shifted = self.get_shift_one(day_dict[0].employee_id, day_dict[0].name, day_dict[0].attendance_status)[0]
                                action = 'sign_in'
                                if day_dict[0].attendance_status == 'sign_in':
                                    action= 'sign_out'
                                if hour_shifted:
                                    new_date_time = str(day_dict[0].date)+' '+hour_shifted
                                    new_date = datetime.strptime(new_date_time, '%Y-%m-%d %H:%M:%S')
                                    self.create_inverse_attendance(day_dict[0].employee_id, action, new_date)
                            elif len(day_dict) == 2: 
                                actions = []
                                for l in day_dict:
                                    actions.append(str(l.attendance_status))
                                
                                if actions == ['sign_in', 'sign_out']:
                                    same_shift = self.is_same_shift(day_dict)[0]
                                else:
                                    same_shift = False
                                
                                if not same_shift:
                                    for d in day_dict:
                                        action = 'sign_in'
                                        if d.attendance_status == 'sign_in':
                                            action= 'sign_out'
                                        hour_shifted = self.get_shift_one(d.employee_id, d.name, d.attendance_status)[0]
                                        if hour_shifted:
                                            new_date_time = str(d.date)+' '+hour_shifted
                                            new_date = datetime.strptime(new_date_time, '%Y-%m-%d %H:%M:%S')
                                            self.create_inverse_attendance(d.employee_id, action, new_date)
                                    
                            elif len(day_dict) == 3: 
                                actions = []
                                for l in day_dict:
                                    actions.append(str(l.attendance_status))
                                if (actions == ['sign_in', 'sign_out', 'sign_out']) or (actions == ['sign_in', 'sign_out', 'sign_in']):
                                    action = 'sign_in'
                                    if day_dict[2].attendance_status == 'sign_in':
                                        action= 'sign_out'
                                    hour_shifted = self.get_shift_one(day_dict[2].employee_id, day_dict[2].name, day_dict[2].attendance_status)[0]
                                elif (actions == ['sign_in', 'sign_in', 'sign_out']) or (actions == ['sign_out','sign_in', 'sign_out']):
                                    action = 'sign_in'
                                    if day_dict[0].attendance_status == 'sign_in':
                                        action= 'sign_out'
                                    hour_shifted = self.get_shift_one(day_dict[0].employee_id, day_dict[0].name, day_dict[0].attendance_status)[0]
                                    
                                if hour_shifted:
                                    new_date_time = str(day_dict[0].date)+' '+hour_shifted
                                    new_date = datetime.strptime(new_date_time, '%Y-%m-%d %H:%M:%S')
                                    self.create_inverse_attendance(day_dict[0].employee_id, action, new_date)
        
    @api.one
    def create_inverse_attendance(self ,employee ,action ,date):   
        hr_attendance = self.env['hr.draft.attendance']
        vals = {
              'employee_id': employee.id,
              'attendance_status': action,
              'name': date,
              'date': date.date(),
              'is_missing': True,
              'day_name': str(date.strftime('%A')),
                }
        hr_attendance.create(vals)
    
    @api.one
    def get_day_worktime(self, employee, day_id ,date, action):
        day_of_week = {'Monday':0 ,'Tuesday':1 ,'Wednesday':2 ,'Thursday':3 ,'Friday':4 ,'Saturday':5 ,'Sunday':6 }
        contract = employee.contract_id
        time_hour = False
        if contract:
            if contract.resource_calendar_id:
                for day in contract.resource_calendar_id.attendance_ids:
                    if int(day.dayofweek) == day_of_week[day_id]:
                        if action == 'in':
                            time_hour = day.hour_from
                        else:
                            time_hour = day.hour_to
            if time_hour:
                #
                dateTime = datetime.strptime(date+' 00:00:00','%Y-%m-%d %H:%M:%S')
                my_local_timezone = timezone(self.time_zone)
                local_date = my_local_timezone.localize(dateTime)
                utcOffset = local_date.strftime('%z')
                hours , minutes = self.get_local_utc(utcOffset)[0]
                # -2 for timing issue 
                real_time = str(int(time_hour)-hours)+ ':' + str(int(math.ceil((time_hour-int(time_hour))*60)))+':00'    
                return real_time
            
        return False
    
    @api.one
    def off_get_day_worktime(self, employee, day_id ,date, action):
        day_of_week = {'Monday':0 ,'Tuesday':1 ,'Wednesday':2 ,'Thursday':3 ,'Friday':4 ,'Saturday':5 ,'Sunday':6 }
        contract = employee.contract_id
        time_hour = False
        if contract:
            if contract.resource_calendar_id:
                for day in contract.resource_calendar_id.attendance_ids:
                    if int(day.dayofweek) == day_of_week[day_id]:
                        if action == 'in':
                            time_hour = day.hour_from
                        else:
                            time_hour = day.hour_to
            if time_hour:
                #
                dateTime = datetime.strptime(date.name,'%Y-%m-%d %H:%M:%S')
                my_local_timezone = timezone(self.time_zone)
                local_date = my_local_timezone.localize(dateTime)
                utcOffset = local_date.strftime('%z')
                hours , minutes = self.get_local_utc(utcOffset)[0]
                # -2 for timing issue 
                real_time = str(int(time_hour)-hours)+ ':' + str(int(math.ceil((time_hour-int(time_hour))*60)))+':00'    
                return real_time
            
        return False
    
    @api.one
    def shifted_employee(self, employee ,date):
        date_time = datetime.strptime(date+' 00:00:00', '%Y-%m-%d %H:%M:%S')
        day_of_week = {'Monday':0 ,'Tuesday':1 ,'Wednesday':2 ,'Thursday':3 ,'Friday':4 ,'Saturday':5 ,'Sunday':6 }
        payslip_obj = self.env['hr.payslip']
        hr_contract = self.env['hr.contract']
        contract_id = payslip_obj.get_contract(employee, date, date)
        att_count = 0
        if contract_id:
            contract = hr_contract.browse(contract_id)[0]
            if contract.resource_calendar_id:
                for day in contract.resource_calendar_id.attendance_ids:
                    if int(day.dayofweek) == day_of_week[date_time.strftime('%A')]:
                        att_count = att_count+1
        return att_count
    
    @api.one
    def get_shift_one(self, employee ,date, action):
        date_time = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        day_of_week = {'Monday':0 ,'Tuesday':1 ,'Wednesday':2 ,'Thursday':3 ,'Friday':4 ,'Saturday':5 ,'Sunday':6 }
        payslip_obj = self.env['hr.payslip']
        hr_contract = self.env['hr.contract']
        contract_id = payslip_obj.get_contract(employee, str(date_time.date()), str(date_time.date()))
        shifted_time = False
        att_line_target = False 
        if contract_id:
            contract = hr_contract.browse(contract_id)[0]
            if contract.working_hours:
                for day in contract.working_hours.attendance_ids:
                    if int(day.dayofweek) == day_of_week[date_time.strftime('%A')]:
                        time_2 = str((date_time+timedelta(hours=3)).time())
                        time_float = self.convert_to_float(time_2)[0]
                        if action == 'sign_in':
                            time_hour = day.hour_from
                        else:
                            time_hour = day.hour_to
                        
                        if shifted_time != False:
                            if shifted_time > abs(time_float - time_hour):
                                shifted_time = abs(time_float - time_hour)
                                att_line_target = day
                        else:
                            if abs(time_float - time_hour) > 0:
                                shifted_time = abs(time_float - time_hour)
                            else:
                                shifted_time = 0.0001
                            att_line_target = day
        
        if att_line_target:
            if action == 'sign_in':
                time_hour = att_line_target.hour_to
            else:
                time_hour = att_line_target.hour_from
            if time_hour:
                real_time = str(int(time_hour)-3)+ ':' + str(int(math.ceil((time_hour-int(time_hour))*60)))+':00'    
                return real_time
            
        return False
    
    @api.one
    def convert_to_float(self, time_att):
        h_m_s = time_att.split(":")
        hours = int(h_m_s[0])
        minutes_1 = float(h_m_s[1])/60.0
        minutes = ("%.2f" % minutes_1)
        return hours+float(minutes)
    
    @api.one  
    def is_same_shift(self, day_dict):
        f_attendance = datetime.strptime(day_dict[0].name, '%Y-%m-%d %H:%M:%S')
        l_attendance = datetime.strptime(day_dict[1].name, '%Y-%m-%d %H:%M:%S')
        diff_seconds = (l_attendance - f_attendance).seconds
        diff_float_time = diff_seconds / 3600 
        if diff_float_time >= 10:
            return False
        return True
            
generate_missing_attendance()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
