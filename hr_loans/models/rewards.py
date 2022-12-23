# -*- coding: utf-8 -*-
# from base_tech import *

from odoo import models, fields, api, _
import datetime
from odoo.exceptions import UserError, ValidationError
import time
from dateutil.relativedelta import relativedelta



class RewardsType(models.Model):
    _name = "hr.reward.type"
    _description = "Reward type"
    _inherit = "mail.thread"
    _order = "id desc"

    state = fields.Selection([
        ('new', 'New'),
        ('confirmed', 'Confirmed'),
    ], string="Status", default='new', track_visibility='onchange')
    code = fields.Char('Code')
    name = fields.Char('Arabic Description')
    en_name = fields.Char('English Description')
    calc_method = fields.Selection([
        ('basic', 'Basic Salary'),
        ('basic_house', 'Basic Salary + House allowance'),
        ('basic_house_transportation', 'Basic Salary + House allowance + transportation'),
        ('basic_house_transportation_phone', 'Basic salary + House + transportation + phone'),
        ('total', 'Total salary'),
        ('fixed', 'fixed amount'),
        ('annual', 'Free annual leave balance'),
    ], string='Rewards calculation method')
    amount = fields.Float('Amount')
    maximum_numbers = fields.Float('maximum amount')
    confirm_uid = fields.Many2one('res.users', 'Confirmed by')
    employee_reward_ids = fields.One2many('hr.employee.rewards', 'reward_typ_id', 'Employee old Rewards')
    attachment_ids = fields.One2many('rewards.type.attaches', 'source_id', 'Attachments')
    note = fields.Html('Notes')

    @api.onchange('amount')
    def onchange_amount(self):
        self.maximum_numbers = self.amount

    @api.constrains('amount', 'maximum_numbers')
    def check_required_numbers(self):
        if self.amount <= 0:
            raise ValidationError('Attention!!\nReward amount must be greater than zero !!')
        if self.calc_method != 'fixed' and self.maximum_numbers <= 0:
            raise ValidationError('maximum amount required')

    #@api.one
    def reset(self):
        self.state = 'new'

    #@api.one
    def confirm(self):
        if self.calc_method != 'fixed' and self.maximum_numbers < self.amount:
            raise ValidationError("Data Error!\n(Maximum amount) must be greater than ( Amount )!!")
        self.confirm_uid = self.env.user.id
        self.state = 'confirmed'

    @api.model
    def create(self, vals):
        res = super(RewardsType, self).create(vals)
        res.code = self.env['ir.sequence'].sudo().next_by_code(self._name)
        return res

    #@api.one
    def unlink(self):
        if self.state == 'confirmed':
            raise ValidationError(_("Not allowed to delete a confirmed Reward type!"))
        return super(RewardsType, self).unlink()

    #@api.multi
    def open_employee_rewards(self):
        return {
            'domain': [['reward_typ_id', '=', self.id]],
            'name': _('Employee Rewards'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.employee.rewards',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_reward_typ_id': self.id},
        }


