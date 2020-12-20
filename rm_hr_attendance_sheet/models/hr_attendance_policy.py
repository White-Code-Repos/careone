# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2020-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################

from odoo import models, fields, api, tools, _
import babel
import time
from datetime import datetime, timedelta


class HrAttendancePolicy(models.Model):
    _name = 'hr.attendance.policy'
    _description = 'Attendance Sheet Policies'

    name = fields.Char(string="Name", required=True)
    overtime_rule_ids = fields.Many2many(comodel_name="hr.overtime.rule",
                                         relation="overtime_rule_policy_rel",
                                         column1="attendance_policy_col",
                                         column2="overtime_rule_col",
                                         string="Overtime Rules", )
    late_rule_id = fields.Many2one(comodel_name="hr.late.rule", required=True,
                                   string="Late In Rule")
    absence_rule_id = fields.Many2one(comodel_name="hr.absence.rule",
                                      string="Absence Rule", required=True)
    diff_rule_id = fields.Many2one(comodel_name="hr.diff.rule",
                                   string="Difference Time Rule", required=True)

    def get_overtime(self):
        self.ensure_one()
        res = {}
        if self:
            overtime_ids = self.overtime_rule_ids
            wd_ot_id = self.overtime_rule_ids.search(
                [('type', '=', 'workday'), ('id', 'in', overtime_ids.ids)],
                order='id', limit=1)
            we_ot_id = self.overtime_rule_ids.search(
                [('type', '=', 'weekend'), ('id', 'in', overtime_ids.ids)],
                order='id', limit=1)
            ph_ot_id = self.overtime_rule_ids.search(
                [('type', '=', 'ph'), ('id', 'in', overtime_ids.ids)],
                order='id', limit=1)
            if wd_ot_id:
                res['wd_rate'] = wd_ot_id.rate
                res['wd_after'] = wd_ot_id.active_after
            else:
                res['wd_rate'] = 1
                res['wd_after'] = 0
            if we_ot_id:
                res['we_rate'] = we_ot_id.rate
                res['we_after'] = we_ot_id.active_after
            else:
                res['we_rate'] = 1
                res['we_after'] = 0

            if ph_ot_id:
                res['ph_rate'] = ph_ot_id.rate
                res['ph_after'] = ph_ot_id.active_after
            else:
                res['ph_rate'] = 1
                res['ph_after'] = 0
        else:
            res['wd_rate'] = res['wd_rate'] = res['ph_rate'] = 1
            res['wd_after'] = res['we_after'] = res['ph_after'] = 0
        return res

    def get_late(self, period):
        self.ensure_one()
        res = period
        flag = False
        if self:
            if self.late_rule_id:
                time_ids = self.late_rule_id.line_ids.sorted(
                    key=lambda r: r.time, reverse=True)
                for line in time_ids:
                    if period >= line.time:
                        flag = True
                        if line.type == 'rate':
                            res = line.rate * period
                        elif line.type == 'fix':
                            res = line.amount

                        break

                if not flag:
                    res = 0
        return res

    def get_diff(self, period):
        self.ensure_one()
        res = period
        flag = False
        if self:
            if self.diff_rule_id:
                time_ids = self.diff_rule_id.line_ids.sorted(
                    key=lambda r: r.time, reverse=True)
                for line in time_ids:
                    if period >= line.time:
                        flag = True
                        if line.type == 'rate':
                            res = line.rate * period
                        elif line.type == 'fix':
                            res = line.amount

                        break

                if not flag:
                    res = 0
        return res

    def get_absence(self, period, cnt):
        res = period
        flag = False
        if self:
            if self.absence_rule_id:
                abs_ids = self.absence_rule_id.line_ids.sorted(
                    key=lambda r: r.counter, reverse=True)
                for ln in abs_ids:
                    if cnt >= int(ln.counter):
                        res = ln.rate * period
                        flag = True
                        break
                if not flag:
                    res = 0
        return res


