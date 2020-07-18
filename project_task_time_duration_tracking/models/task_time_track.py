from odoo import fields, models, api
from datetime import datetime

class TaskTimeTrack(models.Model):
    _name = 'task.time.track'
    _description = 'Description'

    start_date = fields.Datetime(string='Start Date')
    stop_date = fields.Datetime(string='Stop Date')
    duration = fields.Float(string='Duration')
    stage_id = fields.Many2one('project.task.type', string='Stage')
    task_id = fields.Many2one('project.task', string='Task')
    user_id = fields.Many2one('res.users', string='User')
    project_id = fields.Many2one('project.project', string='Project')
    quality_check = fields.Boolean('Quality Check')

    def get_duration(self, start_date, stop_date):
        return (stop_date - start_date).seconds / 3600

    @api.model
    def create(self, values):
        if values.get('start_date') and values.get('stop_date'):
            start_date = datetime.strptime(values.get('start_date'), '%Y-%m-%d %H:%M:%S')
            stop_date = datetime.strptime(values.get('stop_date'), '%Y-%m-%d %H:%M:%S')
            duration = self.get_duration(start_date, stop_date)
            values.update({'duration': duration})
        return super(TaskTimeTrack, self).create(values)

    def write(self, values):
        for record in self:
            start_date = values.get('start_date', record.start_date)
            stop_date = values.get('stop_date', record.stop_date)

            if start_date and stop_date:
                if type(start_date) == str:
                    start_date = datetime.strptime(start_date,
                                                   '%Y-%m-%d %H:%M:%S')
                if type(stop_date) == str:
                    stop_date = datetime.strptime(stop_date,
                                                  '%Y-%m-%d %H:%M:%S')
                duration = self.get_duration(start_date, stop_date)
                values.update({'duration': duration})
        return super(TaskTimeTrack, self).write(values)

    def _calculate_duration(self):
        for record in self:
            if record.start_date and record.stop_date:
                duration = self.get_duration(record.start_date, record.stop_date)
                record.duration = duration
            else:
                record.duration = 0.0