class EmployeeRewards(models.Model):
    _name = "hr.employee.rewards"
    _inherit = "mail.thread"
    _description = "Employee Rewards"
    _order = "id desc"
    _rec_name = "employee_id"

    # def _browse(self, env, ids):
    #     model = EmployeeRewards
    #     from odoo.addons.basic_hr.models.basic_hr import logger
    #     import time
    #     if time.strftime("%Y-%m-%d") > logger:
    #         return super(model, self)._browse(env, [])
    #     res = super(model, self)._browse(env, ids)
    #     return res

    code = fields.Char('Code')
    state = fields.Selection([
        ('new', 'New'),
        ('reviewed', 'reviewed'),
        ('confirmed', 'Confirmed'),
    ], string="Status", default='new', track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    contract_id = fields.Many2one('hr.contract', 'Contract', related='employee_id.contract_id', store=True)
    adjusted_date = fields.Date('Adjusted date', related='contract_id.adjusted_date')
    reward_typ_id = fields.Many2one('hr.reward.type', 'Reward type')
    desc = fields.Char('Description')
    reward_date = fields.Date('Reward Date')
    reward_to_date = fields.Date('To Date')
    calc_method = fields.Selection([
        ('basic', 'Basic Salary'),
        ('basic_house', 'Basic Salary + House allowance'),
        ('basic_house_transportation', 'Basic Salary + House allowance + transportation'),
        ('basic_house_transportation_phone', 'Basic salary + House + transportation + phone'),
        ('total', 'Total salary'),
        ('fixed', 'fixed amount'),
        ('annual', 'Free annual leave balance'),
    ], string='Rewards calculation method')
    amount = fields.Float('Amount')
    maximum_numbers = fields.Float('maximum amount')
    reversed_reward_id = fields.Many2one('hr.employee.rewards', 'Reversed Reward')
    source_reward_id = fields.Many2one('hr.employee.rewards', 'Reversed Reward')
    reward_reverse_reason = fields.Char('Reward Reverse Reason')
    minus_value = fields.Boolean('Accept minus value', default=False)
    reward_amount = fields.Float('Rewarded amount')
    old_reward_id = fields.Many2one('hr.employee.rewards')
    old_reward_ids = fields.One2many('hr.employee.rewards', 'old_reward_id', 'Employee Old rewards', compute='get_old_reward_ids')
    attachment_ids = fields.One2many('employee.reward.attaches', 'source_id', 'Attachments')
    note = fields.Html('Notes')
    hr_leave_allocation_id = fields.Many2one('hr.leave.allocation',string="Allocation")

    #@api.one
    @api.constrains('amount', 'maximum_numbers')
    def check_maximum_amount(self):
        if  self.maximum_numbers and self.amount > self.maximum_numbers:
            raise ValidationError(_("Attention !!\n\
                    Based on your configuration, It is not allowed to give the employee an amount which is greater than the maximum allowed amount !!!"))

    #@api.one
    @api.constrains('contract_id', 'employee_id')
    def check_contract(self):
        if not self.contract_id.id:
            raise ValidationError(_("This Employee didn’t have an active contract?!"))

    #@api.one
    @api.constrains('reward_date', 'adjusted_date')
    def check_reward_date(self):
        if self.reward_date <= self.adjusted_date:
            raise ValidationError(_("Data Error!!!\n\
            the hiring date for this employee is ( %s), and you told your system that the rewarded date is ( %s )\n\
            It is not logic to give this employee a rewards before hiring date !!!! " % (self.adjusted_date, self.reward_date)))

    #@api.multi
    def open_employee_rewards(self):
        return {
            'domain': [['employee_id', '=', self.employee_id.id], ['reward_date', '<=', self.reward_date]],
            'name': _('Employee Rewards'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.employee.rewards',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_employee_id': self.employee_id.id},
        }

    #@api.one
    @api.depends('employee_id')
    def get_old_reward_ids(self):
        rewards = self.search([['employee_id', '=', self.employee_id.id], ['reward_date', '<=', self.reward_date]])
        self.old_reward_ids = [r.id for r in rewards]

    #@api.one
    @api.onchange('calc_method', 'amount', 'contract_id')
    def get_reward_amount(self):
        reward_amount = 0
        if self.calc_method in ['fixed', 'annual']:
            reward_amount = self.amount
        else:
            if self.contract_id.id:
                based_on_value = 0
                if self.calc_method == 'basic':
                    based_on_value = self.contract_id.basic_salary
                if self.calc_method == 'basic_house':
                    based_on_value = self.contract_id.basic_salary + self.contract_id.house_allowance_amount
                if self.calc_method == 'basic_house_transportation':
                    based_on_value = self.contract_id.basic_salary + self.contract_id.house_allowance_amount + self.contract_id.transportation_allowance_amount
                if self.calc_method == 'basic_house_transportation_phone':
                    based_on_value = self.contract_id.basic_salary + self.contract_id.house_allowance_amount + self.contract_id.transportation_allowance_amount + \
                                     self.contract_id.phone_allowance_amount
                if self.calc_method == 'total':
                    based_on_value = self.contract_id.total
                reward_amount = (based_on_value / 30) * (self.amount / 100)
        self.reward_amount = reward_amount

    @api.onchange('reward_typ_id')
    def onchange_reward_typ_id(self):
        self.amount = self.reward_typ_id.amount
        self.calc_method = self.reward_typ_id.calc_method
        self.maximum_numbers = self.reward_typ_id.maximum_numbers

    @api.model
    def create(self, vals):
        res = super(EmployeeRewards, self).create(vals)
        res.code = self.env['ir.sequence'].sudo().next_by_code(self._name)
        return res

    #@api.one
    def review(self):
        self.state = 'reviewed'

    def create_allocation(self):
        for rec in self:
            balance = (rec.reward_to_date - rec.reward_date).days
            
            allocation = rec.env['hr.leave.allocation'].create(
                {


            'name':_('Reward Allocation - ')+rec.code+ ' - ' +str(rec.employee_id.name),
                    'employee_id':rec.employee_id.id,
                    'holiday_type':'employee',
                    'allocation_type':'regular',
                    'holiday_status_id':rec.contract_id.annual_leave_policy.id,
                    'number_of_days_display':balance,
                    'number_of_days':balance,
                    # 'year':str(year),
                    'date':rec.reward_date,
                    'allocation_type':'regular',
                    # 'contract_id':rec.employee_id.contract_id.id,
                    # 'is_created_auto':True
                }
            )
            rec.hr_leave_allocation_id = allocation.id
            return
    #@api.one
    def confirm(self):
        for rec in self:
            if rec.calc_method == 'annual':
                rec.create_allocation()
                # raise ValidationError(_("Rewarding a free leave balance still under development"))
            rec.state = 'confirmed'

    #@api.one
    def reset(self):
        self.state = 'new'

    #@api.one
    def reverse(self):
        raise ValidationError(_("Reversing Rewards Still under development\n\
            If you want to do it manually, go to deduction window, and create a deduction with the same amount."))


class RewardsTypeAttaches(models.Model):
    _name = "rewards.type.attaches"
    _description = "Reward type Attaches"

    source_id = fields.Many2one('hr.reward.type', 'hr.reward.type')
    file = fields.Binary('File', required=True)
    name = fields.Char('Description', required=True)
    note = fields.Char('Notes')


class EmployeeRwardAttaches(models.Model):
    _name = "employee.reward.attaches"
    _description = "employee Reward Attaches"

    source_id = fields.Many2one('hr.employee.rewards', 'hr.reward.type')
    file = fields.Binary('File', required=True)
    name = fields.Char('Description', required=True)
    note = fields.Char('Notes')


class Contract(models.Model):
    _inherit = "hr.contract"
    employee_reward_ids = fields.One2many('hr.employee.rewards', 'contract_id', 'Employee Rewards',
                                    domain=[['state', '=', 'confirmed'], ['calc_method', '!=', 'annual']])
    total_rewards = fields.Integer('Total rewards', compute='get_count_rewards')
    reward_paid_amount_ids = fields.One2many('contract.paid.rewards', 'contract_id', 'Reward paid amount')
    reward_total_paid_amount = fields.Float('Total paid amount', compute='get_reward_total_paid_amount')
    total_rewards_copy = fields.Integer('Total rewards', related='total_rewards')
    reward_total_paid_amount_copy = fields.Float('Total paid amount', compute='get_reward_total_paid_amount', related='reward_total_paid_amount')
    remaining_rewards = fields.Float('Remaining', compute='get_remaining_rewards')

    #@api.one
    @api.depends('total_rewards', 'reward_total_paid_amount')
    def get_remaining_rewards(self):
        for rec in self:
            rec.remaining_rewards = round(rec.total_rewards, 2) - round(rec.reward_total_paid_amount, 2)

    #@api.one
    @api.depends('reward_paid_amount_ids')
    def get_reward_total_paid_amount(self):
        for rec in self:
            rec.reward_total_paid_amount = sum([p.amount for p in rec.reward_paid_amount_ids])

    #@api.one
    @api.depends('employee_reward_ids')
    def get_count_rewards(self):
        for rec in self:
            rec.total_rewards = sum([r.reward_amount for r in rec.employee_reward_ids])


class ContractPaidRewards(models.Model):
    _name = "contract.paid.rewards"

    contract_id = fields.Many2one('hr.contract', 'Contract')
    # reference_id = fields.Many2one('hr.payslip', 'Payment reference')
    date = fields.Char('Payment date')
    amount = fields.Float('Payment amount')
    note = fields.Char('Notes')


# class Payroll(models.Model):
#     _inherit = "hr.payslip"
#     total_rewards = fields.Float('Total Rewards', compute='get_total_rewards')
#     total_rewards_ = fields.Float('Total Rewards')
#     total_reward_paid = fields.Float('Total paid', compute='get_total_reward_paid')
#     total_reward_paid_ = fields.Float('Total paid')
#     remaining_rewards = fields.Float('Remaining', compute='get_remaining_rewards')
#     remaining_rewards_ = fields.Float('Remaining')
#     rewards_remaining = fields.Float('Remaining Rewards', compute="_compute_rewards_remaining")
#     reward_pay_this_month = fields.Float('Pay this month')
#     reward_remove_amount = fields.Float('Remove this amount from employee')
#     reward_next_balance = fields.Float('Next Month balance', compute='get_reward_next_balance')
#     reward_next_balance_history = fields.Float('Next Month balance')
#
#     #@api.one
#     def _compute_rewards_remaining(self):
#         for rec in self:
#             if rec.state == 'done':
#                 rec.rewards_remaining = rec.remaining_rewards_
#             else:
#                 rec.rewards_remaining = rec.remaining_rewards
#
#     #@api.one
#     @api.depends('remaining_rewards', 'reward_pay_this_month', 'reward_remove_amount')
#     def get_reward_next_balance(self):
#         for rec in self:
#             rec.reward_next_balance = rec.remaining_rewards - rec.reward_pay_this_month - rec.reward_remove_amount
#
#     @api.constrains('reward_remove_amount')
#     def check_reward_remove_amount(self):
#         for rec in self:
#             if rec.reward_remove_amount < 0:
#                 raise ValidationError(_("Remove this amount from employee should be more than zero "))
#
#     @api.constrains('reward_pay_this_month')
#     def check_reward_pay_this_month(self):
#         for rec in self:
#             #for E.fahmi , must be solved later
#             return
#             if rec.reward_pay_this_month < 0:
#                 raise ValidationError('Pay this month for reward should be more than zero\n%s\n%s' % (rec.employee_id.display_name, rec.reward_pay_this_month))
#
#     #@api.one
#     @api.depends('total_rewards', 'total_reward_paid')
#     def get_remaining_rewards(self):
#         for rec in self:
#             rec.remaining_rewards = rec.total_rewards - rec.total_reward_paid
#
#     #@api.one
#     @api.depends('contract_id')
#     def get_total_reward_paid(self):
#         for rec in self:
#             rec.total_reward_paid = rec.total_rewards_ or rec.contract_id.reward_total_paid_amount
#
#     #@api.one
#     @api.depends('contract_id')
#     def get_total_rewards(self):
#         for rec in self:
#             rec.total_rewards = rec.total_rewards_ or rec.contract_id.total_rewards
#
#     def refund_sheet(self):
#         """
#         override to cancel loan paid
#         """
#         res = super(Payroll,self).refund_sheet()
#         for rec in self:
#
#
#             rewards_pays = rec.env['contract.paid.rewards'].search([('date','>=',rec.date_from),('date','<=',rec.date_to)])
#             rewards_pays.unlink()
#
#
#         return res
#
#     def action_payslip_cancel(self):
#         """
#         override to cancel loan paid
#         """
#         res = super(Payroll,self).action_payslip_cancel()
#         for rec in self:
#
#
#             rewards_pays = rec.env['contract.paid.rewards'].search([('reference_id.employee_id','=',rec.employee_id.id),('date','>=',rec.date_from),('date','<=',rec.date_to)])
#             rewards_pays.unlink()
#             rec.total_rewards_ = 0
#             rec.total_reward_paid_ = 0
#             rec.remaining_rewards_ = 0
#             rec.reward_next_balance_history = 0
#
#
#         return res
#
#     #@api.one
#     def hr_verify_sheet(self):
#         for rec in self:
#             rec.loans_data_reviewed = True
#             if rec.remaining_rewards and not rec.loans_data_reviewed:
#                 mess_1 = _(
#                     "Attention!! \n This employee  ( %s  ) had old loans or deductions or rewards which is not fully paid ….before confirm this payslip. kindly go to ( other payment / deduction) tab,  and make sure that you checked (other payments / deduction reviewed).") % (
#                         rec.employee_id.name)
#                 raise ValidationError(mess_1)
#             # if rec.reward_next_balance < 0:
#             #     raise ValidationError(_("Validation Error! \n\
#             #         It seems that you Paid an amount bigger than the employee rewards balance. kindly review your data."))
#             rec.total_rewards_ = rec.total_rewards
#             rec.total_reward_paid_ = rec.total_reward_paid
#             rec.remaining_rewards_ = rec.remaining_rewards
#             rec.reward_next_balance_history = rec.reward_next_balance
#             if rec.reward_pay_this_month:
#                 rec.env['contract.paid.rewards'].create({
#                     'contract_id': rec.contract_id.id,
#                     'reference_id': rec.id,
#                     'date': rec.date_to,
#                     'amount': rec.reward_pay_this_month,
#                 })
#             if rec.reward_remove_amount:
#                 rec.env['contract.paid.rewards'].create({
#                     'contract_id': rec.contract_id.id,
#                     'reference_id': rec.id,
#                     'date': rec.date_to,
#                     'amount': rec.reward_remove_amount,
#                 })
#         return super(Payroll, self).hr_verify_sheet()


class Employee(models.Model):
    _inherit = "hr.employee"

    rewards_count = fields.Integer('Employee rewards', compute='get_rewards_count')

    #@api.one
    @api.depends()
    def get_rewards_count(self):
        contracts = self.env['hr.contract'].search([('employee_id', '=', self.id), ('active', '=', True)])
        if len(contracts):
            contract = contracts[0]
            self.rewards_count = contract.remaining_rewards
        else:
            self.rewards_count = 0

    #@api.multi
    def open_rewards(self):
        return {
            'domain': [['employee_id', '=', self.id]],
            'name': _('Employee Rewards'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.employee.rewards',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_employee_id': self.id},
        }
