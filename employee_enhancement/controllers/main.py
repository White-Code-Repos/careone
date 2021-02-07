from odoo import http , SUPERUSER_ID
from odoo.http import request

class Member(http.Controller):

    @http.route('/web/attend_employee', type='json', auth='public')
    def search_employee(self, **rec):
        user = request.env['res.users'].sudo().search([('login', '=', 'hr_user')], limit=1)
        hr_employee_obj = request.env['hr.employee'].with_user(user)
        if request.jsonrequest:
            if rec['id']:
                employee_ids = hr_employee_obj.search([('id', 'in', rec['id'])])
                for employee in employee_ids:
                    employee.attendance_manual({}, entered_pin=None)
                    args = {'success': True, 'message': 'Employee Updated'}
        return args
