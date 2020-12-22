from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    unamapped_attendance_device_ids = fields.Many2many('attendance.device', 'device_employee_rel', 'employee_id', 'device_id',
                                                       string='Unmapped Devices',
                                                       help='The devices that have not store this employee as an user yet.'
                                                       ' When you map employee with a user of a device, the device will disappear from this list.')
    created_from_attendance_device = fields.Boolean(string='Crear desde el dispositivo', readonly=True,
                                                    help='This field indicates that the employee was created from the data of an attendance device')
    finger_templates_ids = fields.One2many('finger.template', 'employee_id', string='Huella Digital', readonly=True)
    total_finger_template_records = fields.Integer(string='Huellas digitales', compute='_compute_total_finger_template_records')

    def _compute_total_finger_template_records(self):
        for r in self:
            r.total_finger_template_records = len(r.finger_templates_ids)

    @api.model_create_multi
    def create(self, vals_list):
        employees = super(HrEmployee, self).create(vals_list)
        attendance_device_ids = self.env['attendance.device'].sudo().with_context(active_test=False).search([])
        if attendance_device_ids:
            employees.write({'unamapped_attendance_device_ids': [(6, 0, attendance_device_ids.ids)]})
        return employees

    
    def write(self, vals):
        if 'barcode' in vals:
            DeviceUser = self.env['attendance.device.user'].sudo()
            for r in self:
                if DeviceUser.search([('employee_id', '=', r.id)], limit=1):
                    raise ValidationError(_("The employee '%s' is currently referred by an attendance device user."
                                            " Hence, you can not change the Badge ID of the employee") % (r.name,))
        return super(HrEmployee, self).write(vals)

    def _get_unaccent_name(self):
        return self.env['to.base'].no_accent_vietnamese(self.name)

    def _prepare_device_user_data(self, device):
        return {
            'uid': device.get_next_uid(),
            'name': self._get_unaccent_name() if device.unaccent_user_name else self.name,
            'password': '',
            'privilege': 0,
            'group_id': '0',
            'user_id': self.barcode,
            'employee_id': self.id,
            'device_id': device.id,
            }

    def create_device_user_if_not_exist(self, device):
        data = self._prepare_device_user_data(device)
        domain = [('device_id', '=', device.id)]
        if device.unique_uid:
            domain += [('uid', '=', int(data['uid']))]
        else:
            domain += [('user_id', '=', str(data['user_id']))]
        user = self.env['attendance.device.user'].search(domain, limit=1)
        if not user:
            user = self.env['attendance.device.user'].create(data)
        else:
            update_vals = {
                'employee_id': self.id,
                }
            if device.unique_uid:
                update_vals.update({
                    'user_id': self.barcode
                    })
            else:
                update_vals.update({
                    'uid': int(data['uid'])
                    })
            user.write(update_vals)
        return user

    def action_load_to_attendance_device(self, device):
        self.ensure_one()
        if not self.barcode:
            raise ValidationError(_("Employee '%s' has no Badge ID specified!"))
        device_user = self.create_device_user_if_not_exist(device)
        device_user.setUser()

    
    def action_view_finger_template(self):
        action = self.env.ref('to_attendance_device.action_finger_template')
        result = action.read()[0]

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        total_finger_template_records = self.total_finger_template_records
        if total_finger_template_records != 1:
            result['domain'] = "[('employee_id', 'in', " + str(self.ids) + ")]"
        elif total_finger_template_records == 1:
            res = self.env.ref('to_attendance_device.view_finger_template_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.finger_templates_ids.id
        return result
