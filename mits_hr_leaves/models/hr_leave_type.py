# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
# from datetime import datetime, date
# from datetime import timedelta
# import calendar
# from dateutil.relativedelta import relativedelta
# from odoo import tools
# import math
# import pytz
# from dateutil import tz
# import os



class hr_holidays_status(models.Model):
    # _name = 'hr.holidays.status'
    # _inherit = ['mail.thread', 'hr.holidays.status']
    _name = 'hr.leave.type'
    _inherit = ['hr.leave.type' ,'mail.thread',]


    name = fields.Char('Leave Description‬‬', required=True, translate=True)
    double_validation = fields.Boolean('Apply Double Validation', default=True,
                                       help="When selected, the Allocation/Leave Requests for this type require a second validation to be approved.")
    type = fields.Selection([('Annual Leave', 'Annual Leave'),
                             ('Non Annual Leave', '‫‪Non Annual Leave‬‬')], _('Leave Type'), required=True)
    limit = fields.Boolean('Unlimited leave balance',
                           help='If you select this check box, the system allows the employees to take more leaves than the available ones for this type and \
                           will not take them into account for the "Remaining Legal Leaves" defined on the employee form.')
    days_per_leave = fields.Integer(string="Maximum Days Per Each Leave")
    days_in_month = fields.Integer(string="Days In Month", default=30)
    months_in_year = fields.Integer(string="Months In Year", default=12)
    days_in_year = fields.Integer(string="Days In Year", compute="_compute_days_in_year", store=True, readonly=True)
    nationality = fields.Selection([
        ('Saudi', 'Saudis Only'),
        ('Non-Saudi', 'Non-Saudis only'),
        ('All Nationalities', '‫All Nationalities‬‬'),
    ], _('Nationality'), required=True)
    reconciliation_based_on = fields.Selection([('basic', 'Basic Salary'), ], string='Leave Reconciliation based on', default='basic')

    start_calc_from = fields.Selection([('First Effective Notice', 'First Effective Notice'),
                                        ('Contract Start Date', 'Contract Start Date'),
                                        ('Trial Period Start Date', '‫Trial Period Start Date‬‬')], _('Start Calculation From'),
                                       default="First Effective Notice")
    start_allocation_after = fields.Integer(string="Start Automatic Allocation After (months)")
    max_balance = fields.Integer(string="Max Accumulated Balance", default=180)
    notes = fields.Html(string="Notes")
    lines = fields.One2many('leaves.calc.method.line', 'leave_type_id', string="Calculation Method")
    max_line_less = fields.Integer()
    can_request_air_ticket = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='can request air ticket')
    can_request_exit_rentry = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Can request For Exit and R-entry')
    linked_exit_renry_id = fields.Many2one('hr.exit.entry.request', 'Linked exit and Re-entry')

    state = fields.Selection([('New', 'New'), ('Approved', 'Approved')], string='Status', readonly=True, select=True, default='New', )
    reconciliation_method = fields.Selection(
        [('Stop payslip during leave and use leave reconciliation', 'Stop payslip during leave and use leave reconciliation'),
         ('Continue payslip during leave ( no need for leave reconciliation)', 'Continue payslip during leave ( no need for leave reconciliation)')],
        string='Leave Reconciliation method')

    non_annual_type = fields.Selection([
        ('Unpaid Leave', 'Unpaid Leave'),
        ('Hajj Leave', 'Hajj Leave'),
        ('Omra Leave', 'Omra Leave'),
        ('New Baby For Men', 'New Baby For Men'),
        ('Marriage Leave', 'Marriage Leave'),
        ('New Baby For Women', 'New Baby For Women'),
        ('Husband Death', 'Husband Death'),
        ('Death Of A Relative', 'Death Of A Relative'),
        ('Exams Vacation', 'Exams Vacation'),
        ('Sick Leave', 'Sick Leave'),
        ('Other', 'Other'),
    ], string='Non Annual Leave Type')
    sick_message = fields.Char('=>', compute="_compute_sick_message")
    number_of_days = fields.Integer(string="Number Of Days")
    non_annual_frequency = fields.Selection([
        ('contract', 'Per contract'),
        ('financial_year', 'Per financial year ( 1Jan : 31 Dec)'),
        ('contractual_year', 'Each contractual year ( hiring dat to next year)'),
        ('one_time', 'one time per live.'),
        ('per_request', 'based on request (no limitation)'),
    ], string='Non annual leave Frequency')
    divide_leave_balance = fields.Selection([
        ('allow_to_divide', 'Allow to divide leave balance ( more than leave request)'),
        ('one_time', 'One time, if employee request this leave, deduct all balance.'),
    ], string='Divide Leave Balance')
    who_request = fields.Selection([
        ('Male only', 'Male only'),
        ('Females only', 'Females only'),
        ('Both', 'Both'),
    ], string='Who can request this leave')

    marital_status = fields.Selection([
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Both', 'Both'),
    ], string='Marital Status')

    religion = fields.Selection([
        ('Muslim', 'Muslim'),
        ('Non-Muslim', 'Non-Muslim'),
        ('All Religions', 'All Religions'),
    ], string='Religion')
    # /////////////////// Smart Buttons /////////////////////////////////////////////////////////////
    count_leave_requests = fields.Float('Number of leave requests', compute='get_count_smart_buttons')
    count_contracts = fields.Float('Number of contracts', compute='get_count_smart_buttons')
    count_leave_allocations = fields.Float('Number of leave allocations', compute='get_count_smart_buttons')
    duration_in_leave_request = fields.Selection([
        ('yes', 'yes'),
        ('no', 'No'),
    ], string='Include Holiday duration in leave request calculation',default='yes',
     help="Example :You have a national holiday between 05/10/2017 to 09/10/2017 ( 5 days ), an employee requested for a leave between 01/10/2017 and 30/10/2017, if you select yes, leave request duration will be 30 days, if you select no, leave request duration will be 25 days.")


    #@api.one
    def get_count_smart_buttons(self):
        self.count_leave_requests = self.env['hr.leave'].search_count([('holiday_status_id', '=', self.id), ('type', '=', 'remove')])
        self.count_contracts = self.env['hr.contract'].search_count([('annual_leave_policy', '=', self.id)])
        self.count_leave_allocations = self.env['hr.leave'].search_count([('holiday_status_id', '=', self.id), ('type', '=', 'add')])

    #@api.multi
    def open_leave_requests(self):
        return {
            'domain': [('holiday_status_id', '=', self.id), ('type', '=', 'remove')],
            'name': _('Leave requests'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.leave',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    #@api.multi
    def open_contracts(self):
        return {
            'domain': [('annual_leave_policy', '=', self.id)],
            'name': _('Contracts'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.contract',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    #@api.multi
    def open_allocations(self):
        return {
            'domain': [('holiday_status_id', '=', self.id), ('type', '=', 'add')],
            'name': _('Leave Allocations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.leave',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    # ///////////////////////////////////////////////////////////////////////////////////////////////////

    #@api.one
    @api.onchange('nationality')
    def onchange_nationality(self):
        self.can_request_exit_rentry = False

    #@api.one
    @api.onchange('limit')
    def onchange_limit(self):
        self.number_of_days = 0

    #@api.one
    @api.onchange('non_annual_frequency')
    def onchange_non_annual_frequency(self):
        if self.non_annual_frequency == 'per_request':
            self.limit = True

    @api.constrains('limit')
    def _check_days_per_leave(self):
        if self.limit and self.days_per_leave <= 0:
            raise exceptions.ValidationError("Attention!! \n Maximum days per each leave can not be zero or minus.")

    @api.constrains('number_of_days')
    def _check_number_of_days(self):
        if self.number_of_days < 0:
            raise exceptions.ValidationError("Number Of Days cannot be negative")

    @api.constrains('type')
    def _check_type(self):
        if self.type == 'Non Annual Leave' and not self.limit:
            if self.number_of_days <= 0:
                error_msg = "Data Error !! \n You are trying to add a new Non annual leave ( %s ) It is not logic that Number of days assigned to this leave is zero or minus or contain days Fractions." % (
                    self.name)
                raise ValidationError(_(error_msg))

    @api.constrains('non_annual_type')
    def _check_non_annual_type(self):
        if self.id:
            old_same_leave_types = self.env['hr.leave.type'].search(
                [('non_annual_type', '=', self.non_annual_type), ('nationality', '=', self.nationality), ('who_request', '=', self.who_request),
                 ('id', '!=', self.id)])
        else:
            old_same_leave_types = self.env['hr.leave.type'].search(
                [('non_annual_type', '=', self.non_annual_type), ('nationality', '=', self.nationality), ('who_request', '=', self.who_request)])

            # if len(old_same_leave_types) and self.type == 'Non Annual Leave':
            #     error_msg = "Dear Hr manager, \n It is not allowed to define same Non-annual leave type ( %s ) for same Nationality ( %s ) and same gender ( %s ) " % (
            #         self.non_annual_type, self.nationality, self.who_request)
            #     raise ValidationError(_(error_msg))

    #@api.one
    @api.onchange('type', 'nationality')
    def clear_can_request(self):
        self.can_request_air_ticket = False
        if self.type != 'Annual Leave':
            self.reconciliation_based_on = False

    #@api.one
    @api.depends('days_in_month', 'months_in_year')
    def _compute_days_in_year(self):
        for rec in self:
            rec.days_in_year = rec.days_in_month * rec.months_in_year

    #@api.one
    @api.depends('non_annual_type')
    def _compute_sick_message(self):
        for rec in self:
            rec.sick_message = 'Full Salary for first 30 days , 75 % from total salary for next 60 days and no salary for last 30 days.'

    @api.constrains('days_in_month', 'months_in_year')
    def _check_values(self):
        if self.days_in_month <= 0 or self.months_in_year <= 0:
            raise exceptions.ValidationError(
                _("Configuration error!! ‫‪The‬‬ ‫‪calculations‬‬ ‫‪mustn’t‬‬ ‫‪contains‬‬ ‫‪a‬‬ ‫‪value‬‬ ‫‪equal‬‬ ‫‪to‬‬ ‫‪zero‬‬"))

    @api.constrains('start_allocation_after')
    def _check_start_allocation_after(self):
        if self.start_allocation_after < 0:
            raise exceptions.ValidationError("Start Automatic Allocation After (months) cannot be negative")

    @api.onchange('type')
    def onchange_type(self):
        for rec in self:
            rec.reconciliation_method = ''
            rec.non_annual_type = ''
            rec.number_of_days = 0
            rec.non_annual_frequency = ''
            rec.divide_leave_balance = ''
            rec.who_request = ''
            rec.marital_status = ''
            rec.religion = ''
            if rec.type == 'Annual Leave':
                rec.limit = False
            if rec.type == "Non Annual Leave":
                rec.lines = []

    @api.onchange('non_annual_type')
    def onchange_non_annual_type(self):
        for rec in self:
            rec.number_of_days = 0
            rec.non_annual_frequency = ''
            rec.divide_leave_balance = ''
            rec.who_request = ''
            rec.marital_status = ''
            rec.religion = ''
            if rec.non_annual_type == 'Unpaid Leave':
                rec.reconciliation_method = 'Stop payslip during leave and use leave reconciliation'
            elif rec.non_annual_type == 'Sick Leave':
                rec.reconciliation_method = 'Continue payslip during leave ( no need for leave reconciliation)'
                rec.number_of_days = 120
            else:
                rec.reconciliation_method = ''

            if rec.non_annual_type == 'New Baby For Men':
                rec.who_request = 'Male only'
                rec.marital_status = 'Married'

            if rec.non_annual_type == 'Marriage Leave':
                rec.marital_status = 'Single'

            if rec.non_annual_type in ['New Baby For Women', 'Husband Death']:
                rec.who_request = 'Females only'
                rec.marital_status = 'Married'

    @api.constrains('max_balance')
    def _check_max_balance(self):
        if self.max_balance <= 0:
            raise exceptions.ValidationError("Configuration error!! Max accumulated balance cannot be equal to zero Or Negative !!")

    #@api.multi
    def action_hr_approve(self):
        for record in self:
            if record.type == 'Annual Leave':
                if len(record.lines) == 0:
                    raise exceptions.ValidationError("Data error!! You must insert at least one line in the calculation method table")
            # if record.limit:
            #     msg = _(
            #         "Dear HR manager, Attention , you selected ( Unlimited leave balance ) for this leave, which mean that your system will not check employee leave balance when requesting for this leave. Are you sure that you want to continue ? ")

            #     raise exceptions.ValidationError(msg)
                # return self.env.user.show_dialogue(msg, 'hr.leave.type', 'hr_approve', record.id)

            return record.hr_approve()

    #@api.multi
    def hr_approve(self):
        for record in self:
            record.write({'state': 'Approved'})
            body = "Document Approved By Hr Department"
            self.message_post(body=body, message_type='email')
        return {}

    #@api.multi
    def action_set_to_new(self):
        for record in self:
            record.write({'state': 'New'})
            body = "Document changed to ->  New Status"
            self.message_post(body=body, message_type='email')
        return {}

    #@api.one
    def unlink(self):
        if self.state != 'New':
            raise exceptions.ValidationError("Not allowed to delete approved document, you can set it to new and delete it")
        contracts = self.env['hr.contract'].search([['annual_leave_policy', '=', self.id]])
        if contracts:
            raise ValidationError(_("You can not delete Leave type while it linked with Contract%s\n" % (str('\n'.join([str(c.name) for c in contracts])))))
        return super(hr_holidays_status, self).unlink()

