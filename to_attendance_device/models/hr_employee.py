from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    unamapped_attendance_device_ids = fields.Many2many('attendance.device', 'device_employee_rel', 'employee_id', 'device_id',
                                                       string='Unmapped Devices',
                                                       help='The devices that have not store this employee as an user yet.'
                                                       ' When you map employee with a user of a device, the device will disappear from this list.')
    created_from_attendance_device = fields.Boolean(string='Created from Device', readonly=True,
                                                    help='This field indicates that the employee was created from the data of an attendance device')
    finger_templates_ids = fields.One2many('finger.template', 'employee_id', string='Finger Template', readonly=True)
    total_finger_template_records = fields.Integer(string='Finger Templates', compute='_compute_total_finger_template_records')
    
    def _compute_total_finger_template_records(self):
        for r in self:
            r.total_finger_template_records = len(r.finger_templates_ids)
    
    @api.model
    def create(self, vals):
        """
        This method create user in attendance device and mapping with employee odoo
        """
        res = super(HrEmployee, self).create(vals)
        AttendanceDeviceSudo = self.env['attendance.device'].sudo()
        attendance_device_ids = AttendanceDeviceSudo.search([])
        if attendance_device_ids:
            res.write({
                'unamapped_attendance_device_ids': [(6, 0, attendance_device_ids.ids)]
                })
        return res

    @api.multi
    def write(self, vals):
        if 'barcode' in vals:
            DeviceUser = self.env['attendance.device.user'].sudo()
            for r in self:
                if DeviceUser.search([('employee_id', '=', r.id)], limit=1):
                    raise ValidationError(_("The employee '%s' is currently referred by an attendance device user."
                                            " Hence, you can not change the Badge ID of the employee") % (r.name,))
        return super(HrEmployee, self).write(vals)
    
   
    @api.model
    def _get_unaccent_name(self):
        return self.env['to.base'].no_accent_vietnamese(self.name)        

    @api.model
    def action_load_to_attendance_device(self, device):
        if not self.barcode:
            raise ValidationError(_("Employee '%s' has no Badge ID specified!"))

        uid = 0
        name = self._get_unaccent_name() if device.unaccent_user_name else self.name
        privilege = 0
        password = ''
        group_id = '0'
        user_id = self.barcode
        if device:
            uid = device.getMaxUid() + 1
        device.setUser(uid, name, privilege, password, group_id, user_id)
        fingers = []
        for template in self.finger_templates_ids:
            fingers.append({'uid': template.uid, 'fid': template.fid, 'valid': template.valid, 'template': template.template})
        if fingers:
            device.setFingerTemplate(uid, name, privilege, password, group_id, user_id, fingers)
    
    @api.multi
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
    
