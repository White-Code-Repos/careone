from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class HrEmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'

    def _check_bank_account_format(self, num, val):
        val = val.strip()
        try:
            return val if any([type(int(i)) is int for i in val]) else False
        except:
            raise ValidationError(
                "'Bank Account %s' Accepts Numbers Only" % str(num))

    @api.model
    def create(self, vals):
        if 'bank_account_1' in vals:
            vals['bank_account_1'] = self._check_bank_account_format(
                1, vals['bank_account_1'])
        if 'bank_account_2' in vals:
            vals['bank_account_2'] = self._check_bank_account_format(
                2, vals['bank_account_2'])
        return super(HrEmployee, self).create(vals)

    def write(self, vals):
        if 'bank_account_1' in vals:
            vals['bank_account_1'] = self._check_bank_account_format(
                1, vals['bank_account_1'])
        if 'bank_account_2' in vals:
            vals['bank_account_2'] = self._check_bank_account_format(
                2, vals['bank_account_2'])
        return super(HrEmployee, self).write(vals)

    sector_id = fields.Many2one(
        comodel_name='hr.department', string='Sector', domain="[('department_type', '=', 'sector')]",
        context="{'default_department_type': 'sector'}")
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', domain="[('department_type', '=', 'department')]",
        context="{'default_department_type': 'department'}")
    section_id = fields.Many2one(
        comodel_name='hr.department', string='Section', domain="[('department_type', '=', 'section')]",
        context="{'default_department_type': 'section'}")
    blood_type = fields.Selection([
        ('O−', 'O−'),
        ('O+', 'O+'),
        ('A−', 'A−'),
        ('A+', 'A+'),
        ('B−', 'B−'),
        ('B+', 'B+'),
        ('AB−', 'AB−'),
        ('AB+', 'AB+'),
    ], string='Blood Type')
    bank_account_1 = fields.Char(string='Bank Account 1')
    bank_account_2 = fields.Char(string='Bank Account 2')
    join_date = fields.Date(string='Join Date')


class HrContract(models.Model):
    _inherit = 'hr.contract'

    employee_join_date = fields.Date(string='Employee Join Date')

    basic_salary = fields.Monetary(
        string='Basic Salary', digits=(16, 2), default=0, readonly=False)

    # Allowance
    nature_of_work = fields.Monetary(
        string='Nature of Work', digits=(16, 2), default=0, readonly=False)
    nature_of_work_operation = fields.Monetary(
        string='Nature of Work Operation', digits=(16, 2), default=0, readonly=False)
    nature_of_running = fields.Monetary(
        string='Nature of Running', digits=(16, 2), default=0, readonly=False)
    incentives = fields.Monetary(
        string='Incentives', digits=(16, 2), default=0, readonly=False)
    rep_allowance = fields.Monetary(
        string='Rep. Allowance', digits=(16, 2), default=0, readonly=False)
    special_exemption = fields.Monetary(
        string='Special Exemption', digits=(16, 2), default=0, readonly=False)
    car_allowances = fields.Monetary(
        string='Car Allowance', digits=(16, 2), default=0, readonly=False)

    # Deduction
    social_insurance = fields.Monetary(
        string='Social Insurance', digits=(16, 2), default=0, readonly=False)
    special_exemption_deduction = fields.Monetary(string='Special Exemption Deduction', digits=(16, 2), default=0,
                                                  readonly=False)
    mobile_deduction = fields.Monetary(
        string='Mobile', digits=(16, 2), default=0, readonly=False)
    meals_drinks = fields.Monetary(
        string='Meals / Drinks', digits=(16, 2), default=0, readonly=False)
    ins_salary_employee = fields.Monetary(
        string='Ins. Salary-Employee', digits=(16, 2), default=0, readonly=False)
    ins_salary_company = fields.Monetary(
        string='Ins. Salary-Company', digits=(16, 2), default=0, readonly=False)
    family_insurance = fields.Monetary(
        string='Family Insurance', digits=(16, 2), default=0, readonly=False)
    medical_deduction = fields.Monetary(
        string='Medical', digits=(16, 2), default=0, readonly=False)
    bofeh = fields.Monetary(
        string='Bofeh', digits=(16, 2), default=0, readonly=False)
    income_tax = fields.Monetary(
        string='Income Tax', digits=(16, 2), default=0, readonly=False)

    # ####################### Zienab Abdelnasser Code ######################

    work_days = fields.Integer('Working Days')
    work_hours = fields.Float('Working Hours')

    total_salary = fields.Float("Total Salary", compute="_get_total_salary")
    per_hour_coast = fields.Float('Coast Per Hours', compute="_get_total_salary")

    @api.depends('wage', 'incentives', 'nature_of_work', 'work_days', 'work_hours')
    def _get_total_salary(self):
        for i in self :
            i.total_salary = i.wage + i.incentives + i.nature_of_work

            i.per_hour_coast = i.total_salary / (i.work_days*i.work_hours) if i.total_salary >0 and (i.work_days*i.work_hours)>0 else 0
