# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta
import time


class ExitEntryType(models.Model):
    _name = "hr.exit.entry.type"
    _inherit = "mail.thread"
    _description = "Exit and re-entry"
    _order = "id desc"

    code = fields.Char('Code')
    name = fields.Char('Description')
    min_months = fields.Integer('minimum months', default=2)
    min_charge = fields.Integer('Minimum charge', default=200)
    additional_month_cost = fields.Integer('Cost for each additional month', default=100)
    max_month = fields.Integer('Maximum month', default=6)
    max_charge = fields.Integer('maximum charge')
    min_months2 = fields.Integer('minimum months', default=2)
    min_charge2 = fields.Integer('minimum charge', default=500)
    additional_month_cost2 = fields.Integer('Cost for each additional month', default=200)
    max_month2 = fields.Integer('Maximum month', default=6)
    max_charge2 = fields.Integer('maximum charge')
    request_ids = fields.One2many('hr.exit.entry.request', 'exit_entry_type_id', 'Exit Re-entry requests')
    count_requests = fields.Integer('Number of requests', compute='get_count_requests')
    state = fields.Selection([
        ('new', 'New'),
        ('Confirmed', 'Confirm'),
    ], 'Status', default='new', track_visibility='onchange')
    loan_type_id = fields.Many2one('hr_loans.loan_advance', 'Loan type', help="when an employee request for exit and re-entry, if the company will pay instead of\
    employee, your system will automatically create a loan request using this loan type. ")

    @api.constrains('min_months', 'max_month', 'min_months2', 'max_month2')
    def check_min_max_month(self):
        if self.min_months > self.max_month:
            raise ValidationError(_("Maximum months must be greater than or equal to minimum months"))
        if self.min_months2 > self.max_month2:
            raise ValidationError(_("Maximum months must be greater than or equal to minimum months"))

    #@api.one
    def reset(self):
        self.state = 'new'

    #@api.one
    def confirm(self):
        self.state = 'Confirmed'

    #@api.multi
    def open_requests(self):
        return {
            'domain': [['exit_entry_type_id', '=', self.id]],
            'name': _('Exit and Re-entry Request'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.exit.entry.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_exit_entry_type_id': self.id},
        }

    #@api.one
    @api.depends()
    def get_count_requests(self):
        self.count_requests = len(self.request_ids) or 0

    @api.constrains('min_months', 'min_charge', 'additional_month_cost', 'min_months2', 'min_charge2', 'additional_month_cost2')
    def check_int_numbers(self):
        if self.min_months <= 0:
            raise ValidationError(_("Minimum Months must be greater than zero !!"))
        if self.min_charge <= 0:
            raise ValidationError(_("Minimum charge must be greater than zero !!"))
        if self.additional_month_cost <= 0:
            raise ValidationError(_("Cost for each additional month must be greater than zero !!"))
        if self.min_months2 <= 0:
            raise ValidationError(_("Minimum Months must be greater than zero !!"))
        if self.min_charge2 <= 0:
            raise ValidationError(_("Minimum charge must be greater than zero !!"))
        if self.additional_month_cost2 <= 0:
            raise ValidationError(_("Cost for each additional month must be greater than zero !!"))

    @api.model
    def create(self, vals):
        res = super(ExitEntryType, self).create(vals)
        res.code = self.env['ir.sequence'].next_by_code(self._name)
        return res


class ExitEntryRequest(models.Model):
    _name = "hr.exit.entry.request"
    _inherit = "mail.thread"
    _description = "Exit and Re-entry Request"
    _order = "id desc"

    state = fields.Selection([
        ('new', 'New'),
        ('confirmed', 'Confirmed'),
    ], string='Status', track_visibility='onchange', default='new')
    code = fields.Char('Code')
    name = fields.Char('Description')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    contract_id = fields.Many2one('hr.contract', 'Contract', compute='get_employee_info', multi=True)
    department_id = fields.Many2one('hr.department', 'Department', compute='get_employee_info', multi=True)
    iqama_no = fields.Char('Iqama number', compute='get_employee_info', multi=True)
    iqama_expiry_date = fields.Date('Iqama Expiry date', compute='get_employee_info', multi=True)
    passport = fields.Char('Passport', compute='get_employee_info', multi=True)
    passport_expiry_date = fields.Date('Passport expiry date', compute='get_employee_info', multi=True)
    passport_expiry_date_copy = fields.Date('Passport expiry date')
    passport_copy = fields.Char('Passport')
    iqama_expiry_date_copy = fields.Date('Iqama Expiry date')
    iqama_no_copy = fields.Char('Iqama number')
    department_copy_id = fields.Many2one('hr.department', 'Department')
    contract_copy_id = fields.Many2one('hr.contract', 'Contract')
    reason = fields.Selection([
        ('leave', 'Leave'),
        ('air_ticket', 'Air ticket'),
        ('trip', 'business trip / deputation'),
        ('final_exit', 'Final Exit'),
        ('other', 'Other'),
    ], string='Reason', )
    reason_desc = fields.Char('Reason description')
    leave_request_id = fields.Many2one('hr.leave', 'Leave request')
    exit_entry_type_id = fields.Many2one('hr.exit.entry.type', 'Exit and Re-entry Policy', related='employee_id.contract_id.exit_entry_type_id', store=True)
    linked_loan_request_id = fields.Many2one('loan.advance.request', 'Linked Loan request')
    one_mutli = fields.Selection([
        ('one', 'One time'),
        ('multi', 'Multiple'),
    ], string='One time / Multiple', default='one')
    min_months = fields.Integer('Minimum months', compute='get_type_info', multi=True)
    min_charge = fields.Integer('Minimum charge', compute='get_type_info', multi=True)
    additional_month_cost = fields.Integer('Cost for each additional month')
    duration_in_month = fields.Integer('Exit and Re-entry duration in months', default=2)
    cost = fields.Float('Exit and Re-entry cost', compute='get_cost')
    company_share = fields.Float('Company share')
    employee_share = fields.Float('Employee share', compute='get_employee_share')
    absheer = fields.Boolean('The employee will pay through ABSHEER')
    employee_payment_method = fields.Selection([
        ('company', 'The company will pay instead of employee + create a Loan'),
        ('cash', 'Cash & bank transfer'),
    ], string='Employee share payment method')
    expected_travel_date = fields.Date('Expected travel date')
    expected_return_date = fields.Date('Expected return date', compute='get_expected_return_date', store=True)
    attachment_ids = fields.One2many('exit.entry.attachment', 'source_id', 'Attachments')
    old_exit_entry_ids = fields.Many2many('hr.exit.entry.request', 'exit_entry_id', 'exit_entry2_id', 'rel_old_exit_entry', 'Old exit Re-entry')
    count_requests = fields.Integer('Number of old requests', compute='get_count_requests')
    count_leave_requests = fields.Integer('Number of Leave requests', compute='get_count_leave_requests')
    leave_request_ids = fields.One2many('hr.leave', 'linked_exit_renry_id', 'Leave Requests')
    air_ticket_request_id = fields.Many2one('air.ticket.request', 'Air Ticket Request')
    note = fields.Html('Notes')
    loan_type_id = fields.Many2one('hr_loans.loan_advance', 'Loan type', related='exit_entry_type_id.loan_type_id',
                             help="when an employee request for exit and re-entry, if the company will pay instead of employee, your system will automatically"
                                  " create a loan request using this loan type. ")

    can_request_exit_rentry = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Can request For Exit and R-entry')
    
    #@api.one
    @api.depends('expected_travel_date', 'duration_in_month')
    def get_expected_return_date(self):
        if self.expected_travel_date:
            expected_return_date = self.expected_travel_date + relativedelta(months=self.duration_in_month)
            
            self.expected_return_date = expected_return_date.strftime("%Y-%m-%d")

    @api.onchange('employee_id', 'reason')
    def onchange_employee_id(self):
        self.air_ticket_request_id = False

    # @api.onchange('expected_travel_date', 'duration_in_month')
    # def get_expected_return_date(self):
    #     if self.expected_travel_date:
    #         expected_return_date = datetime.strptime(self.expected_travel_date, "%Y-%m-%d") + relativedelta(months=self.duration_in_month)
    #         self.expected_return_date = expected_return_date.strftime("%Y-%m-%d")

    @api.constrains('iqama_expiry_date')
    def check_iqama_expiry(self):
        if not self.iqama_expiry_date:
            raise ValidationError(_("Kindly request from HR department to complete the employee data before creating Exit  and re-entry request.\n\
                            Iqama number - iqama expiry date"))

    @api.constrains('company_share', 'cost')
    def check_company_share(self):
        if self.company_share < 0:
            raise ValidationError(_("Not Allowed !!\n Company share can not be a minus value !! "))
        if self.company_share > self.cost:
            raise ValidationError(_("Data Error!!\n Company share cannot greater than total Exit  and re-entry cost."))

    @api.constrains('additional_month_cost')
    def check_additional_month_cost(self):
        if not self.additional_month_cost:
            raise ValidationError(_("Cost for each additional month can not be zero"))

    @api.constrains('duration_in_month')
    def check_duration_in_months(self):
        if not self.duration_in_month:
            raise ValidationError(_("Duration in months can not be zero"))

    @api.constrains('iqama_no', 'iqama_expiry_date', 'passport_expiry_date')
    def check_employee_info(self):
        if not (self.iqama_no and self.iqama_expiry_date and self.passport_expiry_date):
            raise ValidationError(_("Kindly complete the employee data before creating Exit  and re-entry\n\
            Iqama number - iqama expiry date - passport expiry date"))

    @api.constrains('reason')
    def check_reason(self):
        if self.reason not in ['leave', 'air_ticket', 'other']:
            raise ValidationError(_("Not allowed!!\n\
            Creating Exit  and re-entry for Business trip / deputation - Final Exit and other cases still under development."))

    @api.constrains('additional_month_cost')
    def check_additional_month_cost(self):
        for rec in self:
            if rec.additional_month_cost < 0:
                raise ValidationError(_("Data Error!\n\
                Cost for additional months must be greater than zero."))

    @api.constrains('exit_entry_type_id', 'one_mutli', 'duration_in_month')
    def check_duration_in_month(self):
        for rec in self:
            min_months = rec.exit_entry_type_id.min_months if rec.one_mutli == 'one' else rec.exit_entry_type_id.min_months2
            max_months = rec.exit_entry_type_id.max_months if rec.one_mutli == 'one' else rec.exit_entry_type_id.max_months2
            if not min_months <= rec.duration_in_month <= max_months:
                raise ValidationError(_("Data Error!!\n\
                Based on your configuration, the minimum months for Exit and Re-entry is ( %s ) months, Maximum months is ( XXXX ) months.\n\
                So, it is not allowed to request for Exit  and re-entry for ( %s ) months" % (min_months, max_months)))

    @api.constrains('duration_in_month')
    def check_duration_in_month(self):
        for rec in self:
            if not rec.duration_in_month:
                raise ValidationError(_("Data Error!\n\
                Exit and Re-entry duration in months must be greater than zero !"))

    @api.constrains('leave_request_id')
    def check_leave_request_id(self):
        for rec in self:
            if not rec.contract_id.exit_entry_type_id:
                raise ValidationError(_("Configuration Error! \n\
                We could not find any Exit and re-entry policy linked to the employee contract."))

    @api.constrains('contract_id')
    def check_contract(self):
        for rec in self:
            if not rec.contract_id:
                raise ValidationError(_("Not allowed! \n\
                    You are not allowed to request for Exit  and Re-entry for this employee, because he did not have an active contract."))

    #@api.one
    @api.depends('old_exit_entry_ids')
    def get_count_requests(self):
        for rec in self:
            rec.count_requests = len(rec.old_exit_entry_ids) or 0

    #@api.one
    @api.depends('leave_request_ids')
    def get_count_leave_requests(self):
        for rec in self:
            rec.count_requests = len(rec.old_exit_entry_ids) or 0

    #@api.multi
    def open_requests(self):
        return {
            'domain': [['id', 'in', [e.id for e in self.old_exit_entry_ids]]],
            'name': _('Exit and Re-entry Request'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.exit.entry.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_employee_id': self.employee_id.id},
        }

    #@api.multi
    def open_leave_requests(self):
        return {
            'domain': [['id', 'in', [e.id for e in self.leave_request_ids]]],
            'name': _('Leave Request'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.leave',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_employee_id': self.employee_id.id},
        }

    @api.onchange('employee_id')
    def get_old_exit_entry(self):
        for rec in self:
            rec.leave_request_id = False
            old_exit_entry_ids = [(5,)]
            if rec.employee_id:
                domain = [['employee_id', '=', rec.employee_id.id]]
                if not isinstance(rec.id, models.NewId):
                    domain.append(['id', '!=', rec.id])
                old_requests = rec.search(domain)
                if old_requests:
                    old_exit_entry_ids = [(6, False, [e.id for e in old_requests])]
            rec.old_exit_entry_ids = old_exit_entry_ids

    @api.onchange('leave_request_id')
    def onchange_leave_request_id(self):
        for rec in self:
            rec.expected_travel_date = False
            if rec.leave_request_id:
                date_from = rec.leave_request_id.date_from
                
                rec.expected_travel_date = (date_from + relativedelta(days=-1)).strftime("%Y-%m-%d")

    #@api.one
    @api.depends('cost', 'company_share')
    def get_employee_share(self):
        for rec in self:
            rec.employee_share = rec.cost - rec.company_share
            if rec.employee_share <= 0:
                rec.absheer = False

    #@api.one
    @api.onchange('min_months', 'duration_in_month', 'min_charge', 'additional_month_cost')
    def get_company_share(self):
        for rec in self:
            if rec.min_months >= rec.duration_in_month:
                rec.company_share = rec.min_charge
            else:
                diff = rec.duration_in_month - rec.min_months
                additional_cost = rec.additional_month_cost * diff
                rec.company_share = additional_cost + rec.min_charge

    #@api.one
    @api.depends('min_months', 'duration_in_month', 'min_charge', 'additional_month_cost')
    def get_cost(self):
        for rec in self:
            if rec.min_months >= rec.duration_in_month:
                rec.cost = rec.min_charge
            else:
                diff = rec.duration_in_month - rec.min_months
                additional_cost = rec.additional_month_cost * diff
                rec.cost = additional_cost + rec.min_charge

    @api.constrains('duration_in_month')
    def check_duration_in_month(self):
        for rec in self:
            if rec.duration_in_month < 0:
                raise ValidationError("Exit and Re-entry duration in months should be positive number")

    #@api.one
    @api.depends('employee_id', 'exit_entry_type_id', 'one_mutli')
    def get_type_info(self):
        for rec in self:
            rec.min_months = 0
            rec.min_charge = 0
            rec.additional_month_cost = 0
            if rec.exit_entry_type_id and rec.one_mutli:
                exit_entry_type_id = rec.exit_entry_type_id
                rec.min_months = exit_entry_type_id.min_months if rec.one_mutli == 'one' else exit_entry_type_id.min_months2
                rec.min_charge = exit_entry_type_id.min_charge if rec.one_mutli == 'one' else exit_entry_type_id.min_charge2
                rec.additional_month_cost = exit_entry_type_id.additional_month_cost if rec.one_mutli == 'one' else exit_entry_type_id.additional_month_cost2

    #@api.one
    @api.depends('employee_id')
    def get_employee_info(self):
        for rec in self:
            rec.contract_id = rec.contract_copy_id or rec.employee_id.contract_id.id
            rec.department_id = rec.department_copy_id or rec.employee_id.department_id
            rec.iqama_no = rec.iqama_no_copy or rec.employee_id.identification_id
            rec.iqama_expiry_date = rec.iqama_expiry_date_copy or rec.employee_id.iqama_expiry_date
            rec.passport = rec.passport_copy or rec.employee_id.passport_id
            rec.passport_expiry_date = rec.passport_expiry_date_copy or rec.employee_id.passport_expiry_date

    #@api.one
    def confirm(self):
        if not self.iqama_expiry_date:
            raise ValidationError(_("Data Error!\n\
                Not allowed to approve this leave request, there is no Iqama / National ID expiry date for the selected employee."))
        elif self.expected_return_date >= self.iqama_expiry_date:
            raise ValidationError(_("Data Error !!\n\
                Not allowed to approve this leave request, Employee Iqama / National ID will expire before return back, kindly renew employee Iqama before\
                approving this exit and Re-entry."))
        if not self.passport_expiry_date:
            raise ValidationError(_("Data Error!\n\
                Not allowed to approve this leave request, there is no  passport expiry date for the selected employee."))
        elif self.expected_return_date >= self.passport_expiry_date:
            raise ValidationError(_("Data Error !!\n\
                Not allowed to approve this leave request, Employee passport will expire before return from leave, kindly renew employee Iqama before approving\
                this leave request."))
        if self.reason == 'leave':
            if self.leave_request_id.linked_exit_renry_id and self.leave_request_id.linked_exit_renry_id.id != self.id:
                raise ValidationError(_("Not Allowed !! \n\
                        Not allowed to confirm this Exit and Re-entry request, we found that the leave request is already linked with another exit and re-entry…\n\
                        if you want to force your system to accept this exit and Re-entry request, kindly edit this request and select that the reason is (\
                        other ) and write a note to illustrate the reason ..."))
            if self.leave_request_id.air_ticket_id.linked_exit_rentry_id and self.leave_request_id.air_ticket_id.linked_exit_rentry_id.id != self.id:
                raise ValidationError(_("Not Allowed !! \n\
                    Not allowed to confirm this Exit and Re-entry request, we found that you request for this exit and re-entry for a leave, the leave request\
                    which you selected is already linked with Air ticket request, you already created another exit and re-entry for this air ticket, So it is\
                    not logic to create 2 exit and Re-entry for the same leave and it’s air ticket…\n\n\
                    if you want to force your system to accept this exit and Re-entry request, kindly edit this request and select that the reason is ( other )\
                    and write a note to illustrate the reasons ..."))
            # if not self.leave_request_id.air_ticket_id.linked_exit_rentry_id:
            #     self.leave_request_id.air_ticket_id.linked_exit_rentry_id = self.id
            if not self.leave_request_id.linked_exit_renry_id:
                self.leave_request_id.linked_exit_renry_id = self.id
        if self.employee_share > 0 and not self.absheer:
            if not self.loan_type_id and not self.exit_entry_type_id.loan_type_id:
                raise ValidationError(_("Not allowed!!\n\
                    You can not approve this exit and re-entry request, you told your system that the company will pay instead of employee + create a loan.\n\
                    unfortunately, we could not find a loan type linked with the Exit and Re-entry Policy which you select."))
            self.create_loan_request()
        exit_rentry_validation = self._context.get('exit_rentry_validation', False)
        if not exit_rentry_validation:
            action = self.exit_rentry_validation()
            if action: return action
        travel_date = self.expected_travel_date
        travel_date += relativedelta(months=self.duration_in_month)
        
        if self.iqama_expiry_date <= travel_date:
            raise ValidationError(_("Attention!\n\
            Not Allowed to Confirm this Exit and Re-entry because the Iqama will be expired before employee return back to Saudia Arabia"))
        d = self.expected_travel_date
        if self.reason == 'leave' and datetime(d.year, d.month, d.day) >= self.leave_request_id.date_to:
            raise ValidationError(_("Data Error!\n\
            Leave start date is ( %s ) leave end date is ( %s ) you told your system that the expected travel date is ( %s )\n\
            It is not logic that the Exist and re-entry will start after the leave end date." % (
                self.leave_request_id.date_from, self.leave_request_id.date_to, self.expected_travel_date)))
        self.contract_copy_id = self.employee_id.contract_id.id
        self.department_copy_id = self.employee_id.department_id
        self.iqama_no_copy = self.employee_id.identification_id
        self.iqama_expiry_date_copy = self.employee_id.iqama_expiry_date
        self.passport_copy = self.employee_id.passport_id
        self.passport_expiry_date_copy = self.employee_id.passport_expiry_date
        self.state = 'confirmed'

    #@api.one
    def create_loan_request(self):
        vals = {
            'reason': 'طلب سلفه لسداد خروج وعودة',
            'loan_type': self.loan_type_id.id or self.exit_entry_type_id.loan_type_id.id,
            'date': time.strftime("%Y-%m-%d"),
            'loan_amount': self.employee_share,
            'hr_manager_approval': self.employee_share,
            'employee_id': self.employee_id.id,
            'linked_exit_rentry_id': self.id,
            'another_loan_before_pay': True,
        }
        loan_request = self.env['loan.advance.request'].create(vals)
        self.linked_loan_request_id = loan_request.id

    #@api.one
    def create_exit_rentry(self):
        vals = {
            'name': u'طلب خروج و عوده للموظف %s' % (self.employee_id.name),
            'employee_id': self.employee_id.id,
            'reason': 'leave',
            'leave_request_id': self.leave_request_id.id,
            'one_mutli': 'one',
            'state': 'new'
        }
        exit_rentry = self.env['hr.exit.entry.request'].create(vals)
        exit_rentry.onchange_leave_request_id()

    #@api.multi
    def exit_rentry_validation(self):
        exit_rentry = self.search([['employee_id', '=', self.employee_id.id], ['state', '=', 'confirmed']], order='expected_return_date desc')
        if exit_rentry:
            X = self.expected_return_date
            Y = exit_rentry[0].expected_return_date
            Z = self.expected_travel_date
            M = exit_rentry[0].expected_travel_date
            if X <= Y and Z >= M and exit_rentry[0].one_mutli == 'multi':
                return {
                    'domain': "[]",
                    'name': _('Not Allowed'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'exit.rentry.validation',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {
                        'default_employee_id': self.employee_id.id,
                        'default_exit_rentry_id': self.id,
                        'default_validation_from': 'exit_rentry',
                    },
                }
        return False

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.reason = False
        self.one_mutli = False
        # employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])[0]
        # if not (employee and employee.manager):
        #     return {'domain': {'employee_id': [['id', '=', employee.id], ['nationality_type', '=', 'Non-Saudi']]},
        #             'value': {'employee_id': employee.id}}

    @api.model
    def create(self, vals):
        res = super(ExitEntryRequest, self).create(vals)
        res.code = self.env['ir.sequence'].next_by_code(self._name)
        return res

    #@api.one
    def unlink(self):
        if self.state == 'confirmed':
            raise ValidationError(_("Not allowed to delete a confirmed Exit and re-entry!"))
        return super(ExitEntryRequest, self).unlink()


class ExitEntryAttachments(models.Model):
    _name = "exit.entry.attachment"
    _description = "Exit entry attachment"

    source_id = fields.Many2one('hr.exit.entry.request', 'Source')
    file = fields.Binary('File')
    name = fields.Char('Description')
    note = fields.Char('Notes')


class Contract(models.Model):
    _inherit = "hr.contract"
    exit_entry_type_id = fields.Many2one('hr.exit.entry.type', 'Exit and Re-entry Policy')

    @api.onchange('nationality_type')
    def onchange_nationality_type_(self):
        if self.nationality_type == 'Saudi':
            self.exit_entry_type_id = False


class Employee(models.Model):
    _inherit = "hr.employee"

    count_exit_entry_requests = fields.Integer('Number of Exit and Re-entry Request', compute='get_count_exit_entry_requests')

    #@api.one
    @api.depends()
    def get_count_exit_entry_requests(self):
        self.count_exit_entry_requests = len(self.env['hr.exit.entry.request'].search([['employee_id', '=', self.id]]))

    #@api.multi
    def open_exit_entry_requests(self):
        return {
            'domain': [['employee_id', '=', self.id]],
            'name': _('Exit and Re-entry Request'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.exit.entry.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_employee_id': self.id},
        }
