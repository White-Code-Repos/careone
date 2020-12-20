from odoo import models, fields, api, tools, _

class HrPayslipInputType(models.Model):
	_inherit = 'hr.payslip.input.type'

	up_to_3h = fields.Boolean('3H')
	after_to_3h = fields.Boolean('After 3H')
	weekend = fields.Boolean('Weekend')

