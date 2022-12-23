# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date

import time


class LeaveReconciliation(models.Model):
    _name = "hr.leave.reconciliation"
    _description = "Leave reconciliation"
    _order = "id desc"
    _inherit = "mail.thread"


    READONLY_STATES = {
        'refused': [('readonly', True)]
    }

    state = fields.Selection([
        ('new', 'New'),
        ('reviewed', 'Data review'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ], string="Status", default='new', track_visibility='onchange')
    name = fields.Char('Description', states=READONLY_STATES)
    code = fields.Char('Code')
    employee_id = fields.Many2one('hr.employee', 'Employee', states=READONLY_STATES)
    contract_id = fields.Many2one('hr.contract', 'Contract', states=READONLY_STATES)
    type = fields.Selection([
        ('liquidation', 'Leave Balance Liquidation'),
        ('reconciliation', 'Leave Request reconciliation'),
        ('both', 'Both'),
    ], string='Reconciliation type', states=READONLY_STATES)
    total_leave_reconciliation = fields.Float('Total leave request reconciliation', compute='_get_reconciliation_data', store=True)
    total_previously_paid = fields.Float('Total Previously paid', compute='_get_reconciliation_data', store=True)
    total_remaining = fields.Float('Total Remaining', compute='_get_reconciliation_data', store=True)
    # Totals
    total_pay_to_employee = fields.Float('Total pay to employee', compute='_get_reconciliation_data', store=True)
    total_remain_after_pay = fields.Float('Total remaining after payment', compute='_get_reconciliation_data', store=True)
    leave_to_reconcile_ids = fields.One2many('leave.reconcile.line', 'reconciliation_id', 'Leave to reconcile')
    current_leave_balance = fields.Float('Current leave Balance', compute='get_current_leave_balance')
    want_to_liquidate = fields.Float('I want to Liquidate', states=READONLY_STATES)
    reconcile_based_on = fields.Selection([
        ('basic', 'Basic Salary'),
        ('basic_house', 'Basic Salary + House allowance'),
        ('basic_house_transportation', 'Basic Salary + House allowance + transportation'),
        ('basic_house_transportation_phone', 'Basic salary + House + transportation + phone'),
        ('total', 'Total salary'),
    ], string='Reconciliation based on', states=READONLY_STATES)
    balance_liquidation_amount = fields.Float('Balance Liquidation amount', states=READONLY_STATES, )
    total_pay_reconciliation = fields.Float('Total pay to employee ( leave request reconciliation)', related='total_pay_to_employee')
    plus_balance_liquidation_amount = fields.Float('Plus : balance liquidation amount', related='balance_liquidation_amount')
    plus_air_ticket_value = fields.Float('Plus : Air ticket value', compute='get_plus_air_ticket_value')
    minus_loan_deduction = fields.Float('Minus : Loans deduction', related='deduct_loan')
    minus_violation = fields.Float('Minus : Violation - other deductions', related='deduct_deduction')
    plus_rewards = fields.Float('Plus : Rewards', related='deduct_rewards')
    balance_reconciliation = fields.Float('Net Reconciliation amount', compute='get_balance_reconciliation')
    air_ticket_to_reconcile_ids = fields.One2many('air.ticket.reconcile.line', 'reconciliation_id', 'Air tickets to reconcile', states=READONLY_STATES)
    attachment_ids = fields.One2many('leave.reconciliation.attachment', 'source_id', 'Attachments', states=READONLY_STATES)
    note = fields.Html('Notes')
    linked_leave_allocation_id = fields.Many2one('hr.leave', 'Linked Leave Allocation')
    linked_leave_request_id = fields.Many2one('hr.leave', 'Linked Leave request')
    # Loans
    net_reconciliation_amount = fields.Float('Net Reconciliation amount')
    total_loans = fields.Float('Total Loans')
    total_paid_loan = fields.Float('Total Paid Amount')
    remaining_loan = fields.Float('Remaining Amount', compute='get_remaining_loan')
    deduct_loan = fields.Float('Deduct with leave reconciliation')
    remaining_loan_after_reconcile = fields.Float('Remaining after Reconciliation', compute='get_remaining_loan_after_reconcile')
    # Deduction
    total_deduction_amount = fields.Float('Total deduction amount')
    total_deduction_paid_amount = fields.Float('Total paid amount')
    remaining_deduction = fields.Float('Remaining', compute='get_remaining_deduction')
    deduct_deduction = fields.Float('Deduct with leave reconciliation')
    remaining_deduction_after_reconcile = fields.Float('Remaining after Reconciliation', compute='get_remaining_deduction_after_reconcile')
    # Rewards
    total_rewards = fields.Integer('Total rewards')
    reward_total_paid_amount = fields.Float('Total paid amount')
    remaining_rewards = fields.Float('Remaining', compute='get_remaining_rewards')
    deduct_rewards = fields.Float('Pay with leave reconciliation')
    remaining_rewards_after_reconcile = fields.Float('Remaining after Reconciliation', compute='get_remaining_rewards_after_reconcile')
    # Smart button info
    count_leave_allocations = fields.Integer('Leave Allocation', compute='get_counts', multi=True)
    count_leave_requests = fields.Integer('Leave Requests', compute='get_counts', multi=True)
    count_air_tickets = fields.Integer('Air ticket requests', compute='get_counts', multi=True)
    count_old_reconciliation = fields.Integer('Old Reconciliations', compute='get_counts', multi=True)

    @api.constrains()
    def check_last_reconciliation_status(self):
        if self.search([['state', 'no in', ['refused', 'approved']], ['employee_id', '=', self.employee_id.id]]):
            raise ValidationError(_("Not Allowed !! \n\
                We found that there is some old leave reconciliation requests for the same employee which still under process, kindly request from Hr\
                department to finalize all old leave reconciliation requests before requesting for a new one."))

    #@api.one
    @api.depends('employee_id')
    def get_counts(self):
        self.count_leave_allocations = len(self.env['hr.leave'].search([['linked_leave_reconciliation_id', '=', self.id], ['type', '=', 'add']]))
        self.count_leave_requests = len(self.leave_to_reconcile_ids)
        self.count_air_tickets = len(self.air_ticket_to_reconcile_ids)
        self.count_old_reconciliation = len(self.search([['employee_id', '=', self.employee_id.id]]))

    #@api.multi
    def open_leave_allocations(self):
        return {
            'domain': [['linked_leave_reconciliation_id', '=', self.id], ['type', '=', 'add']],
            'name': _("Leave Allocation"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': "hr.leave",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'form_view_ref': 'hr_holidays.edit_holiday_new', 'tree_view_ref': 'hr_holidays.view_holiday_allocation_tree'},
        }

    #@api.multi
    def open_leave_requests(self):
        return {
            'domain': [['id', '=', self.leave_to_reconcile_ids.ids]],
            'name': _("Leave Requests"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': "hr.leave",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'form_view_ref': 'mits_hr_leaves.leave_request_form', 'tree_view_ref': 'mits_hr_leaves.view_holiday'},
        }

    #@api.multi
    def open_air_tickets(self):
        return {
            'domain': [['id', '=', self.air_ticket_to_reconcile_ids.ids]],
            'name': _("Air ticket requests"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': "air.ticket.request",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {},
        }
        pass

    #@api.multi
    def open_old_reconciliation(self):
        return {
            'domain': [['employee_id', '=', self.employee_id.id]],
            'name': _("Old Reconciliations"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': self._name,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {},
        }

    #@api.one
    @api.depends('total_pay_to_employee', 'plus_balance_liquidation_amount', 'plus_air_ticket_value', 'minus_loan_deduction', 'minus_violation',
                 'plus_rewards', )
    def get_balance_reconciliation(self):
        for rec in self:
            rec.balance_reconciliation = rec.total_pay_to_employee + rec.plus_balance_liquidation_amount + rec.plus_air_ticket_value - \
                                        rec.minus_loan_deduction - rec.minus_violation + rec.plus_rewards

    #@api.one
    @api.depends('remaining_rewards', 'deduct_rewards')
    def get_remaining_rewards_after_reconcile(self):
        for rec in self:
            rec.remaining_rewards_after_reconcile = rec.remaining_rewards - rec.deduct_rewards

    #@api.one
    @api.depends('total_rewards', 'reward_total_paid_amount')
    def get_remaining_rewards(self):
        for rec in self:
            rec.remaining_rewards = rec.total_rewards - rec.reward_total_paid_amount

    #@api.one
    @api.depends('remaining_deduction', 'deduct_deduction')
    def get_remaining_deduction_after_reconcile(self):
        for rec in self:
            rec.remaining_deduction_after_reconcile = rec.remaining_deduction - rec.deduct_deduction

    #@api.one
    @api.depends('total_deduction_amount', 'total_deduction_paid_amount')
    def get_remaining_deduction(self):
        for rec in self:
            rec.remaining_deduction = rec.total_deduction_amount - rec.total_deduction_paid_amount

    #@api.one
    @api.depends('remaining_loan', 'remaining_loan')
    def get_remaining_loan_after_reconcile(self):
        for rec in self:
            rec.remaining_loan_after_reconcile = rec.remaining_loan - rec.deduct_loan

    #@api.one
    @api.depends('remaining_loan', 'deduct_loan')
    def get_remaining_loan_after_reconcile(self):
        for rec in self:
            rec.remaining_loan_after_reconcile = rec.remaining_loan - rec.deduct_loan

    #@api.one
    @api.depends('total_loans', 'total_paid_loan')
    def get_remaining_loan(self):
        for rec in self:
            rec.remaining_loan = rec.total_loans - rec.total_paid_loan

    @api.onchange('contract_id')
    def get_loan_deduction_rewards_data(self):
        for rec in self:
            rec.total_loans = rec.contract_id.total_loans_copy
            rec.total_paid_loan = rec.contract_id.total_paid_amount_copy
            rec.remaining_loan = rec.contract_id.remaining_amount
            rec.total_deduction_amount = rec.contract_id.total_deduction_amount_
            rec.total_deduction_paid_amount = rec.contract_id.total_paid_amount_
            rec.remaining_deduction = rec.contract_id.remaining

    #@api.one
    def action_data_review(self):
        self.refresh_data()
        self.state = 'reviewed'

    #@api.one
    def action_confirm(self):
        self.refresh_data()
        self.state = 'confirmed'

    #@api.one
    def action_refuse(self):
        self.state = 'refused'

    #@api.one
    def action_reset(self):
        # if self.search([['employee_id', '=', self.employee_id.id], ['state', 'not in', ['approved', 'refused']]]):
        #     raise ValidationError(_("Not Allowed !! \n\
        #         we found that there is some old leave reconciliation requests for the same employee which still under process, kindly request from Hr\
        #         department to finalize all old leave reconciliation requests before requesting for a new one."))
        self.refresh_data()
        self.state = 'new'

    #@api.multi
    def action_approve(self):
        self.refresh_data()
        if self.search([['employee_id', '=', self.employee_id.id], ['state', 'not in', ['approved', 'refused']], ['id', '!=', self.id]]):
            raise ValidationError(_("Not Allowed !! \n\
                we found that there is some old leave reconciliation requests for the same employee which still under process, kindly request from Hr\
                department to finalize all old leave reconciliation requests before requesting for a new one."))
        if self.want_to_liquidate > 0 and self.type in ['liquidation', 'both'] and not self.get_reconcile_based_on:
            raise ValidationError(_("Dear HR manager,\n\
                Kindly select (Reconciliation based on) in order to let your system to calculate Leave Liquidation amount."))
        if self.want_to_liquidate > self.current_leave_balance:
            raise ValidationError(_("Not allowed !!\n\
                Current leave balance is ( %s ), it is not logic to liquidate ( %s ) which is more than the employee’s current leave balance." % (
                self.current_leave_balance, self.want_to_liquidate)))
        if self.want_to_liquidate < 0:
            raise ValidationError(_("Not allowed!!\nNot allowed to Liquidate a negative days!!!"))
        if self.type == 'reconciliation' and not self.leave_to_reconcile_ids:
            raise ValidationError(_("Not allowed !! \nThere is no leaves to reconcile ..first, you must request for a leave !!!"))
        if self.type == 'liquidation' and self.want_to_liquidate == 0:
            raise ValidationError(_("Not allowed !!\n\
                You requested for leave balance liquidation, kindly write the number of days which you want to Liquidate in ( I want to Liquidate )."))
        if self.type == 'both' and (not self.want_to_liquidate < 1 and not self.leave_to_reconcile_ids):
            raise ValidationError(_("Not Allowed !!\n\
            You told your system that you want to reconcile old Leave request + you want to liquidate some leave balance. this mean that you must have an old\
            leaves which is not fully reconciled + some leave balance which you want to liquidate.\nwhen we reviewed the employee data, we found that this\
            employee does not have old leave requests or he does not have a leave balance to liquidate."))
        there_one_pay_in_leave_to_reconcile = False
        for line in self.leave_to_reconcile_ids:
            if line.pay_to_employee < 0:
                raise ValidationError(_("Data error !! \nNot allowed to pay a negative amount to the employee (Leaves to reconcile tab)"))
            elif line.pay_to_employee > 0:
                there_one_pay_in_leave_to_reconcile = True
                if line.pay_to_employee < round(line.remaining, 2):
                    if not self._context.get('accept_pay_employee', False):
                        return self.return_action('validate.pay.employee', context={
                            'default_reconciliation_id': self.id,
                            'default_pay_to_employee': line.pay_to_employee,
                            'default_desc': line.desc,
                            'default_remaining': line.remaining,
                            'default_type': 'leave_to_reconcile',
                        })
                if line.pay_to_employee > round(line.remaining, 2):
                    raise ValidationError(_("Not Allowed !!\nNot allowed to pay more than the remaining amount in ( leave reconciliation tab)"))
            if self.type in ['reconciliation', 'both'] and line.pay_to_employee != 0:
                self.env['leave.reconciliation.paid.line'].create({
                    'request_id': line.leave_request_id.id,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'amount': line.pay_to_employee,
                    'reconciliation_id': self.id,
                    'notes': 'Paid through leave reconciliation',
                })
        if not there_one_pay_in_leave_to_reconcile and self.type in ['reconciliation', 'both']:
            raise ValidationError(_("Data error !!\n\
                we found that you want to reconcile old leave requests, kindly write the amount which you will pay to employee ( leave to reconcile tab )."))
        there_one_pay_in_air_ticket_to_reconcile = False
        for line in self.air_ticket_to_reconcile_ids:
            there_one_pay_in_air_ticket_to_reconcile = False
            if line.pay_to_employee < 0:
                raise ValidationError(_("Data error !! \nNot allowed to pay a negative amount to the employee (air ticket to reconcile tab)"))
            if line.pay_to_employee > 0:
                there_one_pay_in_air_ticket_to_reconcile = True
            if line.pay_to_employee < line.company_share and not self._context.get('accept_pay_less_company_share_air_ticket', False):
                return self.return_action('validate.pay.employee', context={
                    'default_reconciliation_id': self.id,
                    'default_air_ticket_id': line.air_ticket_type_id.name,
                    'default_type': 'accept_pay_less_company_share_air_ticket',
                })
            if line.pay_to_employee < line.company_share and not self._context.get('accept_pay_more_company_share_air_ticket', False):
                return self.return_action('validate.pay.employee', context={
                    'default_reconciliation_id': self.id,
                    'default_air_ticket_id': line.air_ticket_type_id.name,
                    'default_type': 'accept_pay_more_company_share_air_ticket',
                })
            if line.pay_to_employee != 0:
                line.air_ticket_id.paid_through_reconciliation = True
        if not there_one_pay_in_air_ticket_to_reconcile and self.air_ticket_to_reconcile_ids:
            if not self._context.get('air_ticket_to_reconcile', False):
                return self.return_action('validate.pay.employee', context={
                    'default_reconciliation_id': self.id,
                    'default_type': 'air_ticket_to_reconcile',
                })
        if self.type in ['liquidation', 'both'] and self.want_to_liquidate > 0:
            self.create_leave_request()
        if self.deduct_loan > 0:
            if not self.employee_id.contract_id.id:
                raise ValidationError(_("Data Error !! \n\
                    There is no active contract for this employee!"))
            else:
                self.env['hr.contract.loan.payment'].create({
                    'contract_id': self.employee_id.contract_id.id,
                    'ref': False,
                    'payment_date': self.create_date.split(' ')[0],
                    'paid_amount': self.deduct_loan,
                    'notes': u'تم خصم المبلغ مع تسوية الأجازة',
                })
        if self.deduct_deduction > 0:
            if self.employee_id.contract_id.id:
                raise ValidationError(_("Data Error !! \n\
                    There is no active contract for this employee!"))
            self.env['contract.paid.violation'].create({
                'contract_id': self.employee_id.contract_id.id,
                'date': self.create_date.split(' ')[0],
                'amount': self.deduct_deduction,
                'note': u'تم خصم المبلغ مع تسوية الأجازة',
            })
        if self.deduct_rewards > 0:
            if self.employee_id.contract_id.id:
                raise ValidationError(_("Data Error !! \n\
                    There is no active contract for this employee!"))
            self.env['contract.paid.rewards'].create({
                'contract_id': self.employee_id.contract_id.id,
                'date': self.create_date.split(' ')[0],
                'amount': self.deduct_rewards,
                'note': u'تم سداد المبلغ مع تسوية الأجازة',
            })
        self.state = 'approved'

    #@api.one
    def create_leave_request(self):
        leave_allocations = self.env['hr.leave'].search([
            ['employee_id', '=', self.employee_id.id], ['holiday_status_id', '=', self.contract_id.annual_leave_policy.id], ['state', '=', 'validate'],
            ['type', '=', 'add']], order='allocation_date')
        if leave_allocations:
            allocation_date = leave_allocations[-1].allocation_date
        else:
            allocation_date = self.contract_id.adjusted_date
        vals = {
            'name': 'تسوية رصيد أجازة أوتوماتيك',
            'employee_id': self.employee_id.id,
            'allocation_date': allocation_date,
            'number_of_days': self.want_to_liquidate * -1,
            'system_created': True,
            'create_uid': self.env.user.id,
            'holiday_status_id': self.contract_id.annual_leave_policy.id,
            'allow_minus_value': True,
            'linked_leave_reconciliation_id': self.id,
            'type': 'add',
        }
        leave_allocation = self.env['hr.leave'].create(vals)
        leave_allocation.check_adjust_day()
        leave_allocation.holidays_validate()
        leave_allocation.set_approved_by()
        self.linked_leave_allocation_id = leave_allocation.id

    #@api.multi
    def return_action(self, res_model, name='Attention !!', domain=[], context={}, ):
        return {
            'domain': domain,
            'name': _(name),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': res_model,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }

    #@api.one
    def refresh_data(self):
        self.refresh_get_leave_to_reconcile_ids()
        self.refresh_get_air_ticket_to_reconcile_ids()

    #@api.one
    @api.onchange('employee_id', 'type')
    def get_air_ticket_to_reconcile_ids(self):
        last_pay_amount = {}
        for line in self.air_ticket_to_reconcile_ids:
            last_pay_amount[line.air_ticket_id.id] = line.pay_to_employee
        domain = [['employee_id', '=', self.employee_id.id], ['state', '=', 'approved'], ['i_want_to', '=', 'Cash'], ['company_share', '>', 0],
                   ['request_reason', '=', 'leave'], ['contract_type_equal_leave_type', '=', False]]
        air_ticket_requests = self.env['air.ticket.request'].search(domain)
        air_ticket_to_reconcile = [(5,)]
        for air_ticket_request in air_ticket_requests:
            vals = {'air_ticket_id': air_ticket_request.id}
            if last_pay_amount.get(air_ticket_request.id, False):
                vals['pay_to_employee'] = last_pay_amount.get(air_ticket_request.id)
            air_ticket_to_reconcile.append((0, False, vals))
        self.air_ticket_to_reconcile_ids = air_ticket_to_reconcile
        self.air_ticket_to_reconcile_ids.update_air_ticket_data()

    def refresh_get_air_ticket_to_reconcile_ids(self):
        last_pay_amount = {}
        for line in self.air_ticket_to_reconcile_ids:
            last_pay_amount[line.air_ticket_id.id] = line.pay_to_employee
        domain = [['employee_id', '=', self.employee_id.id], ['state', '=', 'approved'], ['i_want_to', '=', 'Cash'], ['company_share', '>', 0],
                  ['request_reason', '=', 'leave'], ['contract_type_equal_leave_type', '=', False]]
        air_ticket_requests = self.env['air.ticket.request'].search(domain)
        air_ticket_to_reconcile = [(5,)]
        vals_list = []
        for air_ticket_request in air_ticket_requests:
            vals = {'air_ticket_id': air_ticket_request.id}
            if last_pay_amount.get(air_ticket_request.id, False):
                vals['pay_to_employee'] = last_pay_amount.get(air_ticket_request.id)
            vals_list.append((0, False, vals))
        self.air_ticket_to_reconcile_ids = air_ticket_to_reconcile
        self.write({'air_ticket_to_reconcile_ids': vals_list})
        self.air_ticket_to_reconcile_ids.update_air_ticket_data()

    @api.onchange('type', 'employee_id')
    def get_leave_to_reconcile_ids(self):
        last_pay_amount = {}
        for line in self.leave_to_reconcile_ids:
            last_pay_amount[line.leave_request_id.id] = line.pay_to_employee
        leave_to_reconcile_ids = [(5,)]
        if self.type in ['reconciliation', 'both']:
            domain = [['type', '=', 'remove'], ['employee_id', '=', self.employee_id.id], ['state', '=', 'validate'], ['request_reason', '=', 'annual'],
                      ['leave_reconciliation_amount', '!=', 0], ['remaining_amount', '!=', 0], ['leave_fully_reconciled', '!=', True]]
            leaves = self.env['hr.leave'].search(domain)
            for leave in leaves:
                if leave.holiday_status_id.reconciliation_method == "Stop payslip during leave and use leave reconciliation":
                    vals = {'leave_request_id': leave.id}
                    if last_pay_amount.get(leave.id, False):
                        vals['pay_to_employee'] = last_pay_amount.get(leave.id, False)
                    leave_to_reconcile_ids.append((0, False, vals))
        self.leave_to_reconcile_ids = leave_to_reconcile_ids
        self.leave_to_reconcile_ids.update_leave_info()

    def refresh_get_leave_to_reconcile_ids(self):
        last_pay_amount = {}
        for line in self.leave_to_reconcile_ids:
            last_pay_amount[line.leave_request_id.id] = line.pay_to_employee
        leave_to_reconcile_ids = [(5,)]
        vals_list = []
        if self.type in ['reconciliation', 'both']:
            domain = [['type', '=', 'remove'], ['employee_id', '=', self.employee_id.id], ['state', '=', 'validate'], ['request_reason', '=', 'annual'],
                      ['leave_reconciliation_amount', '!=', 0], ['remaining_amount', '!=', 0], ['leave_fully_reconciled', '!=', True]]
            leaves = self.env['hr.leave'].search(domain)
            for leave in leaves:
                if leave.holiday_status_id.reconciliation_method == "Stop payslip during leave and use leave reconciliation":
                    vals = {'leave_request_id': leave.id}
                    if last_pay_amount.get(leave.id, False):
                        vals['pay_to_employee'] = last_pay_amount.get(leave.id, False)
                    vals_list.append((0, False, vals))
        self.leave_to_reconcile_ids = leave_to_reconcile_ids
        self.write({'leave_to_reconcile_ids': vals_list})
        self.leave_to_reconcile_ids.update_leave_info()

    #@api.one
    @api.depends('air_ticket_to_reconcile_ids')
    def get_plus_air_ticket_value(self):
        self.plus_air_ticket_value = sum([l.pay_to_employee for l in self.air_ticket_to_reconcile_ids])

    @api.constrains('want_to_liquidate')
    def check_want_to_liquidate(self):
        if self.want_to_liquidate < 0:
            raise ValidationError(_("I want to Liquidate can not be negative number !!"))

    @api.onchange('employee_id', 'reconcile_based_on', 'type', 'want_to_liquidate')
    def get_balance_liquidation_amount(self):
        balance = 0
        if self.employee_id.contract_id and self.reconcile_based_on and self.type in ['liquidation', 'both']:
            based_on_value = 0
            if self.reconcile_based_on == 'basic':
                based_on_value = self.contract_id.basic_salary
            if self.reconcile_based_on == 'basic_house':
                based_on_value = self.contract_id.basic_salary + self.contract_id.house_allowance_amount
            if self.reconcile_based_on == 'basic_house_transportation':
                based_on_value = self.contract_id.basic_salary + self.contract_id.house_allowance_amount + self.contract_id.transportation_allowance_amount
            if self.reconcile_based_on == 'basic_house_transportation_phone':
                based_on_value = self.contract_id.basic_salary + self.contract_id.house_allowance_amount + self.contract_id.transportation_allowance_amount + \
                                 self.contract_id.phone_allowance_amount
            if self.reconcile_based_on == 'total':
                based_on_value = self.contract_id.total
            balance = based_on_value / 30 * self.want_to_liquidate
        self.balance_liquidation_amount = balance

    @api.onchange('employee_id')
    def get_contract(self):
        self.contract_id = self.employee_id.contract_id

    @api.onchange('employee_id')
    def get_reconcile_based_on(self):
        reconciliation_based_on = self.employee_id.contract_id.annual_leave_policy.reconciliation_based_on
        reconcile_based_on = (reconciliation_based_on and self.type in ['reconciliation', 'both']) and reconciliation_based_on or False
        if reconcile_based_on:
            self.reconcile_based_on = reconcile_based_on

    @api.onchange('current_leave_balance', 'type')
    def set_want_to_liquidate_empty(self):
        if self.type not in ['liquidation', 'both'] or self.current_leave_balance == 0:
            self.want_to_liquidate = 0

    #@api.one
    @api.depends('employee_id', 'type')
    def get_current_leave_balance(self):
        self.current_leave_balance = self.employee_id.leaves_count_float if self.type in ['liquidation', 'both'] else 0

    #@api.one
    @api.depends('employee_id', 'leave_to_reconcile_ids')
    def _get_reconciliation_data(self):
        total_leave_reconciliation = 0
        total_previously_paid = 0
        total_remaining = 0
        total_pay_to_employee = 0
        total_remain_after_pay = 0
        for line in self.leave_to_reconcile_ids:
            total_leave_reconciliation += line.reconciliation_amount
            total_previously_paid += line.previously_paid
            total_remaining += line.remaining
            total_pay_to_employee += line.pay_to_employee
            total_remain_after_pay += line.remain_after_pay
        self.total_leave_reconciliation = total_leave_reconciliation
        self.total_previously_paid = total_previously_paid
        self.total_remaining = total_remaining
        self.total_pay_to_employee = total_pay_to_employee
        self.total_remain_after_pay = total_remain_after_pay

    #@api.one
    def copy(self):
        raise ValidationError(_("Duplicate disabled in this window !!"))

    #@api.one
    def unlink(self):
        if self.state != 'new':
            raise ValidationError("Not allowed !!\n\
                Not allowed to delete any leave reconciliation request if the status is not ( NEW).")
        return super(LeaveReconciliation, self).unlink()

    @api.model
    def create(self, vals):
        res = super(LeaveReconciliation, self).create(vals)
        res.code = self.env['ir.sequence'].next_by_code(self._name)
        return res


class LeaveReconcileLine(models.Model):
    _name = "leave.reconcile.line"

    reconciliation_id = fields.Many2one('hr.leave.reconciliation', 'Leave reconciliation')
    leave_request_id = fields.Many2one('hr.leave', 'Leave request')
    reconciliation_amount = fields.Float('Reconciliation amount')
    previously_paid = fields.Float('Previously  Paid')
    remaining = fields.Float('Remaining')
    pay_to_employee = fields.Float('Pay to employee')
    remain_after_pay = fields.Float('Remaining after payment', compute="get_remain_after_pay")
    # Leave Info
    desc = fields.Char('Description')
    holiday_status_id = fields.Many2one('hr.leave.type', 'Leave type')
    date_from = fields.Datetime('date from')
    date_to = fields.Datetime('date to')
    number_of_days = fields.Float('Number of days')
    last_working_day = fields.Date('Last working days')
    air_ticket_id = fields.Many2one('air.ticket.request', 'Linked Air ticket')

    #@api.one
    @api.depends('remaining', 'pay_to_employee')
    def get_remain_after_pay(self):
        self.remain_after_pay = self.remaining - self.pay_to_employee

    #@api.one
    def update_leave_info(self):
        self.desc = self.leave_request_id.name
        self.holiday_status_id = self.leave_request_id.holiday_status_id
        self.date_from = self.leave_request_id.date_from
        self.date_to = self.leave_request_id.date_to
        self.number_of_days = self.leave_request_id.number_of_days
        self.last_working_day = self.leave_request_id.last_working_day
        self.air_ticket_id = self.leave_request_id.air_ticket_id
        self.reconciliation_amount = self.leave_request_id.leave_reconciliation_amount
        self.previously_paid = self.leave_request_id.paid_amount
        self.remaining = self.pay_to_employee = self.leave_request_id.remaining_amount


class AirTicketReconcileLine(models.Model):
    _name = "air.ticket.reconcile.line"

    reconciliation_id = fields.Many2one('hr.leave.reconciliation', 'Leave reconciliation')
    pay_to_employee = fields.Float('pay to employee')
    air_ticket_id = fields.Many2one('air.ticket.request', 'Air ticket')
    # Air tickket Info
    air_ticket_code = fields.Char('Code')
    description = fields.Char('description')
    request_reason = fields.Selection([('leave', 'leave'),
                                       ('Deputation / business trip', 'Deputation / business trip'),
                                       ('Final exit', 'Final exit'),
                                       ('Other', 'Other')], 'Air Ticket request reason')
    air_ticket_type_id = fields.Many2one('air.ticket.type', 'Air ticket type')
    leave_request_id = fields.Many2one('hr.leave', 'Leave Request')
    ticket_total_price = fields.Float('Air ticket total price')
    company_share = fields.Float('Company share')
    employee_share = fields.Float('Employee share')
    payment_time = fields.Selection([
        ('now', 'Pay Now'),
        ('with_reconciliation', 'Pay with Leave reconciliation'),
    ], string='Payment time')

    #@api.one
    def update_air_ticket_data(self):
        self.air_ticket_code = self.air_ticket_id.name
        self.description = self.air_ticket_id.description
        self.request_reason = self.air_ticket_id.request_reason
        self.air_ticket_type_id = self.air_ticket_id.air_ticket_type
        self.leave_request_id = self.air_ticket_id.leave_request
        self.ticket_total_price = self.air_ticket_id.ticket_total_price
        self.company_share = self.air_ticket_id.company_share
        self.employee_share = self.air_ticket_id.employee_share
        self.payment_time = self.air_ticket_id.payment_time


class LeaveReconciliationAttachement(models.Model):
    _name = "leave.reconciliation.attachment"

    source_id = fields.Many2one('hr.leave.reconciliation', 'Leave reconciliation')
    file = fields.Binary('File')
    name = fields.Char('Description')
    note = fields.Char('Notes')


class ValidatePayToEmployee(models.TransientModel):
    _name = "validate.pay.employee"

    type = fields.Selection([
        ('leave_to_reconcile', 'leave_to_reconcile'),
        ('air_ticket_to_reconcile', 'air_ticket_to_reconcile'),
        ('accept_pay_less_company_share_air_ticket', 'accept_pay_less_company_share_air_ticket'),
        ('accept_pay_more_company_share_air_ticket', 'accept_pay_more_company_share_air_ticket'),
    ])
    reconciliation_id = fields.Many2one('hr.leave.reconciliation')
    pay_to_employee = fields.Float('Pat to employee')
    desc = fields.Char('Desc')
    remaining = fields.Float('remaining')
    air_ticket_id = fields.Many2one('air.ticket.request')

    #@api.one
    def action_accept(self):
        if self.type == 'leave_to_reconcile':
            ctx = dict(self._context.copy(), accept_pay_employee=True)
        if self.type == 'air_ticket_to_reconcile':
            ctx = dict(self._context.copy(), air_ticket_to_reconcile=True)
        if self.type == 'accept_pay_less_company_share_air_ticket':
            ctx = dict(self._context.copy(), accept_pay_less_company_share_air_ticket=True)
        if self.type == 'accept_pay_more_company_share_air_ticket':
            ctx = dict(self._context.copy(), accept_pay_more_company_share_air_ticket=True)
        self.with_context(ctx).reconciliation_id.action_approve()
