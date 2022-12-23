# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) 2020.
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#    website': https://www.linkedin.com/in/ramadan-khalil-a7088164
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
##############################################################################

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
# from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips, ResultRules
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, date_utils
from odoo.tools.misc import format_date
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError, UserError

# class HrPayslip(models.Model):
#     _inherit = "hr.payslip"
#
#
#     attendance_sheet_id = fields.Many2one('attendance.sheet')
#     def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
#         res = super(HrPayslip,self)._get_worked_day_lines( domain, check_out_of_contract)
#         for rec in self:
#             rec.onchange_employee_set_sheet()
#             if rec.attendance_sheet_id:
#                 for work_day in rec.attendance_sheet_id._get_workday_lines():
#                     res.append(work_day)
#
#         return res
#
#
#     def get_attendance_work_days(self):
#
#         for rec in self:
#             if rec.attendance_sheet_id:
#                 worked_day_lines = rec.attendance_sheet_id._get_workday_lines()
#                 rec.worked_days_line_ids = [(0, 0, x) for x in
#                                                worked_day_lines]
#                 # self._get_new_worked_days_lines()
#     def compute_sheet(self):
#         # for rec in self:
#         #     rec.get_attendance_work_days()
#         res = super(HrPayslip,self).compute_sheet()
#
#         return res
#     @api.model
#     def create(self,vals):
#         """
#         search attendance sheet for employee
#         """
#         if not vals.get('attendance_sheet_id',False):
#             employee_id = vals['employee_id']
#             date_from = vals['date_from']
#             date_to = vals['date_to']
#             sheet = self.sudo().env['attendance.sheet'].search([
#                     ('employee_id','>=',employee_id),
#                     ('date_from','>=',date_from),
#                     ('date_to','<=',date_to),
#                     ('state','=','done'),
#                     ],limit=1)
#             if sheet:
#                 vals['attendance_sheet_id'] = sheet.id
#
#
#         res = super(HrPayslip,self).create(vals)
#
#         return res
#
#     @api.onchange('employee_id','date_from','date_to')
#     def onchange_employee_set_sheet(self):
#         for rec in self:
#             rec.attendance_sheet_id = False
#             if rec.employee_id and rec.date_from and rec.date_to:
#                 sheet = self.env['attendance.sheet'].search([
#                     ('employee_id','>=',rec.employee_id.id),
#                     ('date_from','>=',rec.date_from),
#                     ('date_to','<=',rec.date_to),
#                     ('state','=','done'),
#                     ],limit=1)
#                 if sheet:
#                     rec.attendance_sheet_id = sheet.id
#
#
#
#     @api.constrains('employee_id','date_from','date_to')
#     def check_attendance_sheet(self):
#         for rec in self:
#             if not rec.attendance_sheet_id:
#                 raise ValidationError(_("Sorry!! , No Attendance Sheet Found for Employee ")+rec.employee_id.name)