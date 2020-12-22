from odoo import models, fields, api


class AttendanceState(models.Model):
    _name = 'attendance.state'
    _inherit = 'mail.thread'
    _description = 'Attendance State'

    name = fields.Char(string='Name', help='The name of the attendance state. E.g. Login, Logout, Overtime Start, etc', required=True, translate=True,
                       track_visibility='onchange')
    activity_id = fields.Many2one('attendance.activity', string='Activity', required=True,
                                  help='Attendance activity, e.g. Normal Working, Overtime, etc', track_visibility='onchange')
    code = fields.Integer(string='Code Number', help='An integer to express the state code', required=True, track_visibility='onchange')
    type = fields.Selection([('checkin', 'Check-in'),
                            ('checkout', 'Check-out')], string='Activity Type', required=True, track_visibility='onchange')

    _sql_constraints = [
        ('code_unique',
         'UNIQUE(code)',
         "The Code must be unique!"),
        ('name_activity_id_unique',
         'UNIQUE(name, activity_id)',
         "The state name must be unique within the same activity!"),
        ('name_activity_id_unique',
         'UNIQUE(type, activity_id)',
         "The Activity Type and Activity must be unique! Please recheck if you have previously defined an attendance status with the same Activity Type and Activity"),
    ]

    
    def name_get(self):
        """
        name_get that supports displaying tags with their code as prefix
        """
        result = []
        for r in self:
            result.append((r.id, '[' + r.activity_id.name + '] ' + r.name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """
        name search that supports searching by tag code
        """
        args = args or []
        domain = []
        if name:
            domain = ['|', ('activity_id.name', '=ilike', name + '%'), ('name', operator, name)]
        state = self.search(domain + args, limit=limit)
        return state.name_get()

