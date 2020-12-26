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


import pytz
from operator import itemgetter
from odoo import api, fields, models, _


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def att_get_work_intervals(self, day_start, day_end,tz):
        day_start = day_start.replace(tzinfo=tz)
        day_end = day_end.replace(tzinfo=tz)
        attendance_intervals = self._attendance_intervals(day_start, day_end)
        working_intervals = []
        for interval in attendance_intervals:
            working_interval_tz = (
                interval[0].astimezone(pytz.UTC).replace(
                    tzinfo=None),
                interval[1].astimezone(pytz.UTC).replace(
                    tzinfo=None))
            working_intervals.append(working_interval_tz)
        clean_work_intervals = self.att_interval_clean(working_intervals)

        return clean_work_intervals

    def att_interval_clean(self, intervals):
        intervals = sorted(intervals,
                           key=itemgetter(0))  # sort on first datetime
        cleaned = []
        working_interval = None
        while intervals:
            current_interval = intervals.pop(0)
            if not working_interval:  # init
                working_interval = [current_interval[0], current_interval[1]]
            elif working_interval[1] < current_interval[
                0]:
                cleaned.append(tuple(working_interval))
                working_interval = [current_interval[0], current_interval[1]]
            elif working_interval[1] < current_interval[
                1]:
                working_interval[1] = current_interval[1]
        if working_interval:
            cleaned.append(tuple(working_interval))
        return cleaned

    def att_interval_without_leaves(self, interval, leave_intervals):
        if not interval:
            return interval
        if leave_intervals is None:
            leave_intervals = []
        intervals = []
        leave_intervals = self.att_interval_clean(leave_intervals)
        current_interval = [interval[0], interval[1]]
        for leave in leave_intervals:
            if leave[1] <= current_interval[0]:
                continue
            if leave[0] >= current_interval[1]:
                break
            if current_interval[0] < leave[0] < current_interval[1]:
                current_interval[1] = leave[0]
                intervals.append((current_interval[0], current_interval[1]))
                current_interval = [leave[1], interval[1]]
            if current_interval[0] <= leave[1]:
                current_interval[0] = leave[1]
        if current_interval and current_interval[0] < interval[
            1]:  # remove intervals moved outside base interval due to leaves
            intervals.append((current_interval[0], current_interval[1]))
        return intervals
