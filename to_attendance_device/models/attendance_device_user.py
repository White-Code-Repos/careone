from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AttendanceDeviceUser(models.Model):
    _name = 'attendance.device.user'
    _inherit = 'mail.thread'
    _description = 'Attendance Device User'

    name = fields.Char(string='Name', help='The name of the employee stored in the device', required=True, track_visibility='onchange')
    device_id = fields.Many2one('attendance.device', string='Attendance Device', required=True, ondelete='cascade', track_visibility='onchange')
    uid = fields.Integer(string='UID', help='The ID (technical field) of the user/employee in the device storage', readonly=True, track_visibility='onchange')
    user_id = fields.Char(string='ID Number', size=8, help='The ID Number of the user/employee in the device storage', required=True, track_visibility='onchange')
    password = fields.Char(string='Password', track_visibility='onchange')
    group_id = fields.Integer(string='Group', default=0, track_visibility='onchange')
    privilege = fields.Integer(string='Privilege', track_visibility='onchange')
    del_user = fields.Boolean(string='Delete User', default=True,
                              track_visibility='onchange',
                              help='If checked, the user on the device will be deleted upon deleting this record in Odoo')
    employee_id = fields.Many2one('hr.employee', string='Employee', help='The Employee who is corresponding to this device user',
                                  ondelete='set null', track_visibility='onchange')
    attendance_ids = fields.One2many('user.attendance', 'user_id', string='Attendance Data', readonly=True)
    attendance_id = fields.Many2one('user.attendance', string='Current Attendance', store=True,
                                    compute='_compute_current_attendance',
                                    help='The technical field to store current attendance recorded of the user.')
    active = fields.Boolean(string='Active', compute='_get_active', track_visibility='onchange', store=True)
    finger_templates_ids = fields.One2many('finger.template', 'device_user_id', string='Finger Template', readonly=True)
    total_finger_template_records = fields.Integer(string='Finger Templates', compute='_compute_total_finger_template_records')

    _sql_constraints = [
#         ('user_id_device_id_unique',
#          'UNIQUE(user_id, device_id)',
#          "The ID Number must be unique per Device"),
        ('employee_id_device_id_unique',
         'UNIQUE(employee_id, device_id)',
         "The Employee must be unique per Device"),
    ]
    
    def _compute_total_finger_template_records(self):
        for r in self:
            r.total_finger_template_records = len(r.finger_templates_ids)

    @api.depends('device_id', 'device_id.active', 'employee_id', 'employee_id.active')
    def _get_active(self):
        for r in self:
            if r.employee_id:
                r.active = r.device_id.active and r.employee_id.active
            else:
                r.active = r.device_id.active

    @api.depends('attendance_ids')
    def _compute_current_attendance(self):
        for r in self:
            r.attendance_id = self.env['user.attendance'].search([('user_id', '=', r.id)], limit=1, order='timestamp DESC') or False

    @api.constrains('user_id', 'device_id')
    def constrains_user_id_device_id(self):
        for r in self:
            if r.device_id and r.device_id.unique_uid:
                duplicate = self.search([('id', '!=', r.id), ('device_id', '=', r.device_id.id), ('user_id', '=', r.user_id)], limit=1)
                if duplicate:
                    raise UserError(_('The ID Number must be unique per Device!'
                                      ' A new user was being created/updated whose user_id and'
                                      ' device_id is the same as the existing one\'s (name: %s; device: %s; user_id: %s)')
                                      % (duplicate.name, duplicate.device_id.display_name, duplicate.user_id))

    @api.multi
    def unlink(self):
        force_delete_from_both = self.env.context.get('force_delete_from_both', False)
        for r in self:
            if r.del_user:
                try:
                    r.device_id.delUser(r.uid, r.user_id)
                except Exception as e:
                    if force_delete_from_both:
                        pass
                    raise UserError(str(e))
        return super(AttendanceDeviceUser, self).unlink()

    @api.onchange('user_id')
    def onchange_user_id(self):
        if self.user_id:
            self.user_id = self.env['to.base'].no_accent_vietnamese(self.user_id.replace(' ', ''))

    @api.model
    def setUser(self):
        new_user = self.device_id.setUser(
            self.uid,
            self.name,
            self.privilege,
            self.password,
            self.group_id,
            self.user_id)
        return new_user

    @api.model
    def create(self, vals):
        res = super(AttendanceDeviceUser, self).create(vals)
        if self.env.context.get('should_set_user', False):
            res.setUser()
        return res

#     def _should_set_user(self, vals):
#         user_fields = ['name', 'uid', 'user_id', 'password', 'group_id', 'privilege']
#         for key in vals.keys():
#             if str(key) in user_fields:
#                 return True
#         return False

    @api.model
    def _prepare_employee_data(self, barcode):
        return {
            'name': self.name + ' [' + _('Created from Device') + ']',
            'created_from_attendance_device': True,
            'barcode': barcode,
            }

    @api.model
    def create_employee(self):
        """
        This method will try create a new employee from the device user data.
        """
        Employee = self.env['hr.employee'].sudo()
        new_employee = False
        try:
            new_employee = Employee.create(self._prepare_employee_data(self.user_id))
        except Exception as e:
            _logger.info(e)
            new_employee = Employee.create(self._prepare_employee_data(Employee._default_random_barcode()))
        if new_employee:
            self.write({'employee_id': new_employee.id, })
        return new_employee
    
    @api.model
    def smart_find_employee(self):
        employee_id = False
        if self.employee_id:
            employee_id = self.employee_id
        else:
            for employee in self.device_id.unmapped_employee_ids:
                if self.user_id == employee.barcode \
                or self.name == employee.name \
                or self.name.lower() == employee._get_unaccent_name().lower() \
                or self.name == employee.name[:len(self.name)]:
                    employee_id = employee
        return employee_id       
    
    @api.multi
    def action_view_finger_template(self):
        action = self.env.ref('to_attendance_device.action_finger_template')
        result = action.read()[0]

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        total_finger_template_records = self.total_finger_template_records
        if total_finger_template_records != 1:
            result['domain'] = "[('device_user_id', 'in', " + str(self.ids) + ")]"
        elif total_finger_template_records == 1:
            res = self.env.ref('to_attendance_device.view_finger_template_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.finger_templates_ids.id
        return result
    
    @api.multi
    def write(self, vals):
        res = super(AttendanceDeviceUser, self).write(vals)
        if 'name' in vals:
            for r in self:
                r.setUser()
        return res
