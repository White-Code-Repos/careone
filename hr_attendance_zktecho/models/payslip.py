# -*- coding: utf-8 -*-

from datetime import datetime,timedelta

from odoo import models, fields


class Payslip(models.Model):
    
    _inherit = 'hr.employee'
    
    no_attendance = fields.Boolean(string="Exempt from Attendance", help="This checkbox defines whether the employee's payslip is related to their attendance or not") 
    
    def get_work_days_data(self, from_datetime, to_datetime, calendar=None):
        if self.no_attendance:
            number_of_days = (to_datetime-from_datetime).days
            
            day_of_week = {'Monday':'0' ,'Tuesday':'1' ,'Wednesday':'2' ,'Thursday':'3' ,'Friday':'4' ,'Saturday':'5' ,'Sunday':'6' }
            days = 0
            delta = 0
            for i in range(number_of_days+1):
                day_id = (to_datetime+timedelta(delta)).strftime('%A')
                att_days = []
                for day in calendar.attendance_ids:
                    if day.dayofweek not in att_days and str(day.dayofweek) == day_of_week[day_id]:
                        att_days.append(str(day.dayofweek))
                if day_of_week[day_id] in att_days:
                    days += 1
                delta -= 1
            return {
            'days': days,
            'hours': days*calendar.hours_per_day,
            }
        
        data = self.get_attendance_data(from_datetime, to_datetime)
        return {
            'days': data['number_of_days'],
            'hours': data['number_of_hours'],
        }
    
    def get_attendance_data(self, from_datetime, to_datetime):
        total_wh = 0
        if to_datetime and from_datetime:
            from_date = from_datetime
            to_date = to_datetime
            attendences = {}
            employee = self
            sql = '''
            select att.worked_hours as worked_hours, att.check_in as checkin
            from hr_employee as emp inner join hr_attendance as att
                 on emp.id = att.employee_id
            where att.check_in >= %s and att.check_out <= %s and emp.id = %s
            order by checkin
            '''
            self.env.cr.execute(sql, (from_date, to_date, employee.id))
            attendences = self.env.cr.dictfetchall()
            wh = 0.0
            # sum up the attendances' durations
            dates_cal = []
            number_days = 0
            for att in attendences:
                dt = datetime.strptime(str(att['checkin']), '%Y-%m-%d %H:%M:%S')
                if dt.date() not in dates_cal:
                    dates_cal.append(dt.date())
                    number_days = number_days+1
                dur = att['worked_hours']
                if dur > 8:
                    wh += 8
                else:
                    wh += dur
            total_wh += wh
            
        return {'number_of_hours':total_wh , 'number_of_days':number_days}
    