class HrPolicy_overtimeLine(models.Model):
    _name = 'hr.policy.overtime.line'
    _description = 'Overtime Policy Lines'
    type = [
        ('weekend', 'Week End'),
        ('workday', 'Working Day'),
        ('ph', 'Public Holiday')

    ]
    overtime_rule_id = fields.Many2one(comodel_name='hr.overtime.rule',
                                       string='Name', required=True)
    type = fields.Selection(selection=type, string="Type", default='workday')
    active_after = fields.Float(string="Apply after",
                                help="After this time the overtime will be calculated")
    rate = fields.Float(string='Rate')
    attendance_policy_id = fields.Many2one(comodel_name='hr.attendance.policy')

    @api.onchange('overtime_rule_id')
    def onchange_ov_id(self):
        for line in self:
            line.type = line.overtime_rule_id.type
            line.active_after = line.overtime_rule_id.active_after
            line.rate = line.overtime_rule_id.rate


class HrOvertimeRule(models.Model):
    _name = 'hr.overtime.rule'
    _description = 'Over time Rules'
    type = [
        ('weekend', 'Week End'),
        ('workday', 'Working Day'),
        ('ph', 'Public Holiday')

    ]

    name = fields.Char(string="name")
    type = fields.Selection(selection=type, string="Type", default='workday')
    active_after = fields.Float(string="Apply after",
                                help="After this time the overtime will be calculated")
    rate = fields.Float(string='Rate')


class HrLateRule(models.Model):
    _name = 'hr.late.rule'
    _description = 'Late In Rules'

    name = fields.Char(string='name', required=True)
    line_ids = fields.One2many(comodel_name='hr.late.rule.line',
                               inverse_name='late_id', string='Late In Periods')


class HrLateRuleLine(models.Model):
    _name = 'hr.late.rule.line'
    _description = 'Late In Rule Lines'
    type = [
        ('fix', 'Fixed'),
        ('rate', 'Rate')
    ]

    late_id = fields.Many2one(comodel_name='hr.late.rule', string='Late Rule')
    type = fields.Selection(string="Type", selection=type, required=True, )
    rate = fields.Float(string='Rate')
    time = fields.Float('Time')
    amount = fields.Float('Amount')


class HrDiffRule(models.Model):
    _name = 'hr.diff.rule'
    _description = 'Diff Time Rule'

    name = fields.Char(string='name', required=True)
    line_ids = fields.One2many(comodel_name='hr.diff.rule.line',
                               inverse_name='diff_id',
                               string='Difference time Periods')


class HrDiffRuleLine(models.Model):
    _name = 'hr.diff.rule.line'
    _description = 'Diff Time Rule Line'
    type = [
        ('fix', 'Fixed'),
        ('rate', 'Rate')
    ]

    diff_id = fields.Many2one(comodel_name='hr.diff.rule', string='Diff Rule')
    type = fields.Selection(string="Type", selection=type, required=True, )
    rate = fields.Float(string='Rate')
    time = fields.Float('Time')
    amount = fields.Float('Amount')


class HrAbsenceRule(models.Model):
    _name = 'hr.absence.rule'
    _description = 'Absence Rules'

    name = fields.Char(string='name', required=True)
    line_ids = fields.One2many(comodel_name='hr.absence.rule.line',
                               inverse_name='absence_id',
                               string='Late In Periods')


class HrAbsenceRuleLine(models.Model):
    _name = 'hr.absence.rule.line'
    _description = 'Absence Rule Lines'
    times = [
        ('1', 'First Time'),
        ('2', 'Second Time'),
        ('3', 'Third Time'),
        ('4', 'Fourth Time'),
        ('5', 'Fifth Time'),

    ]
    absence_id = fields.Many2one(comodel_name='hr.absence.rule', string='name')
    rate = fields.Float(string='Rate', required=True)
    counter = fields.Selection(string="Times", selection=times, required=True, )
