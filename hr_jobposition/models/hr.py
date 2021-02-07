# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrJobGrade(models.Model):
    _name = 'hr.job.grade'
    _description = "Job Grade"

    name = fields.Text(string='Name')


class HrJobLevel(models.Model):
    _name = 'hr.job.level'
    _description = "Job Level"

    name = fields.Text(string='Name')


class HrJob(models.Model):
    _inherit = 'hr.job'

    code = fields.Char('Job Code')
    job_grade_id = fields.Many2one('hr.job.grade', string='Job Grade')
    job_level_id = fields.Many2one('hr.job.level', string='Job Level')

    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'Job code must be unique per company !')
    ]


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    department_type = fields.Selection([
        ('sector', 'Sector'),
        ('department', 'Department'),
        ('section', 'Section')], string='Type')


class HrEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'

    sector = fields.Char('Sector')
    department = fields.Char('Department')
    section = fields.Char('Section')
    
    @api.onchange('department_id')
    def onchange_department(self):
        if self.department_id:
            if self.department_id.parent_id and self.department_id.parent_id.parent_id:
                self.sector = self.department_id.parent_id and self.department_id.parent_id.parent_id and self.department_id.parent_id.parent_id.name or ''
                self.department = self.department_id.parent_id and self.department_id.parent_id.name or ''
                self.section = self.department_id.name
            elif self.department_id.parent_id and not self.department_id.parent_id.parent_id:
                self.sector = self.department_id.parent_id and self.department_id.parent_id.name or ''
                self.department = self.department_id.name
                self.section = ''
            elif not self.department_id.parent_id:
                self.sector = self.department_id.name
                self.department = ''
                self.section = ''
            else:
                self.sector = ''
                self.department = ''
                self.section = ''
