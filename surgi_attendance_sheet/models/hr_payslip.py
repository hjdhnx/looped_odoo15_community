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


# class HrPayslipPenalty(models.Model):
#     _inherit = "hr.payslip"
#
#     penalty_ids = fields.Many2many(comodel_name='hr.attendance.penalty', store=True,
#                                    string='Penalties')
#     penalty_amount = fields.Float('Total Penalties',
#                                   compute='_compute_penalty_total_amount')
#
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('Reviewed', 'Compute'),
#         ('Final Reviewed', 'Final Reviewed'),
#         ('verify', 'Waiting'),
#         ('done', 'Done'),
#         ('paid', 'Paid'),
#         ('cancel', 'Rejected'),
#     ], 'Status', select=True, readonly=True, copy=False,
#         help='* When the payslip is created the status is \'Draft\'.\
#             \n* If the payslip is under verification, the status is \'Waiting\'. \
#             \n* If the payslip is confirmed then status is set to \'Done\'.\
#             \n* When user cancel payslip the status is \'Rejected\'.')
#
#
#     #old original
#     # def action_payslip_cancel(self):
#     #     if self.filtered(lambda slip: slip.state == 'done'):
#     #         raise UserError(_("Cannot cancel a payslip that is done."))
#     #     self.write({'state': 'cancel'})
#     #     self.mapped('payslip_run_id').action_close()
#
#     def _compute_penalty_total_amount(self):
#         for slip in self:
#             slip.penalty_amount = sum([p.amount for p in slip.penalty_ids])
#
#     def hr_verify_sheet(self):
#         for rec in self:
#             rec.final_review_payslip()
#         res = super(HrPayslipPenalty,self).hr_verify_sheet()
#
#         return res
#
#     def final_review_payslip(self):
#         # self.compute_sheet()
#         self.write({
#             # 'state': 'Final Reviewed',
#          'final_reviewed_by': self.env.uid, 'final_reviewed_date': datetime.now().strftime('%Y-%m-%d')})
#         body = "Document Final Reviewed"
#         self.message_post(body=body, message_type='email')
#         return {}
#
#     def review_payslip(self):
#         # self.compute_sheet()
#         # 1/0
#         self.write({
#             # 'state': 'Reviewed',
#         'reviewed_by': self.env.uid, 'reviewed_date': datetime.now().strftime('%Y-%m-%d')})
#         body = "Document Reviewed"
#         self.message_post(body=body, message_type='email')
#         self.final_review_payslip()
#         self.state = 'verify'
#         return {}
#
#     def action_refresh_from_work_entries(self):
#
#         res = super(HrPayslipPenalty,self).action_refresh_from_work_entries()
#         for rec in self:
#             rec.state = 'Reviewed'
#         return res
#     def compute_sheet(self):
#         for rec in self:
#             # rec.review_payslip()
#             rec.state = 'draft'
#             # rec.state = 'verify'
#         res = super(HrPayslipPenalty,self).compute_sheet()
#         for rec in self:
#             # rec.review_payslip()
#             if rec._context.get('is_check_percentage',False):
#                 rec.check_max_deduction()
#             rec.state = 'Final Reviewed'
#         return res
#
#
#
#     def check_max_deduction(self):
#
#         """
#         #prevent deduction to be more than percentage in setting
#         """
#
#         for rec in self:
#             get_param = self.env['ir.config_parameter'].sudo().get_param
#             max_deduction_percentage = get_param('ext_hr_payroll.max_deduction_percentage')
#             # max_deduction_percentage = res['max_deduction_percentage']
#             if float(max_deduction_percentage) :
#                 if rec.line_ids:
#                     gross = rec.env['hr.payslip.line'].search([('slip_id','=',rec.id),('code','=','GROSS')])
#                     gross = abs(gross.amount)
#                     total_ded = rec.env['hr.payslip.line'].search([('slip_id','=',rec.id),('code','=','DED')])
#                     total_ded = abs(total_ded.amount)
#
#                     if gross:
#                         ded_percentage = (total_ded / gross) * 100
#                         # print(">>>>>>>>>>>>>>>>>>>>>>>>ded_percentage ",ded_percentage)
#                         if ded_percentage > float(max_deduction_percentage):
#                             raise ValidationError(_("Sorry!!, you can't confirm because Deduction Pecentage from Gross more than percentage defined in setting for employee ")+rec.employee_id.name)
#
#         return
#     def action_set_to_draft(self):
#         for rec in self:
#             rec.state = 'draft'
#
#     def action_set_penalty(self):
#         for rec in self:
#             rec.action_get_penalty()
#             rec.state = 'Reviewed'
#
#     def action_get_penalty(self):
#         for slip in self:
#             if slip.date_from and slip.date_to and slip.employee_id:
#                 penalty_ids = self.env['hr.attendance.penalty'].search(
#                     [('accrual_date', '>=', slip.date_from),
#                      ('accrual_date', '<=', slip.date_to),
#                      ('paid', '=', False),
#                      ('employee_id', '=', slip.employee_id.id)])
#                 if penalty_ids:
#                     slip.penalty_ids = [(6, 0, penalty_ids.ids)]
#
#     def action_payslip_done(self):
#         res = super(HrPayslipPenalty,self).action_payslip_done()
#         for slip in self:
#             if slip.penalty_ids:
#                 for pen in self.penalty_ids:
#                     pen.paid = True
#         return res
#
#     @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from',
#                   'date_to')
#     def _onchange_employee(self):
#         self.action_get_penalty()
#         return super(HrPayslipPenalty, self)._onchange_employee()
