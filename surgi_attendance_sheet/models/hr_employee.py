# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) 2020.
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#    website': https://www.linkedin.com/in/ramadan-khalil-a7088164
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import pytz


class hrEmployee(models.Model):
    _inherit = "hr.employee"

    attendance_approval = fields.Boolean('Require Attendance Approval')

    employee_attendance_penalty = fields.Integer(compute='_compute_hr_employee_attendance_penalty', string='Penalty Count')
    

    def _compute_hr_employee_attendance_penalty(self):
        employee_attendance_penalty_obj = self.env['hr.attendance.penalty']
        for rec in self:
            rec.employee_attendance_penalty = 0
            count = employee_attendance_penalty_obj.search_count([('employee_id', '=', rec.id) ])
            if count:
                rec.employee_attendance_penalty = count

    def get_employee_shifts(self, day_start, day_end, tz):
        self.ensure_one()
        plan_slot_obj = self.env['planning.slot']
        day_start_native = day_start.replace(tzinfo=tz).astimezone(
            pytz.utc).replace(tzinfo=None)
        day_end_native = day_end.replace(tzinfo=tz).astimezone(
            pytz.utc).replace(tzinfo=None)
        print(">>>>>>>>>>>>>>>>>>>>day_start_native ",day_start_native,day_end_native)
        slot_ids = plan_slot_obj.search(
            [('employee_id','=',self.id),
             ('start_datetime', '>=', day_start_native),
             ('start_datetime', '<=', day_end_native)])
        print(">>>>>>>>>>>>>>>>>>>>slot_ids ",slot_ids.start_datetime,slot_ids.start_datetime)
        # 2022-01-31 22:00:00 2022-01-31 22:00:00
        working_intervals = []
        for slot in slot_ids:
            working_intervals.append((slot.start_datetime, slot.end_datetime))
        return working_intervals


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    attendance_approval = fields.Boolean('Require Attendance Approval')




