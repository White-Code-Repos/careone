from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EmployeeUploadLineWizard(models.TransientModel):
    _name = 'employee.upload.line.wizard'
    _description = 'Employee Upload Details'

    wizard_id = fields.Many2one('employee.upload.wizard', required=True, ondelete='cascade')

    device_id = fields.Many2one('attendance.device', string='Device', required=True, ondelete='cascade')

    employee_id = fields.Many2one('hr.employee', string='Employees to upload', required=True, ondelete='cascade')

    @api.model
    def upload_employee(self):
        self.employee_id.action_load_to_attendance_device(self.device_id)


class EmployeeUploadWizard(models.TransientModel):
    _name = 'employee.upload.wizard'
    _description = 'Employee Upload Wizard'

    @api.model
    def _get_employee_ids(self):
        return self.env['hr.employee'].search([('id', 'in', self.env.context.get('active_ids', []))])

    device_ids = fields.Many2many('attendance.device', string='Devices', required=True)

    employee_ids = fields.Many2many('hr.employee', string='Employees to upload', default=_get_employee_ids, required=True)

    line_ids = fields.One2many('employee.upload.line.wizard', 'wizard_id', string='Upload Details')

    @api.model
    def _prepare_lines(self):
        line_ids = self.env['employee.upload.line.wizard']
        for employee in self.employee_ids:
            for device in self.device_ids:
                new_line = line_ids.new({
                    'wizard_id': self.id,
                    'employee_id':employee.id,
                    'device_id': device.id,
                    })
                line_ids += new_line
        return line_ids

    @api.onchange('employee_ids')
    def _onchange_employee_ids(self):
        if self.employee_ids:
            self.device_ids = self.employee_ids.mapped('unamapped_attendance_device_ids')
            self.line_ids = self._prepare_lines()

    @api.onchange('employee_ids', 'device_ids')
    def _onchange_devices_and_employees(self):
        self.line_ids = self._prepare_lines()

    @api.multi
    def action_employee_upload(self):
        self.ensure_one()
        for line in self.line_ids:
            if not line.employee_id.barcode:
                raise ValidationError(_('Employee %s has no Badge ID (employee barcode) set. Please set it on the employee profile.')
                                      % (line.employee_id.name))
            line.upload_employee()
        # we download and map all employees with users again
        self.device_ids.action_employee_map()

