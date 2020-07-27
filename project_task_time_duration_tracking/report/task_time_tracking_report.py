# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools


class TaskTimeTrackingReport(models.Model):
    _name = "task.time.tracking.report"
    _description = "Task Time Tracking Report"
    _auto = False

    start_date = fields.Datetime(string='Start Date', readonly=True)
    stop_date = fields.Datetime(string='Stop Date', readonly=True)
    duration = fields.Float(string='Duration', readonly=True)
    stage_id = fields.Many2one('project.task.type', string='Stage',
                               readonly=True)
    task_id = fields.Many2one('project.task', string='Task', readonly=True)
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    project_id = fields.Many2one('project.project', string='Project',
                                 readonly=True)
    quality_check = fields.Boolean('Quality Check', readonly=True)

    @api.model
    def _query(self):
        return '''
            SELECT 
                ttt.id,
                ttt.user_id as user_id,
                ttt.task_id as task_id,
                ttt.project_id as project_id,
                ttt.duration as duration,
                ttt.stage_id as stage_id,
                ttt.start_date as start_date,
                ttt.stop_date as stop_date,
                ttt.quality_check as quality_check,
                pt.name as task,
                ptt.name as stage, 
                rs.login as user, 
                pp.name as project
            FROM 
                task_time_track AS ttt, 
                res_users AS rs, 
                project_task AS pt, 
                project_project AS pp, 
                project_task_type AS ptt
            WHERE 
                ttt.stage_id = ptt.id AND
                ttt.task_id = pt.id AND
                ttt.user_id = rs.id AND
                ttt.project_id = pp.id
            GROUP BY
                ttt.id,
                ttt.user_id,
                ttt.stage_id,
                ttt.task_id,
                ttt.project_id,
                ttt.duration,
                pt.name,
                ptt.name,
                rs.login,
                pp.name
        '''

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (%s)''' % (
            self._table, self._query()
        ))
