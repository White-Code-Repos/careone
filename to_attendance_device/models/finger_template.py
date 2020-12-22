from odoo import models, fields, api


class FingerTemplate(models.Model):
    _name = 'finger.template'
    _description = 'Fingers Template'

    device_user_id = fields.Many2one('attendance.device.user', string='Device User',
                                     help='The device user who is owner of this finger template')
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  help='The employee who is owner of this finger template', ondelete='cascade',
                                  compute='_compute_employee_id', inverse='_set_employee_id', store=True)
    uid = fields.Integer(string='UId', help='The ID (technical field) of the user/employee in the device storage',
                         related='device_user_id.uid', store=True)
    device_id = fields.Many2one('attendance.device', string='Attendance Device',
                                related='device_user_id.device_id', store=True)
    fid = fields.Integer(string='Finger Id', help='The ID of this finger template in attendance device.')
    valid = fields.Integer(string='Valid')
    template = fields.Binary(string='Template')
    
    @api.depends('device_user_id', 'device_user_id.employee_id')
    def _compute_employee_id(self):
        for r in self:
            if r.device_user_id and r.device_user_id.employee_id:
                r.employee_id = r.device_user_id.employee_id.id
            else:
                self._cr.execute('''SELECT employee_id FROM finger_template WHERE id = %s''' % (r.id))
                res = self._cr.fetchone()
                r.employee_id = res[0] or False

    def _set_employee_id(self):
        pass
    
