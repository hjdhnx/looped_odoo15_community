# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from datetime import timedelta
import calendar
from dateutil.relativedelta import relativedelta
from odoo import tools
import math
import pytz
from dateutil import tz
import os


class hr_holidays(models.Model):
    _name = "hr.leave"
    _inherit = ["hr.leave", "salary.details"]
    _order = "id desc"


    holiday_status_id = fields.Many2one("hr.leave.type", "Leave Type", required=True, readonly=True,
                                        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, domain=[('state', 'in', ['Approved'])])
    holiday_status_type = fields.Selection(related='holiday_status_id.type')
    reconciliation_method = fields.Selection(related='holiday_status_id.reconciliation_method')
    allow_minus_value = fields.Boolean('Allow Minus Value')
    contract_id = fields.Many2one('hr.contract', string=_('Contract'), compute="_compute_contract", readonly=True, store=True)
    annual_leave_policy = fields.Many2one('hr.leave.type', string='Annual Leave Policy', related="contract_id.annual_leave_policy")
    allocation_date = fields.Date('Allocation Date')
    system_created = fields.Boolean('Created By The System', readonly=True)
    approved_by = fields.Many2one('res.users', string="Approved By", readonly=True)
    request_reason = fields.Selection([
        ('annual', 'annual leave'),
        ('non-annual', 'Non-annual leave'),
    ], string='Leave request reason')
    current_balance = fields.Integer('Current balance', compute='get_current_balance',store=True)
    current_balance_ = fields.Float('Current balance')
    remaining_balance = fields.Integer('Remaining balance', compute='get_remaining_balance',store=True)
    nationality_type = fields.Selection(related='employee_id.nationality_type')
    religion = fields.Selection(related='employee_id.religion')
    marital = fields.Selection(related='employee_id.marital')
    gender = fields.Selection(related='employee_id.gender')
    last_working_day = fields.Date('last working day', compute='compute_last_working_day')
    last_working_week_day = fields.Char('Last Working week day', compute='get_date_day')
    expected_working_day = fields.Date('Expected working day', compute='compute_expected_working_day')
    expected_working_week_day = fields.Char('Expected working week day', compute='get_date_day')
    reconciliation_based_on = fields.Selection([
        ('basic', 'Basic Salary'),
    ], string='Leave Reconciliation based on', default='basic')
    basic_salary = fields.Float('Basic salary')
    trial_wage = fields.Float('Trial Basic salary')
    trial_total_salary = fields.Float('Total')
    total_salary = fields.Float('Total')
    leave_reconciliation_amount = fields.Float('Leave Reconciliation amount', compute='get_leave_reconciliation_amount', store=True)
    paid_amount = fields.Float('Paid amount', compute='_compute_paid_amount')
    remaining_amount = fields.Float('Remaining amount', compute='get_remaining_amount')
    leave_fully_reconciled = fields.Boolean('Leave Fully Reconciled', compute='get_remaining_amount', store=True)
    holiday_history_ids = fields.Many2many('hr.leave', 'rel_leave_history', 'leave_id', 'history_id', string='Leave history')
    linked_exit_renry_id = fields.Many2one('hr.exit.entry.request', 'Linked exit and Re-entry')
    attachment_ids = fields.One2many('leave.attachment', 'leave_request_id', 'Attachments')
    # developer mode fields (Employee INfo)
    iqama_id = fields.Char('Iqama number', compute='get_employee_info', multi=True)
    iqama_id_ = fields.Char('Iqama number')
    iqama_expiry_date = fields.Date('Iqama Expiry date', compute='get_employee_info', multi=True)
    iqama_expiry_date_ = fields.Date('Iqama Expiry date')
    passport_no = fields.Char('Passport Number', compute='get_employee_info', multi=True)
    passport_no_ = fields.Char('Passport Number')
    passport_expiry_date = fields.Date('Passport expiry date', compute='get_employee_info', multi=True)
    passport_expiry_date_ = fields.Date('Passport expiry date')
    note = fields.Html('Notes')
    # Smart buttons
    count_air_ticket_requests = fields.Float('Number of air tickets', compute='get_count_smart_buttons', multi=True)
    air_ticket_request_ids = fields.One2many('air.ticket.request', 'leave_request', 'air ticket requests')
    count_exit_rentry_requests = fields.Float('Number of Exit and Re-entry', compute='get_count_smart_buttons', multi=True)
    exit_rentry_request_ids = fields.One2many('hr.exit.entry.request', 'leave_request_id', 'Exit and Re-entry requests')
    leave_requests_id = fields.Many2one('hr.leave')
    old_leave_requests_ids = fields.One2many('hr.leave', 'leave_requests_id', 'Old leave requests', compute='get_old_leave_requests')
    count_old_leave_requests = fields.Integer('Number of old leave requests', compute='get_count_smart_buttons', multi=True)
    old_similar_leave_requests_ids = fields.One2many('hr.leave', 'leave_requests_id', 'Similar leave requests', compute='get_similar_leave_requests')
    count_similar_leave_requests = fields.Integer('Number of old leave requests', compute='get_count_smart_buttons', multi=True)
    linked_leave_reconciliation_id = fields.Many2one('hr.leave.reconciliation', 'Linked Leave reconciliation')
    date_from_day = fields.Char('Date From Day', compute='get_date_day')
    date_to_day = fields.Char('Date To Day', compute='get_date_day')
    leave_extended = fields.Boolean('Leave Extended')
    leave_request_extend_id = fields.Many2one('hr.leave', 'leave request to extend this leave')
    original_leave_request_id = fields.Many2one('hr.leave', 'Original Leave request')
    return_from_leave = fields.Many2one('effective.notice', 'Return from leave')
    return_from_leave_date = fields.Date('Return from leave date', related="return_from_leave.start_work", )
    button_extend_invisible = fields.Boolean('button extend invisible', compute='get_button_extend_invisible')
    early_return_from_leave = fields.Many2one('effective.notice', 'Early Return from leave')
    late_return_from_leave = fields.Many2one('effective.notice', 'Late Return from leave')
    count_reconciliations = fields.Integer('Number of old leave requests', compute='get_count_smart_buttons', multi=True)
    adjusted_date = fields.Date('Adjusted Date', related='contract_id.adjusted_date')
    reconciliation_paid_line_ids = fields.One2many('leave.reconciliation.paid.line', 'request_id', 'Paid Amounts')
    by_eos = fields.Boolean('Through EOS')
    start_allocation_after = fields.Integer(related="holiday_status_id.start_allocation_after",string="Start Automatic Allocation After (months)")
    non_annual_frequency = fields.Selection(related="holiday_status_id.non_annual_frequency")
    duration_in_leave_request = fields.Selection(related="holiday_status_id.duration_in_leave_request")
    type = fields.Selection([('remove','Leave Request'),('add','Allocation Request')],
     'Request Type', required=True, readonly=True,default='remove'
    )
    employee_user_id = fields.Many2one('res.users',related="employee_id.user_id",store=True)

    def action_approve(self):
        """
        incase no attachment if holiday stautes attachment true then prevent confirm
        """
        for rec in self:
            if rec.holiday_status_id.is_required_attachment and not len(rec.attachment_ids.ids):
                raise ValidationError(_("Sorry! , you must atlease upload on attachment to be able to approve"))
        res = super(hr_holidays,self).action_approve()
        return res


    @api.constrains('state','employee_id','attachment_ids')
    def check_attachment(self):
        for rec in self:
            if rec.holiday_status_id.is_required_attachment and not len(rec.attachment_ids.ids):
                raise ValidationError(_("Sorry! , you must atlease upload on attachment to be able to approve"))
    
    @api.constrains('request_reason','holiday_status_id','employee_id','date_from','date_to')
    def check_non_annual_frequency(self):
        for rec in self:
            
            if rec.holiday_status_id.non_annual_frequency:
                non_annual_frequency = rec.holiday_status_id.non_annual_frequency
                if non_annual_frequency == 'contract':
                    prev_leaves = self.env['hr.leave'].search(
                        [
                            ('id','!=',rec.id),
                            ('holiday_status_id','=',rec.holiday_status_id.id),
                            ('contract_id','=',rec.contract_id.id),
                            ('state','=','validate'),
                        ]
                            )
                    if prev_leaves:
                        raise ValidationError(_("Sorry! , you request this leave before and this leave policy is one time per contract"))
    

                elif non_annual_frequency == 'financial_year':
                    start_f = datetime.strptime((str(rec.date_from.year)+"-01-01"), "%Y-%m-%d").date()
                    end_f = datetime.strptime((str(rec.date_from.year)+"-12-31"), "%Y-%m-%d").date()
                    prev_leaves = self.env['hr.leave'].search(
                        [
                            ('id','!=',rec.id),
                            ('holiday_status_id','=',rec.holiday_status_id.id),
                            ('date_from','>=',start_f),
                            ('date_to','<=',end_f),
                            ('state','=','validate'),
                        ]
                            )
                    if prev_leaves:
                        raise ValidationError(_("Sorry! , you request this leave before and this leave policy is one time per Financial Year"))
    
                    
                elif non_annual_frequency == 'contractual_year' and rec.contract_id and rec.contract_id and rec.contract_id.first_contract_date:
                    start_f = rec.contract_id.first_contract_date #datetime.strptime((str(rec.date_from.year)+"-01-01"), "%Y-%m-%d").date()
                    end_f = start_f + relativedelta(years=1)#datetime.strptime((str(rec.date_from.year)+"-12-31"), "%Y-%m-%d").date()
                    prev_leaves = self.env['hr.leave'].search(
                        [
                            ('id','!=',rec.id),
                            ('holiday_status_id','=',rec.holiday_status_id.id),
                            ('date_from','>=',start_f),
                            ('date_to','<=',end_f),
                            ('state','=','validate'),
                        ]
                            )
                    if prev_leaves:
                        raise ValidationError(_("Sorry! , you request this leave before and this leave policy is one time per Contract Year"))
    
                    
                elif non_annual_frequency == 'one_time':
                    prev_leaves = self.env['hr.leave'].search(
                        [
                            ('id','!=',rec.id),
                            ('holiday_status_id','=',rec.holiday_status_id.id),
                            ('state','=','validate'),
                        ]
                            )
                    if prev_leaves:
                        raise ValidationError(_("Sorry! , you request this leave before and this leave policy is one time per live"))
    
                return
    @api.constrains('request_reason','date_from','date_to','employee_id')
    def check_allocation_after(self):
        """
        if leave type have allocation after then check no employee can request leave type
        unless after alocation months from contract aleave start
        """
        for rec in self:
            if not rec.contract_id:
                raise ValidationError(_("Sorry! , please define Contract for Employee"))
        
            if rec.start_allocation_after and rec.date_from:
                leave_after_date = rec.contract_id.leaves_calc_on + relativedelta(months=rec.start_allocation_after)
                if leave_after_date > datetime.date(rec.date_from):
                    raise ValidationError(_("Sorry! , You can't Request This Leave Type Until " + str(leave_after_date)))
        

    # def action_confirm(self):
    #     """
    #     incase no attachment if holiday stautes attachment true then prevent confirm
    #     """
        
    #     res = super(hr_holidays,self).action_confirm()
    #     return res

    #@api.one
    @api.depends()
    def get_similar_leave_requests(self):
        self.old_similar_leave_requests_ids = False
        domain = [['employee_id', '=', self.employee_id.id], ['holiday_status_id', '=', self.holiday_status_id.id]]
        if not isinstance(self.id, models.NewId):
            domain.append(['id', '!=', self.id])
        self.old_similar_leave_requests_ids = [l.id for l in self.search(domain)]

    #@api.one
    @api.depends()
    def get_old_leave_requests(self):
        self.old_leave_requests_ids = False
        domain = [['employee_id', '=', self.employee_id.id], ['create_date', '<=', self.create_date]]
        if not isinstance(self.id, models.NewId):
            domain.append(['id', '!=', self.id])
        self.old_leave_requests_ids = [l.id for l in self.search(domain)]

    #@api.multi
    def open_similar_leave_requests(self):
        return {
            'domain': [['id', '=', [l.id for l in self.old_similar_leave_requests_ids]]],
            'name': _('Similar leave requests'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.leave',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    #@api.multi
    def open_old_leave_requests(self):
        return {
            'domain': [['id', '=', [l.id for l in self.old_leave_requests_ids]]],
            'name': _('Old leave requests'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.leave',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    #@api.multi
    def open_exit_rentry_requests(self):
        return {
            'domain': [['leave_request_id', '=', self.id]],
            'name': _('Exit and Re-entry'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.exit.entry.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    #@api.multi
    def open_air_ticket_requests(self):
        return {
            'domain': [['leave_request', '=', self.id]],
            'name': _('Air tickets'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'air.ticket.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    #@api.one
    @api.depends('air_ticket_request_ids', 'exit_rentry_request_ids')
    def get_count_smart_buttons(self):
        self.count_air_ticket_requests = len(self.air_ticket_request_ids)
        self.count_exit_rentry_requests = len(self.exit_rentry_request_ids)
        self.count_old_leave_requests = len(self.old_leave_requests_ids)
        self.count_similar_leave_requests = len(self.old_similar_leave_requests_ids)
        self.count_reconciliations = self.env['hr.leave.reconciliation'].search_count([('linked_leave_request_id', '=', self.id)])

    #@api.one
    @api.depends('date_from', 'date_to')
    def get_date_day(self):
        for rec in self:
            rec.date_to_day = rec.last_working_week_day = rec.expected_working_week_day = False
            rec.date_from_day = rec.last_working_week_day = rec.expected_working_week_day = False
            if rec.date_from:
                rec.date_from_day = rec.get_week_day(rec.date_from, 'datetime')
            if rec.date_to:
                rec.date_to_day = rec.get_week_day(rec.date_to, 'datetime')
            if rec.last_working_day:
                rec.last_working_week_day = rec.get_week_day(rec.last_working_day, 'date')
            if rec.expected_working_day:
                rec.expected_working_week_day = rec.get_week_day(rec.expected_working_day, 'date')

    def get_week_day(self, some_date, type):
        week_day = {'Monday': 'Monday / الإثنين', 'Tuesday': 'Tuesday / الثلاثاء', 'Wednesday': 'Wednesday / الأربعاء', 'Thursday': 'Thursday / الخميس',
                    'Friday': 'Friday / الجمعة', 'Saturday': 'Saturday / السبت', 'Sunday': 'Sunday / الأحَد'}
        if type == 'datetime':
            some_date_datetime = some_date
        elif type == 'date':
            some_date_datetime = some_date
        else:
            return ''
        some_date_day = calendar.day_name[some_date_datetime.weekday()]
        return week_day[some_date_day]

    #@api.one
    @api.depends('employee_id')
    def get_employee_info(self):
        self.iqama_id = self.iqama_id_ or self.employee_id.identification_id
        self.iqama_expiry_date = self.iqama_expiry_date_ or self.employee_id.iqama_expiry_date
        self.passport_no = self.passport_no_ or self.employee_id.passport_id
        self.passport_expiry_date = self.passport_expiry_date_ or self.employee_id.passport_expiry_date

    #@api.one
    @api.depends('leave_reconciliation_amount', 'paid_amount')
    def get_remaining_amount(self):
        for rec in self:
            remaining_amount = rec.leave_reconciliation_amount - rec.paid_amount
            leave_fully_reconciled = False
            if remaining_amount <= 0:
                leave_fully_reconciled = True
            rec.remaining_amount = remaining_amount
            rec.leave_fully_reconciled = leave_fully_reconciled

    @api.constrains('paid_amount')
    def check_paid_amount(self):
        for rec in self:
            if rec.paid_amount < 0:
                raise ValidationError(_("Paid amount can not be less that zero"))

    #@api.one
    def _compute_paid_amount(self):
        for rec in self:
            rec.paid_amount = sum(l.amount for l in rec.reconciliation_paid_line_ids)

    #@api.one
    @api.depends('contract_id', 'number_of_days', 'request_reason', 'reconciliation_based_on', 'holiday_status_id')
    def get_leave_reconciliation_amount(self):
        for rec in self:
            based_on_value = 0
            if rec.holiday_status_id.reconciliation_method == 'Stop payslip during leave and use leave reconciliation':
                if rec.request_reason == 'annual' and rec.contract_id and rec.holiday_status_type == 'Annual Leave':
                    if rec.reconciliation_based_on == 'basic':
                        based_on_value = rec.basic_salary
                rec.leave_reconciliation_amount = (based_on_value / 30) * (rec.number_of_days)
            else:
                rec.leave_reconciliation_amount = 0

    #@api.one
    #need mig
    # @api.constrains('contract_id', 'annual_leave_policy')
    # def check_contract_and_annual_leave_policy(self):
    #     for rec in self:
    #         if (not rec.contract_id or not rec.annual_leave_policy):
    #             raise ValidationError(_("Configuration error!\n\
    #                 Your system couldn’t find an active contract or the annual leave policy for the employee which you selected."))

    @api.onchange('holiday_status_id')
    def onchange_leave_type(self):
        reconciliation_based_on = False
        if self.holiday_status_id and self.holiday_status_id.reconciliation_based_on:
            reconciliation_based_on = self.holiday_status_id.reconciliation_based_on
        self.reconciliation_based_on = reconciliation_based_on

    @api.onchange('employee_id', 'holiday_status_id')
    def get_leave_history(self):
        # and self.type == 'remove'
        if self.employee_id and self.holiday_status_id :
            #  ['type', '=', 'remove']
            history = self.search([['employee_id', '=', self.employee_id.id], ['holiday_status_id', '=', self.holiday_status_id.id],])
            self.holiday_history_ids = [(6, False, [h.id for h in history])]
        else:
            self.holiday_history_ids = [(5,)]

    @api.onchange('employee_id', 'contract_id')
    def reset_leave_type(self):
        self.holiday_status_id = False




    @api.onchange('employee_id', 'contract_id','annual_leave_policy','request_reason')
    def set_leave_type(self):
        for rec in self:
            rec.holiday_status_id = False
            if rec.employee_id and rec.contract_id and rec.annual_leave_policy and rec.request_reason == 'annual':
                rec.holiday_status_id = rec.annual_leave_policy.id


    @api.onchange('contract_id', 'request_reason', 'employee_id', 'holiday_status_id', 'holiday_status_type')
    def get_salary_allowances(self):
        self.trial_house_allowance_type = False
        self.trial_house_allowance = False
        self.trial_house_allowance_amount = False
        self.trial_transportation_allowance_type = False
        self.trial_transportation_allowance = False
        self.trial_transportation_allowance_amount = False
        self.trial_phone_allowance_type = False
        self.trial_phone_allowance = False
        self.trial_phone_allowance_amount = False
        self.trial_insurance = False
        self.trial_commission = False
        self.trial_other_allowance = False
        self.trial_other_allowance_name = False
        self.house_allowance_type = False
        self.house_allowance = False
        self.house_allowance_amount = False
        self.transportation_allowance_type = False
        self.transportation_allowance = False
        self.transportation_allowance_amount = False
        self.phone_allowance_type = False
        self.phone_allowance = False
        self.phone_allowance_amount = False
        self.insurance = False
        self.commission = False
        self.other_allowance = False
        self.other_allowance_name = False
        self.trial_wage = False
        self.basic_salary = False
        self.total_salary = False
        self.trial_total_salary = False
        if self.contract_id and self.request_reason == 'annual':
            self.basic_salary = self.contract_id.basic_salary
            self.trial_wage = self.contract_id.trial_wage
            self.update_allowances_from_(self.contract_id, self)
            self.total_salary = self.contract_id.total
            self.trial_total_salary = self.contract_id.trial_total

    @api.onchange('request_reason', 'employee_id')
    def get_leave_type(self):
        self.holiday_status_id = False
        if self.request_reason == 'annual':
            self.holiday_status_id = self.annual_leave_policy.id

    # @api.onchange('request_reason')
    # def onchange_request_reason(self):
    #     domain = [['state', 'in', ['Approved',]]]
    #     # self.type == 'remove' and
    #     if self.request_reason == 'non-annual':
    #         # marital
    #         # marital_state = []
    #         # if self.employee_id.marital:
    #         #     if self.employee_id.marital == 'single':
    #         #         marital_state = ['Single','']
    #         domain += [
    #          ['type', '=', 'Non Annual Leave'],
    #          ['nationality', 'in', ['All Nationalities', self.nationality_type]],
    #          ['religion','in',['All Religions',self.religion]],
    #          ['marital_status','in',['Both',self.marital]],
    #          ['who_request','in',['Both',self.gender]],
    #          ]
    #         # domain += [['type', '=', 'Non Annual Leave'],]
    #     return {'domain': {'holiday_status_id': domain}}

    #@api.one
    @api.depends('current_balance', 'number_of_days','date_from','date_to','current_balance')
    def get_remaining_balance(self):
        for rec in self:
            if rec.current_balance and rec.number_of_days:
                rec.remaining_balance = rec.current_balance - rec.number_of_days
            else:
                rec.remaining_balance = 0

    #@api.one
    def create_exit_rentry(self):
        vals = {
            'name': 'Exit Entry For %s' % (self.employee_id.name),
            'employee_id': self.employee_id.id,
            'reason': 'leave',
            'leave_request_id': self.id,
            'one_mutli': 'one',
            'state': 'new'
        }
        
        exit_rentry = self.env['hr.exit.entry.request'].create(vals)
        exit_rentry.onchange_leave_request_id()

    #@api.one
    def exit_and_rentry_validation(self):
        exit_rentry = self.env['hr.exit.entry.request'].search([['employee_id', '=', self.employee_id.id], ['state', '=', 'confirmed']],
                                                               order='expected_return_date desc')
        if not exit_rentry:
            self.create_exit_rentry()
        if exit_rentry:
            X = self.date_to
            Y = exit_rentry[0].expected_return_date
            if X > Y:
                self.create_exit_rentry()
            else:
                Z = self.date_from
                M = self.linked_exit_renry_id.expected_return_date
                if Z < M:
                    self.create_exit_rentry()
                else:
                    if exit_rentry[-1].one_mutli == 'one':
                        self.create_exit_rentry()
                    elif exit_rentry[-1].one_mutli == 'multi':
                        return {
                            'domain': "[]",
                            'name': _('Not Allowed'),
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'exit.rentry.validation',
                            'type': 'ir.actions.act_window',
                            'target': 'new',
                            'context': {
                                'default_leave_request_id': self.id,
                                'default_employee_id': self.employee_id.id,
                                'default_exit_rentry_id': exit_rentry[-1].id,
                                'default_validation_from': 'leave',
                            },
                        }
    def action_validate(self):
        res = super(hr_holidays, self).action_validate()
        for rec in self:
            rec.holidays_validate()

        return res
    #@api.one
    def holidays_validate(self):
        # if self.type == 'remove':
        if self.holiday_status_id.reconciliation_method == 'Stop payslip during leave and use leave reconciliation':
            domain = [
                ('date_from', '<=', self.date_to),
                ('date_to', '>=', self.date_from),
                ('employee_id', '=', self.employee_id.id),
                ('state', '!=', 'cancel'),
            ]
            conflict_payslips = self.env['hr.payslip'].search(domain)
            if conflict_payslips:
                message = _(
                    "Data Error !! \n Based on your configuration, the leave reconciliation method for ( %s ) is to Stop payslip during this leave and create leave reconciliation, when we reviewed old payslip for this employee, we found that there is old payslip for the same employee which conflict with this leave request !!! Kindly review your old payslip data. ") % self.holiday_status_id.name
                raise ValidationError(message)
        date_to = datetime.date(self.date_to)
        date_from = datetime.date(self.date_from)
        if self.employee_id.nationality_type != 'Saudi':
            
            if self.employee_id.nationality_type != 'Saudi' and not self.iqama_expiry_date:
                raise ValidationError(_("Data Error!\n\
                    Not allowed to approve this leave request, there is no Iqama / National ID expiry date for the selected employee."))
            elif date_to and not self.iqama_expiry_date > date_to:
                raise ValidationError(_("Data Error !!\n\
                    Not allowed to approve this leave request, Employee Iqama / National ID will expire before return from leave, kindly renew employee Iqama\
                    before approving this leave request."))
            if not self.passport_expiry_date:
                raise ValidationError(_("Data Error!\n\
                    Not allowed to approve this leave request, there is no  passport expiry date for the selected employee."))
            elif not self.passport_expiry_date > date_to:
                raise ValidationError(_("Data Error !!\n\
                    Not allowed to approve this leave request, Employee passport will expire before return from leave, kindly renew employee Iqama before approving\
                    this leave request."))
        if self.last_working_day > date_from:
            raise ValidationError(_("Date Error!\n\
                Last working date must be equal to or less than leave start date!."))
        if self.can_request_exit_rentry == 'yes': #or self.nationality_type != 'Saudi':
            self.exit_and_rentry_validation()
            # if not self.linked_exit_renry_id:
            #     if not self.air_ticket_id:
            #         5/0
            #         self.exit_and_rentry_validation()
            #     else:
            #         4/0
            #         if self.air_ticket_id.linked_exit_rentry_id:
            #             self.linked_exit_renry_id = self.air_ticket_id.linked_exit_rentry_id.id
            #         # else:
            #         #     self.exit_and_rentry_validation()
        if not self.last_working_day:
            raise ValidationError(_("Please select last working day."))
        if self.original_leave_request_id:
            self.original_leave_request_id.leave_extended = True
        self.current_balance_ = self.employee_id.leaves_count
        # Employee info
        self.iqama_id_ = self.employee_id.identification_id
        self.iqama_expiry_date_ = self.employee_id.iqama_expiry_date
        self.passport_no_ = self.employee_id.passport_id
        self.passport_expiry_date_ = self.employee_id.passport_expiry_date

        old_leave_requests = self.env['hr.leave'].search(
            [('state', '=', 'validate'), ('employee_id', '=', self.employee_id.id), ('leave_request_extend_id', '=', ''), ('return_from_leave', '=', '')])
        if old_leave_requests:
            raise ValidationError(_("Not allowed !!\n\
                Not allowed to approve this leave for this employee, our records indicated that this employee has old leave request, till now this employee didn’t return from this leave.\n To solve this issue, kindly create a return from a leave for this employee, then you can request for another leave."))

        # return super(hr_holidays, self).holidays_validate()

    #@api.one
    @api.depends('employee_id', 'request_reason', 'contract_id','date_from','date_to')
    def get_current_balance(self):
        # self.current_balance = self.current_balance_ or self.employee_id.leaves_count
        for rec in self:
            if rec.employee_id.all_allocation_count: #and rec.employee_id.leaves_count :
                rec.current_balance = rec.employee_id.all_allocation_count - rec.employee_id.leaves_count 
            else:
                rec.current_balance = 0
    #@api.one
    @api.depends('employee_id', 'request_reason', 'contract_id')
    def get_button_extend_invisible(self):
        button_timeout = False
        if self.date_to:
            button_end_date = self.date_to + timedelta(30)
            button_timeout = datetime.now() > button_end_date

        # self.state != "validate" or
        if button_timeout or self.leave_request_extend_id or self.env.context.get('popup') == True:
            self.button_extend_invisible = True
        else:
            self.button_extend_invisible = False

    #@api.multi
    def action_reconcile(self):
        custom_context = {
            "default_name": "Leave reconciliation",
            "default_employee_id": self.env.context.get("employee_id", False),
            "default_type": "both",
            "default_linked_leave_request_id": self.env.context.get("active_id", False),
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.reconciliation',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('mits_hr_leaves.hr_leave_reconciliation_form').id,
            'context': custom_context,
            'target': 'current',
        }

    #@api.multi
    def open_reconciles(self):
        return {
            'domain': [('linked_leave_request_id', '=', self.id)],
            'name': _('Leave reconciliations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.leave.reconciliation',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
    _sql_constraints = [
        ('date_check', "CHECK ( 1 == 1 )", "The number of days must be greater than 0."),
    ]

    #@api.one
    @api.constrains('employee_id')
    def _check_employee_id(self):
        contracts = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('active', '=', True)])
        if not len(contracts):
            raise exceptions.ValidationError("This employee has no active contract ,Please create a contract to the selecte d employee")
        if self.type == 'remove':
            old_leave_requests = self.env['hr.leave'].search(
                [('state', '=', 'validate'), ('employee_id', '=', self.employee_id.id), ('leave_request_extend_id', '=', ''), ('return_from_leave', '=', '')])
            if old_leave_requests:
                raise ValidationError(_("Not allowed !!\n\
                    Not allowed to request for another leave for this employee, our records indicated that this employee has old leave request, till now this employee didn’t return from this leave.\n To solve this issue, kindly create a return from a leave for this employee, or open the last leave request and extend this leave, "))

    #@api.one
    @api.depends('employee_id')
    def _compute_contract(self):
        for rec in self:
            contracts = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id), ('active', '=', True)])
            if len(contracts):
                rec.contract_id = contracts[0].id

    #@api.one
    @api.constrains('holiday_type')
    def _check_holiday_type(self):
        if self.holiday_type == 'category':
            raise exceptions.ValidationError("Couldn’t save, allocation based on employee tag still under development")


        
    #@api.one
    # @api.constrains('contract_id')
    # def _check_contract_id(self):
    #     for rec in self:
    #         if not rec.contract_id.adjusted_date:
    #             raise exceptions.ValidationError("Can’t save this allocation request because we couldn’t calculate adjusted date for employee contract.")

    #@api.one
    @api.constrains('holiday_status_id','date_from','date_to','employee_id')
    def _check_holiday_status_id(self):
        if self.holiday_status_id.type == "Annual Leave" and self.holiday_status_id != self.annual_leave_policy:
            raise exceptions.ValidationError(
                "Not allowed to assign this annual leave to this employee. Please review the annual leave policy at employee contract.")
        if self.holiday_status_id.limit and self.number_of_days > self.holiday_status_id.days_per_leave :
            raise exceptions.ValidationError(
                _("Not Allowed. Number of days requested ( %s ) is greater than the Maximum days per each leave request  (%s)") % (
                    self.number_of_days, self.holiday_status_id.days_per_leave))

        if self.number_of_days < 0 and not self.allow_minus_value:
            raise exceptions.ValidationError(
                "The number of days must be greater than 0. To allow minus values, you must click on allow minus quantities field.")
        
    
    # #@api.one
    # @api.constrains('number_of_days','date_from','date_to','employee_id')
    # def _check_number_of_days(self):
    #     # if not self.holiday_status_id.limit 
    #     if self.holiday_status_id.type != 'Annual Leave' and self.number_of_days > self.holiday_status_id.number_of_days: #and self.type == 'remove':
    #         raise exceptions.ValidationError(
    #             _("Not Allowed. Number of days requested ( %s ) is greater than the Maximum days per each leave request  (%s)") % (
    #                 self.number_of_days, self.holiday_status_id.number_of_days))

        

    #@api.multi
    def check_adjust_day(self):
        for record in self:
            if record.type == 'add' and record.holiday_status_id.type == "Annual Leave":
                adjusted_date = record.contract_id.adjusted_date
                allocation_date = record.allocation_date

                if adjusted_date.day != allocation_date.day and not self.by_eos:
                    raise exceptions.ValidationError(
                        "Attention!! We found that you configured your system give the employee a monthly annual leave balance at a certain day from each month\
                        , now you are trying to allocate leaves on a different day. We highly recommend to use a monthly base (except the termination cases or \
                        EOC cases)")

    #@api.multi
    def set_approved_by(self):
        for record in self:
            record.approved_by = self.env.uid

    # @api.v7
    def localize_dt(self, date, to_tz):
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz(to_tz)
        # utc = datetime.utcnow()
        utc = date
        # Tell the datetime object that it's in UTC time zone since
        # datetime objects are 'naive' by default
        utc = utc.replace(tzinfo=from_zone)
        # Convert time zone
        res = utc.astimezone(to_zone)
        return res.strftime('%Y-%m-%d %H:%M:%S')



    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days(self):
        for holiday in self:
            if holiday.date_from and holiday.date_to:
                #this section need check
                if holiday.duration_in_leave_request == 'no':
                    data = holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)
                    holiday.number_of_days = data['days']
                    if holiday.number_of_days:
                        holiday.number_of_days = holiday.number_of_days + 1
                    
                else:
                    diff_days =  (holiday.date_to - holiday.date_from ).days
                    holiday.number_of_days = diff_days + 1
            else:
                holiday.number_of_days = 0



    @api.model
    def get_user_tz(self):
        tz = self.env.user.tz
        return
    #need mig
    # def holidays_refuse(self, cr, uid, ids, context=None):
    #     obj_emp = self.pool.get('hr.employee')
    #     ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
    #     manager = ids2 and ids2[0] or False
    #     for holiday in self.browse(cr, uid, ids, context=context):
    #         if holiday.return_from_leave:
    #             raise exceptions.ValidationError(
    #                 "Not Allowed !! Not allowed to refuse / cancel this leave Request because there is a return from leave already linked with this leave request. If you have any special cases which requires to cancel this approved leave request, you can create a new leave allocation to increase employee balance.")
    #         if holiday.state == 'validate1':
    #             self.write(cr, uid, [holiday.id], {'state': 'refuse', 'manager_id': manager})
    #         else:
    #             self.write(cr, uid, [holiday.id], {'state': 'refuse', 'manager_id2': manager})
    #         if holiday.original_leave_request_id:
    #             holiday.original_leave_request_id.leave_extended = False
    #             holiday.original_leave_request_id.leave_request_extend_id = ''
    #         if holiday.leave_request_extend_id:
    #             raise exceptions.ValidationError(
    #                 "Not Allowed, There is a leave request to extend this leave, you must refuse or delete the leave request extension before refusing this leave.")
    #     self.holidays_cancel(cr, uid, ids, context=context)
    #     return True

    @api.model
    def create(self, vals):
        res = super(hr_holidays, self).create(vals)
        if res.original_leave_request_id:
            res.original_leave_request_id.leave_request_extend_id = res
        if self.env.context.get('return_from_leave', False):
            return_from_leave_id = self.env.context.get('return_from_leave', False)
            return_from_leave = self.env['effective.notice'].search([('id', '=', return_from_leave_id)])
            return_from_leave.hr_department_approval()
        return res

    #@api.one
    def unlink(self):
        if self.original_leave_request_id or self.leave_request_extend_id or self.leave_extended:
            raise ValidationError(_("Not allowed to delete this leave request because there is leave extension already linked with this leave."))
        if self.system_created:
            raise ValidationError(_(
                "Not allowed!! \n Not allowed to delete a record which is automatically created by the system, try to refuse or set to new.  Or create another leave allocation with a negative / Positive sign to reverse this allocation."))
        return super(hr_holidays, self).unlink()

    #@api.one
    @api.depends('employee_id', 'date_from')
    def compute_last_working_day(self):
        for rec in self:
            rec.last_working_day = False
            if rec.date_from and rec.employee_id:
                start_date = rec.date_from
                start_date_yesterday = start_date - timedelta(days=1)
                rec.last_working_day = rec.get_last_working_date(start_date_yesterday, rec.employee_id)

    def get_last_working_date(self, checked_date, employee_id):
        # //////////////  Check For Old Leave Request /////////////////////////////////////////////
        old_leave_requests = self.env['hr.leave'].search(
            [('state', '!=', 'refuse'), ('employee_id', '=', employee_id.id), ('date_from', '<=', checked_date.strftime('%Y-%m-%d %H:%M:%S')),
             ('date_to', '>=', checked_date.strftime('%Y-%m-%d %H:%M:%S'))])
        if old_leave_requests:
            for old_leave_request in old_leave_requests:
                leave_start_date = old_leave_request.date_from
                leave_start_date_yesterday = leave_start_date - timedelta(days=1)
                return self.get_last_working_date(leave_start_date_yesterday, employee_id)

        # //////////////  Check For Old Working schedule Days /////////////////////////////////////////////
        week_day = checked_date.weekday()
        contracts = self.env['hr.contract'].search([('employee_id', '=', employee_id.id), ('active', '=', True)])
        contract = contracts and contracts[0] or False
        day_on_working_days = 0
        if contract and contract.attendance_ids:
            for attendance_id in contract.attendance_ids:
                if week_day == int(attendance_id.dayofweek):
                    day_on_working_days = 1
            if not day_on_working_days:
                checked_date_yesterday = checked_date - timedelta(days=1)
                return self.get_last_working_date(checked_date_yesterday, employee_id)

        return checked_date

    #@api.one
    @api.depends('employee_id', 'date_to')
    def compute_expected_working_day(self):
        for rec in self:
            rec.expected_working_day = False
            if rec.date_to and rec.employee_id:
                end_date = rec.date_to
                end_date_tomorrow = end_date + timedelta(days=1)
                rec.expected_working_day = rec.get_expected_working_day(end_date_tomorrow, rec.employee_id)

    def get_expected_working_day(self, checked_date, employee_id):
        # //////////////  Check For Old Leave Request /////////////////////////////////////////////
        old_leave_requests = self.env['hr.leave'].search(
            [('state', '!=', 'refuse'), ('employee_id', '=', employee_id.id), ('date_from', '<=', checked_date.strftime('%Y-%m-%d %H:%M:%S')),
             ('date_to', '>=', checked_date.strftime('%Y-%m-%d %H:%M:%S'))])
        if old_leave_requests:
            for old_leave_request in old_leave_requests:
                leave_end_date = old_leave_request.date_to
                leave_end_date_tomorrow = leave_end_date + timedelta(days=1)
                return self.get_expected_working_day(leave_end_date_tomorrow, employee_id)

        # //////////////  Check For Old Working schedule Days /////////////////////////////////////////////
        week_day = checked_date.weekday()
        contracts = self.env['hr.contract'].search([('employee_id', '=', employee_id.id), ('active', '=', True)])
        contract = contracts and contracts[0] or False
        day_on_working_days = 0
        if contract and contract.attendance_ids:
            for attendance_id in contract.attendance_ids:
                if week_day == int(attendance_id.dayofweek):
                    day_on_working_days = 1
            if not day_on_working_days:
                checked_date_tomorrow = checked_date + timedelta(days=1)
                return self.get_expected_working_day(checked_date_tomorrow, employee_id)

        return checked_date

    # need mig
    # def onchange_type(self, cr, uid, ids, holiday_type, employee_id=False, context=None):
    #     return

