# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2020-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################


from odoo import models, fields, tools, api, exceptions, _


class HrPublicHoliday(models.Model):
    _name = "hr.public.holiday"
    _inherit = ['mail.thread']
    _description = "hr.public.holiday"
    HOLIDAY_TYPE = [
        ('emp', 'name'),
        ('dep', 'Department'),
        ('tag', 'Tags')

    ]
    type_select = fields.Selection(HOLIDAY_TYPE, "By", default='emp')
    emp_ids = fields.Many2many(comodel_name="hr.employee",
                               relation="employee_ph_rel",
                               column1="employee_ph_col2",
                               column2="attendance_ph_col2",
                               string="Employees", )

    dep_ids = fields.Many2many(comodel_name="hr.department",
                               relation="department_att_ph_rel1",
                               column1="ph_department_col2",
                               column2="att_ph_col3", string="Departments", )
    cat_ids = fields.Many2many(comodel_name="hr.employee.category",
                               relation="category__phrel",
                               column1="cat_col2", column2="ph_col2",
                               string="Tags", )

    name = fields.Char(string="Description",required=True)
    date_from = fields.Date(string="From",required=True)
    date_to = fields.Date(string="To",required=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Not Active')], default='inactive',
        track_visibility='onchange',
        string='Status', required=True, index=True, )
    note = fields.Text("Notes")

    @api.onchange("dep_ids", "cat_ids")
    def get_employee_ids(self):
        emp_ids = []
        if self.type_select == 'dep':
            self.emp_ids = self.env['hr.employee'].search(
                [('department_id.id', 'in', self.dep_ids.ids)])
        elif self.type_select == 'tag':
            for employee in self.env['hr.employee'].search([]):
                list1 = self.cat_ids.ids
                list2 = employee.category_ids.ids
                match = any(map(lambda v: v in list1, list2))
                if match:
                    emp_ids.append(employee.id)
            self.emp_ids = self.env['hr.employee'].search(
                [('id', 'in', emp_ids)])
