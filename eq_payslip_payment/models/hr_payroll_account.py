#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

# class HrPayslip(models.Model):
#     _inherit = 'hr.payslip'
#
#     def action_payslip_done(self):
#         """
#             Generate the accounting entries related to the selected payslips
#             A move is created for each journal and for each month.
#         """
#         res = super(HrPayslip, self).action_payslip_done()
#         self._action_create_account_move()
#
#
#         #add : merge all lines into one move and delete other moves
#         if len(self.mapped('move_id')):
#             main_move_id = self.mapped('move_id')[0].with_context(check_move_validity=False)
#
#             for move in self.mapped('move_id'):
#                 for line in move.with_context(check_move_validity=False).line_ids:
#                     line.move_id = main_move_id.id
#                 if move.id != main_move_id.id:
#                     move.unlink()
#             for slip in self:
#                 slip.move_id = main_move_id.id
#
#         #     print("?>>>>>>>>>>>>>>>>>>> ",slip.move_id)
#         # print(">>>>>>>>>>>>>>>>>>>self.mapped('move_id') ",self.mapped('move_id'))
#         # 1/0
#         return res
#
#     def _action_create_account_move(self):
#         precision = self.env['decimal.precision'].precision_get('Payroll')
#
#         # Add payslip without run
#         payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)
#
#         # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
#         payslip_runs = (self - payslips_to_post).mapped('payslip_run_id')
#         for run in payslip_runs:
#             if run._are_payslips_ready():
#                 payslips_to_post |= run.slip_ids
#
#         # A payslip need to have a done state and not an accounting move.
#         payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.move_id)
#
#         # Check that a journal exists on all the structures
#         if any(not payslip.struct_id for payslip in payslips_to_post):
#             raise ValidationError(_('One of the contract for these payslips has no structure type.'))
#         if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
#             raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))
#
#         # Map all payslips by structure journal and pay slips month.
#         # {'journal_id': {'month': [slip_ids]}}
#         g_journal = False #slip.struct_id.journal_id.id
#         # emps = slip.employee_id.id
#         slip_mapped_data = {slip.employee_id.id: {fields.Date().end_of(slip.date_to, 'month'): self.env['hr.payslip']} for slip in payslips_to_post}
#         for slip in payslips_to_post:
#             g_journal = slip.struct_id.journal_id.id
#             slip_mapped_data[slip.employee_id.id][fields.Date().end_of(slip.date_to, 'month')] |= slip
#
#         for journal_id in slip_mapped_data: # For each journal_id.
#             for slip_date in slip_mapped_data[journal_id]: # For each month.
#
#                 line_ids = []
#                 debit_sum = 0.0
#                 credit_sum = 0.0
#                 date = slip_date
#                 move_dict = {
#                     'narration': '',
#                     'ref': date.strftime('%B %Y'),
#                     'journal_id': g_journal , #journal_id,
#                     'date': date,
#                 }
#
#
#                 for slip in slip_mapped_data[journal_id][slip_date]:
#                     move_dict['narration'] += slip.number or '' + ' - ' + slip.employee_id.name or ''
#                     move_dict['narration'] += '\n'
#                     slip_lines = slip._prepare_slip_lines(date, line_ids)
#                     line_ids.extend(slip_lines)
#
#                 for line_id in line_ids: # Get the debit and credit sum.
#                     debit_sum += line_id['debit']
#                     credit_sum += line_id['credit']
#
#
#                 # 1/0
#
#                 # The code below is called if there is an error in the balance between credit and debit sum.
#                 if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
#                     slip._prepare_adjust_line(line_ids, 'credit', debit_sum, credit_sum, date)
#                 elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
#                     slip._prepare_adjust_line(line_ids, 'debit', debit_sum, credit_sum, date)
#
#                 # Add accounting lines in the move
#                 move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
#                 move = self._create_account_move(move_dict)
#                 for slip in slip_mapped_data[journal_id][slip_date]:
#                     slip.write({'move_id': move.id, 'date': date})
#         return True
#
#
#     def _prepare_slip_lines(self, date, line_ids):
#         self.ensure_one()
#         precision = self.env['decimal.precision'].precision_get('Payroll')
#         new_lines = []
#         for line in self.line_ids.filtered(lambda line: line.category_id):
#             amount = -line.total if self.credit_note else line.total
#             if line.code == 'NET': # Check if the line is the 'Net Salary'.
#                 for tmp_line in self.line_ids.filtered(lambda line: line.category_id):
#                     if tmp_line.salary_rule_id.not_computed_in_net: # Check if the rule must be computed in the 'Net Salary' or not.
#                         if amount > 0:
#                             amount -= abs(tmp_line.total)
#                         elif amount < 0:
#                             amount += abs(tmp_line.total)
#             if float_is_zero(amount, precision_digits=precision):
#                 continue
#             debit_account_id = line.salary_rule_id.account_debit.id
#             credit_account_id = line.salary_rule_id.account_credit.id
#
#             if debit_account_id: # If the rule has a debit account.
#                 debit = amount if amount > 0.0 else 0.0
#                 credit = -amount if amount < 0.0 else 0.0
#
#                 debit_line = self._get_existing_lines(
#                     line_ids + new_lines, line, debit_account_id, debit, credit)
#
#                 if not debit_line:
#                     debit_line = self._prepare_line_values(line, debit_account_id, date, debit, credit)
#                     new_lines.append(debit_line)
#                 else:
#                     debit_line['debit'] += debit
#                     debit_line['credit'] += credit
#                     if line.slip_id.employee_id.address_home_id:
#                         debit_line['partner_id'] = line.slip_id.employee_id.address_home_id.id
#
#             if credit_account_id: # If the rule has a credit account.
#                 debit = -amount if amount < 0.0 else 0.0
#                 credit = amount if amount > 0.0 else 0.0
#                 credit_line = self._get_existing_lines(
#                     line_ids + new_lines, line, credit_account_id, debit, credit)
#
#                 if not credit_line:
#                     credit_line = self._prepare_line_values(line, credit_account_id, date, debit, credit)
#                     new_lines.append(credit_line)
#                 else:
#                     credit_line['debit'] += debit
#                     credit_line['credit'] += credit
#                     if line.slip_id.employee_id.address_home_id:
#                         credit_line['partner_id'] = line.slip_id.employee_id.address_home_id.id
#         return new_lines
#
#
#     def _prepare_line_values(self, line, account_id, date, debit, credit):
#         return {
#             'name': line.name,
#             'partner_id': line.slip_id.employee_id.address_home_id.id if line.slip_id.employee_id.address_home_id else False,#line.partner_id.id,
#             'account_id': account_id,
#             'journal_id': line.slip_id.struct_id.journal_id.id,
#             'date': date,
#             'debit': debit,
#             'credit': credit,
#             'analytic_account_id': line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id,
#         }