# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import datetime

from odoo.exceptions import UserError, ValidationError
import time
from dateutil.relativedelta import relativedelta


class air_ticket_type(models.Model):
    _name = 'air.ticket.type'
    _description = "Air ticket type"
    _inherit = ['mail.thread']
    _order = "id desc"
    _rec_name = "policy_name"

    name = fields.Char(_('Code'), readonly=True)
    policy_name = fields.Char(_('Air Ticket Policy Name'), required=True)
    nationality = fields.Selection([('Saudi', 'Saudi'),
                                    ('Non-Saudi', 'Non-Saudi'),
                                    ('All Nationalities', '‫All Nationalities‬‬'), ], _('Nationality'), required=True)
    frequency_air_ticket = fields.Selection([('Not allowed', 'Not allowed'),
                                             ('one time each', 'one time each'),
                                             ('One time per contract', 'One time per contract'),
                                             ('Unlimited air tickets based on request condition',
                                              'Unlimited air tickets based on request condition')],
                                            _('Frequency Air Ticket'), required=True)
    number_of_months = fields.Float(_('Each'))
    months_to_request_air_ticket = fields.Integer(
        'The employee is allowed to request air ticket if his balance is greater than')
    maximum_accumulated_balance = fields.Integer('Maximum accumulated balance', default=24)
    air_ticket_class = fields.Selection([('First Class', 'First Class'),
                                         ('Business Class', 'Business Class'),
                                         ('Economic Class', 'Economic Class')], _('Air ticket class'))
    give_cash_instead_tickets = fields.Selection([('Yes', 'Yes'),
                                                  ('No', 'No')],
                                                 _('allow to give cash to employees instead of tickets'))
    relatives_tickets = fields.Selection([('Allow tickets for relatives', 'Allow tickets for relatives'),
                                          ('Never allow tickets for relatives', 'Never allow tickets for relatives')],
                                         _('Relatives Tickets'))
    number_of_wives = fields.Integer('Number Of Wives')
    children = fields.Integer('Number Of Children')
    max_child_age = fields.Integer('Max Age For Children')

    number_of_relatives = fields.Float(_('Number of relatives'), compute='_compute_number_of_relatives')
    notes = fields.Text(_('Notes'))
    state = fields.Selection([('New', 'New'),
                              ('Approved', 'Approved')], string='Status', readonly=True, select=True, copy=False,
                             default='New')
    type = fields.Selection([('annual', 'Annual'), ('non-annual', 'Non-annual')], string='Air ticket Type')
    air_ticket_request_ids = fields.One2many('air.ticket.request', 'air_ticket_type', 'Air ticket requests')
    air_ticket_request_count = fields.Integer('Number of requests', compute='get_air_ticket_request_count')
    can_request_exit_rentry = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Can request For Exist and R-entry')
    loan_type_id = fields.Many2one('hr_loans.loan_advance', 'Loan type', help="when an employee request for air ticket, if the company will pay instead of\
    employee, your system will automatically create a loan request using this loan type. ")

    account_id = fields.Many2one('account.account')
    journal_id = fields.Many2one('account.journal')


    #@api.one
    @api.depends('number_of_wives', 'children')
    def _compute_number_of_relatives(self):
        for rec in self:
            rec.number_of_relatives = rec.number_of_wives + rec.children

    #@api.one
    @api.onchange('relatives_tickets')
    def onchange_relatives_tickets(self):
        if self.relatives_tickets == 'Allow tickets for relatives':
            self.number_of_wives = 1
            self.children = 2
            self.max_child_age = 18
        else:
            self.number_of_wives = 0
            self.children = 0
            self.max_child_age = 0

    #@api.multi
    def open_requests(self):
        return {
            'domain': [['air_ticket_type', '=', self.id]],
            'name': _('Air ticket requests'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'air.ticket.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_air_ticket_type': self.id},
        }

    #@api.one
    @api.constrains('number_of_wives', 'children', 'max_child_age')
    def _check_positive(self):
        if self.number_of_wives < 0:
            raise exceptions.ValidationError(_("Number Of Wives cannot be Minus"))
        if self.children < 0:
            raise exceptions.ValidationError(_("Number Of Children cannot be Minus"))
        if self.max_child_age < 0:
            raise exceptions.ValidationError(_("Max Age For Children cannot be Minus"))

    #@api.one
    @api.depends('air_ticket_request_ids')
    def get_air_ticket_request_count(self):
        self.air_ticket_request_count = len((self.air_ticket_request_ids))

    @api.constrains('frequency_air_ticket', 'number_of_months', 'maximum_accumulated_balance',
                    'months_to_request_air_ticket')
    def check_maximum_accumulated_balance(self):
        if self.frequency_air_ticket == 'one time each':
            if self.maximum_accumulated_balance < 0:
                raise ValidationError("maximum accumulated balance Cant Be Minus")

            if self.months_to_request_air_ticket < 0:
                raise ValidationError(
                    "The employee is allowed to request air ticket if his balance is greater than Field Cant Be Minus")

            if self.maximum_accumulated_balance < self.number_of_months:
                raise ValidationError(_("Configuration Error!\n\
                    Based on your configuration, you told your system that employees is allowed to request air ticket each (%s) months,\
                    Also you told your system that the maximum accumulated balance is (%s) months.\n Based on this configuration, all employees will not be \
                    able to request air tickets, because the maximum accumulated balance is less than the balance which is necessary to request air ticket.(%s)\
                    months!" % (self.number_of_months, self.maximum_accumulated_balance, self.number_of_months)))

            if self.months_to_request_air_ticket > self.number_of_months:
                raise ValidationError(_("Configuration Error!\n\
                    Based on this configuration, it is not logic to till your system that the employee can request one air ticket each (%s) and the employee is\
                    allowed to request air ticket if his balance is greater than (%s )Months" % (
                self.number_of_months, self.months_to_request_air_ticket)))

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('mits_a_t.air_ticket_type')
        res = super(air_ticket_type, self).create(vals)
        return res

    @api.constrains('number_of_months')
    def _check_number_of_months(self):
        if self.frequency_air_ticket == "one time each":
            if self.number_of_months == 0:
                raise exceptions.ValidationError("Attention!! Number of Months cannot equal to zero.")

    @api.constrains('number_of_relatives')
    def _check_number_of_months(self):
        if self.relatives_tickets == "Allow tickets for relatives":
            if self.number_of_relatives == 0:
                raise exceptions.ValidationError("Attention!! Number of relatives cannot equal to zero.")

    #@api.multi
    def ticket_approve(self):
        for rec in self:
            # if rec.frequency_air_ticket == "one time each" and rec.months_to_request_air_ticket == 0:
            #     error_msg = _(
            #         "Dear Hr manager, \n Based on your configuration, The employee is allowed to request air ticket if his balance is greater than zero months, this mean that if you select this air ticket type in employee contract, he will be able to request air tickets any time.")
            #     # return self.env.user.show_dialogue(error_msg,'air.ticket.type','do_ticket_approve',rec.id)
            #     raise ValidationError(error_msg)
            rec.do_ticket_approve()

    #@api.multi
    def do_ticket_approve(self):
        self.write({'state': 'Approved'})
        body = "Ticket Approved"
        self.message_post(body=body, message_type='email')
        return {}

    

    #@api.multi
    def ticket_set_new(self):
        self.write({'state': 'New'})
        body = "Ticket Returned to New Status"
        self.message_post(body=body, message_type='email')
        return {}

    #@api.multi
    def unlink(self):
        for rec in self:
            if rec.state == 'Approved':
                raise exceptions.ValidationError(_("Not allowed to delete an Approved Ticket !!"))
        return super(air_ticket_type, self).unlink()


class air_ticket_request(models.Model):
    _name = 'air.ticket.request'
    _description = 'Air ticket request'
    _order = "id desc"
    _inherit = ['mail.thread']

    READONLY_STATE = {'approved': [('readonly', True)],'paid': [('readonly', True)]}

    name = fields.Char(_('Code'), readonly=True)
    description = fields.Char(_('Description'), required=True, states=READONLY_STATE)
    employee_id = fields.Many2one('hr.employee', _('Employee'), required=True, states=READONLY_STATE)
    employee_nationality = fields.Selection(string='Employee nationality', related='employee_id.nationality_type')
    request_type = fields.Selection([('Annual air ticket', 'Annual air ticket'),
                                     ('Other', 'Other')], _('Request Type'), states=READONLY_STATE)
    contract_id = fields.Many2one('hr.contract', string='Contract', compute="_compute_contract", readonly=True,
                                  store=True)
    contract_leave_policy = fields.Many2one('hr.leave.type', _('Contract leave policy'),
                                            related="contract_id.annual_leave_policy", readonly=True)
    air_ticket_policy = fields.Many2one('air.ticket.type', string='Annual Air Ticket Policy',
                                        related="contract_id.air_ticket_policy", readonly=True)
    # working_months = fields.Char(_('Working months'), related="contract.total_contract_duration")
    cash_allowed = fields.Selection([('Yes', 'Yes'),
                                     ('No', 'No')], _('Cash allowed'), readonly=True, compute="_compute_cash_allowed")
    relatives_tickets = fields.Selection([('Allow tickets for relatives', 'Allow tickets for relatives'),
                                          ('Never allow tickets for relatives', 'Never allow tickets for relatives')],
                                         _('Relatives Tickets'), readonly=True,
                                         compute="_compute_relatives_tickets")
    number_of_relatives = fields.Float(_('Number of relatives'), related="air_ticket_policy.number_of_relatives")
    request_reason = fields.Selection([('leave', 'leave'),
                                       ('Deputation / business trip', 'Deputation / business trip'),
                                       ('Final exit', 'Final exit'),
                                       ('Other', 'Other')], _('Air Ticket request reason'), required=True,
                                      states=READONLY_STATE)
    reason_detail = fields.Char('air ticket request reason', states=READONLY_STATE)
    leave_request = fields.Many2one('hr.leave', _('Leave Request'), states=READONLY_STATE)
    leave_from = fields.Datetime('Leave start', related='leave_request.date_from')
    leave_to = fields.Datetime('Leave start', related='leave_request.date_to')
    travel_date = fields.Date('Travel date', states=READONLY_STATE)
    leave_request_type_id = fields.Many2one('hr.leave.type', 'Leave request type',
                                            related='leave_request.holiday_status_id')
    contract_type_equal_leave_type = fields.Boolean('Contract leave policy equal leave type',
                                                    compute='get_contract_type_equal_leave_type', store=True)
    air_ticket_type = fields.Many2one('air.ticket.type', 'Air ticket type', states=READONLY_STATE)
    i_want_to = fields.Selection([('Reserve a ticket through company', 'Reserve a ticket through company'),
                                  ('Cash', 'Cash')], _('I want to'), default='Reserve a ticket through company',
                                 states=READONLY_STATE)
    reserve_ticket_for = fields.Selection([
        ('Employee only', 'Employee only'),
        ('Employee and his relatives', 'Employee and his relatives'),
    ('Relatives only', 'Relatives only'),

    
     ], _('Reserve ticket for'),
                                          required=True, states=READONLY_STATE,
                                          default='Employee only')
    ticket_total_price = fields.Float('Air ticket total price', states=READONLY_STATE)
    company_share = fields.Float('Company share', states=READONLY_STATE)
    employee_share = fields.Float('Employee share', compute="get_employee_share")
    employee_share_method = fields.Selection([
        ('debit', 'The company will pay instead of employee + Create a deduction'),
        ('cash', 'Cash & bank transfer'),
    ], string="Employee share payment method", states=READONLY_STATE)
    request_date = fields.Date(_('Request date'), required=True, default=lambda s: time.strftime("%Y-%m-%d"),
                               states=READONLY_STATE)
    skip_valid_approve_req = fields.Boolean(_('Skip system Validation And approve this request'), states=READONLY_STATE)
    reviewed_by = fields.Many2one('res.users', _('Reviewed by'), readonly=True)
    confirmed_by = fields.Many2one('res.users', _('Confirmed by'), readonly=True)
    air_ticket_details = fields.One2many('air.ticket.details', 'request_id', _('Air Ticket Details'),
                                         states=READONLY_STATE)
    state = fields.Selection([
        ('new', 'New request'),
        ('reviewed', 'Data reviewed'),
        ('approved', 'final Approved'),
        ('paid', 'Paid'),
        ('refused', 'Refused'),
    ], string='Status', default='new', track_visibility='onchange')
    old_tickets_request_ids = fields.Many2many('air.ticket.request', 'rel_old_air_ticket_request',
                                               'air_ticket_request1', 'air_ticket_requets2', 'Old air tickets')
    note = fields.Html('Notes')
    attachment_ids = fields.One2many('air.ticket.request.attachment', 'source_id', 'Attachments', states=READONLY_STATE)
    id_ = fields.Integer('id', compute='save_id', store=True)
    wait = fields.Boolean('wait', states=READONLY_STATE)
    can_request_exit_rentry = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='request For Exist and R-entry', related='air_ticket_type.can_request_exit_rentry')
    air_ticket_type_can_request_exit_rentry = fields.Selection(related='air_ticket_type.can_request_exit_rentry')
    linked_exit_rentry_id = fields.Many2one('hr.exit.entry.request', 'Linked exit Re-entry', states=READONLY_STATE)
    expected_return_date = fields.Date('Expected Return date', compute='get_expected_return_date')
    # developer mode fields (Employee INfo)
    iqama_id = fields.Char('Iqama number', compute='get_employee_info', multi=True)
    iqama_id_ = fields.Char('Iqama number')
    iqama_expiry_date = fields.Date('Iqama Expiry date', compute='get_employee_info', multi=True)
    iqama_expiry_date_ = fields.Date('Iqama Expiry date', states=READONLY_STATE)
    passport_no = fields.Char('Passport Number', compute='get_employee_info', multi=True)
    passport_no_ = fields.Char('Passport Number', states=READONLY_STATE)
    passport_expiry_date = fields.Date('Passport expiry date', compute='get_employee_info', multi=True)
    passport_expiry_date_ = fields.Date('Passport expiry date', states=READONLY_STATE)
    # Smart buttons
    count_leave_requests = fields.Float('Number of leave requests', compute='get_smart_buttons_count', multi=True)
    leave_request_ids = fields.One2many('hr.leave', 'air_ticket_id', 'Leave requests', states=READONLY_STATE)
    count_exit_rentry = fields.Float('Number of Exit and Re-entry', compute='get_smart_buttons_count', multi=True)
    exit_rentry_ids = fields.One2many('hr.exit.entry.request', 'air_ticket_request_id', 'Exit and Re-entry',
                                      states=READONLY_STATE)
    loan_type_id = fields.Many2one('hr_loans.loan_advance', 'Loan type', related='air_ticket_type.loan_type_id')
    loan_request_id = fields.Many2one('loan.advance.request', 'Linked Loan request', states=READONLY_STATE)
    count_loan_request = fields.Integer('Number of loan requests', compute='get_count_loan_request')
    count_old_requests = fields.Integer('Number of loan requests', compute='get_count_lcount_old_requests')

    current_air_ticket_balance = fields.Integer('Current air Ticket balance', states=READONLY_STATE)
    deduct = fields.Float('If this Air Ticket approved, system will deduct', states=READONLY_STATE)
    remaining_balance = fields.Float('Remaining Balance', states=READONLY_STATE)
    show_remaining = fields.Boolean('Show remaining', states=READONLY_STATE)
    payment_time = fields.Selection([
        ('now', 'Pay Now'),
        ('with_reconciliation', 'Pay with Leave reconciliation'),
    ], string='Payment time', states=READONLY_STATE)
    limit = fields.Boolean()
    

    # paid_through_reconciliation = fields.Boolean('Paid through leave reconciliation', states=READONLY_STATE)

    departure_date = fields.Date(_('Departure date'))
    return_date = fields.Date(_('Return date'))
    airticket_move_id = fields.Many2one('account.move',copy=False)

    def ticket_action_payment(self):
        for rec in self:

            airticket_type = rec.air_ticket_type
            # journal_id = rec.env['ir.config_parameter'].sudo().get_param('hr_loans.default_loan_journal_id', False)
            # account_id = rec.env['ir.config_parameter'].sudo().get_param('hr_loans.default_loan_account_id', False)    
            
            journal_id = airticket_type.journal_id.id
            account_id = airticket_type.account_id.id
            
            
            if not journal_id or not account_id:
                raise exceptions.ValidationError(_("Sorry!!,please  add journal and account in type setting ."))
            if not rec.employee_id.address_home_id.id:
                raise exceptions.ValidationError(_("Sorry!!,please set address partner in employee information first."))
            
            ctx = {
                'default_airticket_id': rec.id,
            'default_journal_id': journal_id,
            'default_account_id':account_id,
            'default_airticket_amount':rec.employee_share,
                }
            return {
                'name': 'Air Ticket Payment',
                'type': 'ir.actions.act_window',
                'res_model': 'emp.airticket.payment',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context':ctx
            }

    

    def action_set_date(self):
        for rec in self:
            if rec.return_date < rec.departure_date:
                raise ValidationError(_("Sorry Depature Date Must be Less than Return Date"))
            for line in rec.air_ticket_details:
                line.departure_date = rec.departure_date
                line.return_date = rec.return_date

    @api.onchange('i_want_to', 'request_reason')
    def onchange_i_want_to(self):
        payment_time = False
        if self.i_want_to == 'Cash' and self.request_reason != 'leave':
            payment_time = 'now'
        self.payment_time = payment_time

    @api.onchange('employee_id', 'air_ticket_type')
    def get_current_air_ticket_balance(self):
        one_time = self.show_remaining = self.air_ticket_type.frequency_air_ticket == 'one time each' and self.air_ticket_type.type == 'annual'
        self.current_air_ticket_balance = self.employee_id.air_ticket_balance if one_time else 0
        self.deduct = self.air_ticket_type.number_of_months if one_time else 0
        self.remaining_balance = self.current_air_ticket_balance - self.deduct

    #@api.one
    @api.depends()
    def get_count_lcount_old_requests(self):
        old = self.search([['employee_id', '=', self.employee_id.id]])
        self.count_old_requests = len(old)

    #@api.one
    @api.depends()
    def get_count_loan_request(self):
        loans = self.env['loan.advance.request'].search([['linked_air_ticket_id', '=', self.id]])
        self.count_loan_request = len(loans)

    #@api.multi
    def open_exit_rentry_requests(self):
        return {
            'domain': [['id', '=', [l.id for l in self.exit_rentry_ids]]],
            'name': _('Linked Exit and Re-entry'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.exit.entry.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    #@api.multi
    def open_leave_requests(self):
        return {
            'domain': [['id', '=', [l.id for l in self.leave_request_ids]]],
            'name': _('leave requests'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.leave',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    #@api.multi
    def open_old_requests(self):
        return {
            'domain': [['employee_is', '=', self.employee_id.id]],
            'name': _('leave requests'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': self._name,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    #@api.multi
    def open_loan_request(self):
        loans = self.env['loan.advance.request'].search([['linked_air_ticket_id', '=', self.id]])
        return {
            'domain': [['id', '=', [l.id for l in loans]]],
            'name': _('Loan requests'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'loan.advance.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    #@api.one
    def get_remaining(self):
        self.get_current_air_ticket_balance()

    #@api.one
    @api.depends()
    def get_smart_buttons_count(self):
        self.count_leave_requests = len(self.leave_request_ids)
        self.count_exit_rentry = len(self.exit_rentry_ids)

    #@api.one
    @api.depends('employee_id')
    def get_employee_info(self):
        self.iqama_id = self.iqama_id_ or self.employee_id.identification_id
        self.iqama_expiry_date = self.iqama_expiry_date_ or self.employee_id.iqama_expiry_date
        self.passport_no = self.passport_no_ or self.employee_id.passport_id
        self.passport_expiry_date = self.passport_expiry_date_ or self.employee_id.passport_expiry_date

    #@api.one
    @api.depends('air_ticket_details')
    def get_expected_return_date(self):
        expected_return_date = False
        for line in self.air_ticket_details:
            if line.check_box and line.relation == 'Employee':
                expected_return_date = line.return_date
        self.expected_return_date = expected_return_date

    @api.onchange('i_want_to', 'employee_nationality', 'air_ticket_type')
    def get_can_request_exit_rentry(self):
        if self.i_want_to and self.employee_nationality == 'Non-Saudi' and self.air_ticket_type.can_request_exit_rentry == 'yes':
            self.can_request_exit_rentry = False

    @api.onchange('employee_id')
    def get_old_tickets_request(self):
        old_tickets_request_ids = [(5,)]
        if self.employee_id:
            domain = [['employee_id', '=', self.employee_id.id], ['id_', '!=', self.id_]]
            old_requests = self.search(domain)
            old_tickets_request_ids += [(4, r.id) for r in old_requests]
        self.old_tickets_request_ids = old_tickets_request_ids

    #@api.one
    @api.depends('ticket_total_price', 'company_share')
    def get_employee_share(self):
        self.employee_share = self.ticket_total_price - self.company_share
        if self.employee_share <= 0:
            self.employee_share_method = False

    @api.onchange('ticket_total_price')
    def onchange_ticket_total_price(self):
        self.company_share = self.ticket_total_price

    #@api.one
    def reset(self):
        self.state = 'new'

    #@api.one
    def refuse(self):
        self.state = 'refused'

    #@api.one
    def review(self):
        self.get_remaining()
        self.reviewed_by = self.env.user.id
        self.state = 'reviewed'

    #@api.multi
    def approve(self, skip=False, confirm_no_company_share=False):
        # if self.state == 'approved' or self.wait:
        #     raise ValidationError(_("Please wait ..."))
        self.wait = True
        if not self.travel_date:
            raise ValidationError(_("please select travel date"))

        
        
        if self.leave_from and self.travel_date:
            travel_date = datetime.datetime(self.travel_date.year, self.travel_date.month, self.travel_date.day)
            if travel_date >= self.leave_from:
                raise ValidationError(_("Date Error!\n\
                Travel date must be less than leave Start date!."))
        if self.request_reason not in ['leave', 'Other','Deputation / business trip']:
            raise ValidationError(
                _("Requesting air tickets for deputation, final exit and other cases still under development."))
        if self.ticket_total_price <= 0:
            raise ValidationError(_("Attention!\nAir ticket total price cannot be zero!"))
        if self.request_reason == 'leave':
            if self.skip_valid_approve_req:
                if not (isinstance(skip, bool) and skip):
                    self.wait = False
                    return self.open_skip_validate_wizard('mits_air_tickets.skip_validate_wizard_form')
            else:
                holiday_status_id = self.leave_request.holiday_status_id
                if holiday_status_id.can_request_air_ticket != 'yes':
                    raise ValidationError(_("Can Not Request air ticket for this leave type\n\
                        To configure your leave types, go to leaves and air tickets module > Leaves Configuration then open Leave types window."))
                else:
                    air_ticket_frequency = holiday_status_id.allowed_air_ticket_id.frequency_air_ticket
                    if air_ticket_frequency == 'Not allowed':
                        raise ValidationError(_("Not allowed !!\n\
                            Based on the leave policy, this employee cannot request air ticket for this leave type"))
                    if air_ticket_frequency == 'one time each':
                        A = self.employee_id.air_ticket_balance
                        B = self.air_ticket_type.months_to_request_air_ticket
                        D = self.company_share
                        if not D:
                            if not (isinstance(confirm_no_company_share, bool) and confirm_no_company_share):
                                self.wait = False
                                return self.open_company_share_validate_wizard(
                                    'mits_air_tickets.company_share_validate_wizard_form', A)
                        if D > 0:
                            if A >= B:
                                self.create_air_ticket_allocation()
                            else:
                                if self.skip_valid_approve_req:
                                    self.create_air_ticket_allocation()
                                else:
                                    raise ValidationError(_("Not allowed !\n\
                                    This employee only have ( %s ) months in his balance, based on the air ticket policy, the employee cannot request \
                                    for this air ticket unless his balance is equal to or greater than ( %s ) months.\nAs a HR manager, if you want to \
                                    confirm this air ticket regardless the employee balance, kindly select (skip system validation and approve this \
                                    transaction)" % (A, B)))
                    if air_ticket_frequency == 'One time per contract':
                        if self.env['air.ticket.request'].search(
                                [['employee_id', '=', self.employee_id.id], ['contract_id', '=', self.contract_id.id],
                                 ['air_ticket_type', '=', self.air_ticket_type.id], ['state', '=', 'approved']]):
                            raise ValidationError(_("Not allowed !\nBased on the air ticket policy, the employee cannot request this air ticket one time per \
                            contract, unfortunately we found that there is old air tickets assigned to the employee contract. \nAs a HR manager, if you want to\
                            confirm this air ticket regardless the old air tickets, kindly select (skip system validation and approve this transaction)"))
            self.skip_validation_and_approve()
        for line in self.air_ticket_details:
            if line.check_box and not line.ticket_type:
                raise ValidationError(_("Error!! \nPlease select Ticket type"))
        if self.company_share > self.ticket_total_price:
            raise ValidationError(_("Attention!\n\
            Air ticket total price is ( %s ), you told your system that the company share is ( %s ),it is not logic that the company will pay more than air\
             ticket total price." % (self.ticket_total_price, self.company_share)))
        for line in self.air_ticket_details:
            if line.check_box:
                if line.ticket_type and not line.departure_date:
                    raise ValidationError(_(" Dear, \n\
                        For ( %s )Kindly make sure that you select the departure and / or Return date" % (line.name)))
                if line.ticket_type == 'Return' and not self.expected_return_date:
                    raise ValidationError(_("Dear, \n\
                        For ( %s )Kindly make sure that you select the departure and / or Return date" % line.name))
                if line.departure_date and self.expected_return_date and line.departure_date > self.expected_return_date:
                    raise ValidationError(
                        _("Date Error !\nReturn date must be greater than or equal to Departure date !"))
        # if self.reserve_ticket_for != 'Relatives only' and not self.expected_return_date:
        #     raise ValidationError(_("Data Error !! \n\
        #         Please select expected return date for ( %s )" % (self.employee_id.name)))
        if self.employee_share > 0 and not self.loan_request_id:
            if not self.air_ticket_type.loan_type_id:
                raise ValidationError(_("Not allowed!!\n\
                    You can not approve this air ticket request, you told your system that the company will pay instead of employee + create a loan.\
                    unfortunately, we could not find a loan type linked with the Air ticket type which you select."))
            elif self.i_want_to != 'Cash' and self.employee_share_method == 'debit':
                self.create_loan_request()
        if self.request_reason == 'leave':
            if self.leave_request and self.employee_nationality == 'Non-Saudi':
                if self.leave_request.linked_exit_renry_id:
                    self.linked_exit_rentry_id = self.leave_request.linked_exit_renry_id.id
                else:
                    self.validate_for_create_exit_rentry()
        if self.i_want_to == 'Cash' and not self.payment_time:
            raise ValidationError(_("Dear Hr Manager,\n\
                Are you planning to pay this air ticket amount now, or you planning to pay this amount with Leave reconciliation? Kindly select Payment time."))
        else:
            if self.can_request_exit_rentry == 'yes' and not self.linked_exit_rentry_id and self.employee_nationality == 'Non-Saudi':
                self.validate_for_create_exit_rentry()
        self.get_remaining()
        self.reviewed_by = self.env.user.id
        self.wait = False
        # Employee info
        self.iqama_id_ = self.employee_id.identification_id
        self.iqama_expiry_date_ = self.employee_id.iqama_expiry_date
        self.passport_no_ = self.employee_id.passport_id
        self.passport_expiry_date_ = self.employee_id.passport_expiry_date
        self.state = 'approved'

    #@api.one
    def create_loan_request(self):
        vals = {
            'reason': 'طلب سلفه تذكرة طيران',
            'loan_type': self.air_ticket_type.loan_type_id.id,
            'date': time.strftime("%Y-%m-%d"),
            'loan_amount': self.employee_share,
            'hr_manager_approval': self.employee_share,
            'employee_id': self.employee_id.id,
            'linked_air_ticket_id': self.id,
            'another_loan_before_pay': True,
        }
        loan_request = self.env['loan.advance.request'].create(vals)
        self.loan_request_id = loan_request.id
        loan_request.action_hr_approve()

    #@api.one
    def validate_for_create_exit_rentry(self):
        last_exit_rentry = self.env['hr.exit.entry.request'].search(
            [['employee_id', '=', self.employee_id.id], ['state', '=', 'confirmed']],
            order='expected_return_date desc')
        if self.reserve_ticket_for != 'Relatives only' and last_exit_rentry and self.expected_return_date:
            X = self.expected_return_date
            Y = last_exit_rentry[0].expected_return_date
            if X > Y:
                self.create_exit_rentry()
            else:
                Z = self.travel_date
                M = Y
                if Z < M:
                    self.create_exit_rentry()
                elif last_exit_rentry[0].one_mutli == 'one':
                    self.create_exit_rentry()
                elif last_exit_rentry[0].one_mutli == 'multi':
                    return {
                        'domain': "[]",
                        'name': _('Not Allowed'),
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'exit.rentry.validation',
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'context': {
                            'default_air_ticket_id': self.id,
                            'default_employee_id': self.employee_id.id,
                            'default_exit_rentry_id': last_exit_rentry[0].id,
                        },
                    }

    #@api.one
    def create_exit_rentry(self):
        vals = {
            'name': u'طلب خروج و عوده للموظف %s' % (self.employee_id.name),
            'employee_id': self.employee_id.id,
            'reason': 'air_ticket',
            'air_ticket_request_id': self.id,
            'one_mutli': 'one',
            'expected_travel_date': self.travel_date,
            'state': 'new'
        }
        exit_rentry = self.env['hr.exit.entry.request'].create(vals)
        exit_rentry.get_type_info()
        exit_rentry.get_cost()
        # exit_rentry.onchange_leave_request_id()

    #@api.one
    def create_air_ticket_allocation(self):
        exit_rentry = self.env['air.ticket.balance.allocation'].create({
            'employee_id': self.employee_id.id,
            'allocated_balance': self.air_ticket_type.number_of_months * -1,
            'allocated_date': self.travel_date,
            'reason': 'خصم رصيد تذاكر طيران من النظام',
            'auto_create': True,
            'air_ticket_request_id': self.id,
            'confirmed_uid': self.env.user.id,
            'state': 'confirmed',
        })

    #@api.multi
    def open_company_share_validate_wizard(self, view_xml_id, A):
        ctx = {'default_air_ticket_request_id': self.id, 'default_a': str(A)}
        return {
            'domain': "[]",
            'name': _('Company share Validate'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'validate.wizard',
            'view_id': self.env.ref(view_xml_id).id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }

    #@api.multi
    def open_skip_validate_wizard(self, view_xml_id):
        ctx = {'default_air_ticket_request_id': self.id}
        return {
            'domain': "[]",
            'name': _('Skip validate ?'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'validate.wizard',
            'view_id': self.env.ref(view_xml_id).id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }

    #@api.multi
    def skip_validation_and_approve(self):
        for rec in self:
            if rec.leave_request.air_ticket_id:
                raise ValidationError(_("You are trying to request an air ticket for a specific leave, unfortunately, you cannot approve this air Ticket request, \
                    because we found that the leave request which you selected is already linked with another ticket!!"))
            rec.leave_request.air_ticket_id = rec.id

    @api.onchange('leave_from')
    def onchange_travel_date(self):
        for rec in self:
            rec.travel_date = rec.leave_from and rec.leave_from #.split(' ')[0]

    #@api.one
    @api.depends('leave_request_type_id', 'contract_leave_policy', 'leave_request')
    def get_contract_type_equal_leave_type(self):
        for rec in self:
            rec.contract_type_equal_leave_type = rec.leave_request and rec.leave_request_type_id.id != rec.contract_leave_policy.id

    @api.onchange('leave_request', 'employee_id', 'request_reason')
    def get_air_ticket_type(self):
        for rec in self:
            contract_type_equal_leave_type = rec.leave_request and rec.leave_request_type_id.id != rec.contract_leave_policy
            rec.air_ticket_type = False
            if contract_type_equal_leave_type:
                rec.air_ticket_type = rec.air_ticket_policy.id

    @api.onchange('request_reason', 'employee_id')
    def clear_leave_request(self):
        for rec in self:
            rec.leave_request = False


    @api.constrains('contract_id')
    def _check_contract_id(self):
        for rec in self:
            if not rec.contract_id:
                raise exceptions.ValidationError("The employee which you selected didn't have an active contract")

    @api.constrains('contract_leave_policy')
    def _check_contract_leave_policy(self):
        for rec in self:
            if not rec.contract_leave_policy:
                raise exceptions.ValidationError(
                    "Cannot save this transaction, because there is no leave policy attached to the selected employee.")

    @api.constrains('air_ticket_policy')
    def _check_air_ticket_policy(self):
        for rec in self:
            if not rec.air_ticket_policy:
                raise exceptions.ValidationError(
                    "You cannot request annual air ticket for this employee because we didn’t find any annual air ticket policy in his contract.")

    @api.constrains('relatives_tickets', 'air_ticket_details')
    def _check_relatives_tickets(self):
        for rec in self:
            if rec.relatives_tickets == "Never allow tickets for relatives":
                for line in self.air_ticket_details:
                    if line.check_box and line.relation != 'Employee':
                        raise exceptions.ValidationError(
                            "Based on this leave policy … it is not allowed to request air ticket for the employee relatives.")

    @api.constrains('reserve_ticket_for', 'air_ticket_details')
    def _check_reserve_ticket_for(self):
        if not self._context.get('skip_validation', False):
            if self.reserve_ticket_for in ["Employee only", "Employee and his relatives"]:
                for line in self.air_ticket_details:
                    if not line.check_box and line.relation == 'Employee':
                        raise exceptions.ValidationError(
                            "You forget to select the employee. (Go To (Air ticket details) Tab, then select the employee")
            if self.reserve_ticket_for == "Employee only":
                for line in self.air_ticket_details:
                    if line.check_box and line.relation != 'Employee' and not self.skip_valid_approve_req:
                        raise exceptions.ValidationError(
                            "Not allowed to request air ticket for employee relatives, Only Hr manage can approve this request if he select to skip system\
                            validations and approve this request.")
            if self.reserve_ticket_for in ["Relatives only", "Employee and his relatives"]:
                number_of_relatives = 0
                if self.number_of_relatives:
                    number_of_relatives = self.number_of_relatives
                elif self.air_ticket_type and self.air_ticket_type.relatives_tickets == 'Allow tickets for relatives' and self.air_ticket_type.number_of_relatives:
                    number_of_relatives = self.air_ticket_type.number_of_relatives

                if not number_of_relatives:
                
                    raise exceptions.ValidationError(
                        "You requested to reserve air tickets for the employee and his relatives, unfortunately your system couldn’t find any relatives linked\
                        to this employee, to add relatives to the selected employee, please go to employee window, then add new relatives. Or you can select\
                        (request air ticket for employee only).")
                checked_relatives = 0
                for line in self.air_ticket_details:
                    if line.check_box and line.relation != 'Employee':
                        checked_relatives += 1
                if not checked_relatives:
                    raise exceptions.ValidationError(
                        "You requested to reserve air tickets for the employee and his relatives, please select the relatives which you want to reserve ticket\
                        for them.")
                if checked_relatives > number_of_relatives:
                    msg = "You selected air ticket for %s relatives, You are allowed only to request air tickets for %s relatives." % (
                        checked_relatives, number_of_relatives)
                    raise exceptions.ValidationError(msg)
            if self.reserve_ticket_for == "Relatives only":
                for line in self.air_ticket_details:
                    if line.check_box and line.relation == 'Employee':
                        raise exceptions.ValidationError(
                            "Not allowed to request a ticket for employee relatives because you requested from your system to reserve ticket for relatives\
                            only.")

    @api.model
    def create(self, vals):
        res = super(air_ticket_request, self).create(vals)
        res.name = self.env['ir.sequence'].next_by_code('mits_a_t.air_ticket_request')
        res.save_id()
        return res

    #@api.one
    def unlink(self):
        if self.state == 'approved':
            raise ValidationError(_("Can not delete while Final approved"))
        super(air_ticket_request, self).unlink()

    #@api.multi
    def write(self, vals):
        # if self.state == 'approved' and not self._context.get('can_edit', False):
        #     raise ValidationError(_("Can not edit while Final approved"))
        return super(air_ticket_request, self).write(vals)

    #@api.one
    @api.depends()
    def save_id(self):
        if not self.id_:
            self.id_ = self.id

    #@api.one
    @api.depends('employee_id')
    def _compute_contract(self):
        for rec in self:
            contracts = self.env['hr.contract'].search(
                [('employee_id', '=', rec.employee_id.id), ('active', '=', True)])
            if len(contracts):
                self.contract_id = contracts[0].id

    @api.onchange('air_ticket_details')
    def _compute_ticket_total_price(self):
        for rec in self:
            total = 0
            for line in rec.air_ticket_details:
                total += line.ticket_price
                if line.check_box and rec.request_reason == 'leave' and line.relation == 'Employee' and line.departure_date:
                    rec.travel_date = line.departure_date
            rec.ticket_total_price = total

    #@api.one
    @api.depends('air_ticket_policy')
    def _compute_cash_allowed(self):
        for rec in self:
            if rec.air_ticket_policy and rec.air_ticket_policy.frequency_air_ticket != 'Not allowed':
                rec.cash_allowed = rec.air_ticket_policy.give_cash_instead_tickets
            else:
                rec.cash_allowed = 'No'

    #@api.one
    @api.depends('air_ticket_policy','air_ticket_type')
    def _compute_relatives_tickets(self):
        for rec in self:
            if rec.request_reason == 'Deputation / business trip' and rec.air_ticket_type:
                rec.relatives_tickets = rec.air_ticket_type.relatives_tickets
            elif rec.air_ticket_policy and rec.air_ticket_policy.frequency_air_ticket != 'Not allowed':
                rec.relatives_tickets = rec.air_ticket_policy.relatives_tickets
            else:
                rec.relatives_tickets = 'Never allow tickets for relatives'

    @api.onchange('cash_allowed')
    def onchange_cash_allowed(self):
        for rec in self:
            if rec.cash_allowed == 'No':
                rec.i_want_to = 'Reserve a ticket through company'

    @api.onchange('relatives_tickets')
    def onchange_relatives_tickets(self):
        for rec in self:
            if rec.relatives_tickets == 'Never allow tickets for relatives':
                rec.reserve_ticket_for = 'Employee only'
            elif rec.relatives_tickets == 'Allow tickets for relatives':
                rec.reserve_ticket_for = 'Employee and his relatives'
            else:
                rec.reserve_ticket_for = ''

    #@api.one
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            # Get details
            vals = []
            for detail in self.air_ticket_details:
                rec = (2, detail.id, False)
                vals.append(rec)
            emp = (0, False, {
                'name': self.employee_id.name,
                'relation': 'Employee',
            })
            vals.append(emp)
            for relative in self.employee_id.relatives:
                relative_vals = (0, False, {
                    'name': relative.name,
                    'relation': relative.type,
                })
                vals.append(relative_vals)
            self.air_ticket_details = vals
        
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)]) if not self.employee_id else self.employee_id
        employee = employee and employee[0] or False
        employees = self.env['hr.employee'].search([])
        if employee and employee.manager:
            return #{'domain': {'employee_id': [('id', 'in', employees.ids)]}}
        if not employee:
            return #{'domain': {'employee_id': [('id', 'in', [])]}}
        if employee and not employee.manager:
            self.employee_id = employee.id
            # Get details
            vals = []
            emp = (0,False,{
                'name': self.employee_id.name,
                'relation': 'Employee',
            })
            vals.append(emp)
            for relative in self.employee_id.relatives:
                # relative_vals.append((0,False,{
                # 'name': relative.name,
                # 'relation': relative.type,
                # }))
                relative_vals = (0,False,{
                'name': relative.name,
                'relation': relative.type,
                })
            
                vals.append(relative_vals)
            self.air_ticket_details = vals
            return {'domain': 
            {
            # 'employee_id': [('id', '=', employee.id)],
                               'leave_request': [('employee_id', '=', employee.id), ('state', '=', 'validate')]}}

            # #@api.multi
            # def write(self, vals):
            #     if self.state == 'approved' and not self._context.get('allow_edit', False):
            #         raise ValidationError(_("You can not edit while approved"))
            #     return super(air_ticket_request, self).write(vals)


class air_ticket_details(models.Model):
    _name = 'air.ticket.details'

    request_id = fields.Many2one('air.ticket.request', _('Air Ticket Details'))
    check_box = fields.Boolean(_('Select'))
    name = fields.Char(_('Name'), readonly=True)
    relation = fields.Char(_('Relation'), readonly=True)
    ticket_type = fields.Selection([('One way', 'One way'),
                                    ('Return', 'Return')], _('Ticket type'))
    departure_date = fields.Date(_('Departure date'))
    departure_airport = fields.Char(_('Departure airport'))
    flight_number = fields.Char(_('Flight number'))
    airlines = fields.Char(_('Airlines'))
    return_date = fields.Date(_('Return date'))
    return_airport = fields.Char(_('Return airport'))
    return_flight_number = fields.Char(_('Return Flight number'))
    return_airlines = fields.Char(_('Airlines'))
    ticket_price = fields.Float(_('Air Ticket Price'))
    notes = fields.Text(_('Notes'))

    # Clear data from ticket type field if check box = false
    @api.onchange('check_box')
    def _onchange_check_box(self):
        for rec in self:
            if not rec.check_box:
                rec.ticket_type = False
                rec.ticket_price = False
                rec.departure_date = False
                rec.return_date = False

    @api.constrains('ticket_price')
    def _check_ticket_price(self):
        for rec in self:
            if rec.ticket_price < 0 and rec.check_box:
                raise exceptions.ValidationError("Air Ticket Price must be Positive")

    @api.constrains('check_box', 'ticket_type')
    def check_selection(self):
        for rec in self:
            if rec.check_box and not rec.ticket_type:
                raise ValidationError(_("Attention !!\n\
                    You forgot to select air ticket type for ( %s )" % (rec.name)))

    @api.onchange('check_box', 'ticket_type')
    def get_ticket_price(self):
        for rec in self:
            rec.ticket_price = 0
            if rec.check_box and rec.ticket_type and not rec.ticket_price:
                if rec.request_id.employee_id.city_id or rec.request_id.employee_id.country_id:
                    source = rec.request_id.employee_id.city_id or rec.request_id.employee_id.country_id
                    price = rec.ticket_type == 'One way' and source.one_way_price or source.return_price
                    price = (
                            rec.ticket_type == 'One way' and rec.request_id.employee_id.country_id.one_way_price or rec.request_id.employee_id.country_id.return_price) if not price else price
                    rec.ticket_price = price


class Contract(models.Model):
    _inherit = 'hr.contract'

    nationality = fields.Many2one('res.country', _('Nationality'), related="employee_id.country_id", readonly=True)
    nationality_type = fields.Selection([('Saudi', 'Saudi'),
                                         ('Non-Saudi', 'Non-Saudi')], _('Nationality type'),
                                        related="employee_id.nationality_type", readonly=True)
    air_ticket_policy = fields.Many2one('air.ticket.type', string='Annual Air Ticket Policy')
    number_of_wives = fields.Integer('Number Of Wives')
    children = fields.Integer('Number Of Children')
    max_child_age = fields.Integer('Max Age For Children')
    total_relatives = fields.Integer('Total relatives included in air tickets', compute='_compute_total')

    #@api.one
    @api.depends('number_of_wives', 'children')
    def _compute_total(self):
        for rec in self:
            rec.total_relatives = rec.number_of_wives + rec.children

    #@api.one
    @api.onchange('air_ticket_policy')
    def onchange_air_ticket_policy(self):
        for rec in self:
            if rec.air_ticket_policy.relatives_tickets == 'Allow tickets for relatives' and rec.marital == 'married':
                rec.number_of_wives = rec.air_ticket_policy.number_of_wives
                rec.children = rec.air_ticket_policy.children
                rec.max_child_age = rec.air_ticket_policy.max_child_age

    #@api.one
    @api.onchange('marital')
    def onchange_marital(self):
        for rec in self:
            if rec.marital != 'married':
                rec.number_of_wives = 0
                rec.children = 0
                rec.max_child_age = 0

    #@api.one
    @api.constrains('number_of_wives', 'children', 'max_child_age')
    def _check_positive(self):
        for rec in self:
            if rec.number_of_wives < 0:
                raise exceptions.ValidationError(_("Number Of Wives cannot be Minus"))
            if rec.children < 0:
                raise exceptions.ValidationError(_("Number Of Children cannot be Minus"))
            if rec.max_child_age < 0:
                raise exceptions.ValidationError(_("Max Age For Children cannot be Minus"))

    @api.onchange('nationality')
    def onchange_nationality(self):
        for rec in self:
            rec.annual_leave_policy = False

    @api.onchange('employee_id')
    def onchange_air_ticket_policy_employee(self):
        for rec in self:
            rec.air_ticket_policy = False

    @api.onchange('nationality_type')
    def onchange_employee_id(self):
        for rec in self:
            if rec.nationality_type == "Non-Saudi":
                return {'domain': {'nationality_type': [('nationality', '=', 'Non-Saudi'), ('state', '=', 'Approved')]}}
                # return {'domain': {[]}}
            if rec.nationality_type == "Saudi":
                return {'domain': {'nationality_type': [('nationality', '=', 'Saudi'), ('state', '=', 'Approved')]}}
                # return {'domain': {[]}}


class air_ticket_for_leave_type(models.Model):
    _inherit = 'hr.leave.type'

    allow_tickets_for_leave = fields.Selection([('Yes', 'Yes'), ('No', 'No')],
                                               _('Allow to request air ticket for this leave'), required=False)
    allowed_air_ticket_id = fields.Many2one('air.ticket.type', 'Allowed air ticket')

    @api.onchange('nationality', 'can_request_air_ticket')
    def clear_allowed_air_ticket_id(self):
        for rec in self:
            rec.allowed_air_ticket_id = False


class leave_type(models.Model):
    _inherit = "hr.leave.type"

    can_request_exit_rentry = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Can request For Exist and R-entry')


class hr_holiday(models.Model):
    _inherit = "hr.leave"

    annual_air_ticket_policy_id = fields.Many2one('air.ticket.type', 'Annual air ticket policy',
                                                  compute='get_annual_air_ticket_policy')
    allow_to_request_air_ticket = fields.Selection(string='Allow to request air ticket',
                                                   related='holiday_status_id.can_request_air_ticket')
    create_air_ticket_request = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                                 string="Create air ticket request for this leave",
                                                 related='holiday_status_id.can_request_air_ticket')
    air_ticket_id = fields.Many2one('air.ticket.request', string="Linked Air-Ticket")
    air_ticket_ids = fields.One2many('air.ticket.request','leave_request', string="Linked Air-Tickets")
    air_ticket_num = fields.Integer()
    can_request_exit_rentry = fields.Selection(related='holiday_status_id.can_request_exit_rentry',
                                               string='Can Request for Exit and Re-entry')

    #@api.one
    @api.depends('contract_id')
    def get_annual_air_ticket_policy(self):
        self.annual_air_ticket_policy_id = self.contract_id.air_ticket_policy

    # #@api.one
    # @api.onchange('allow_to_request_air_ticket')
    # def onchange_allow_to_request_air_ticket(self):
    #     if self.allow_to_request_air_ticket == 'no':
    #         self.create_air_ticket_request = 'no'
    #     else:
    #         self.create_air_ticket_request = 'yes'

    # def action_validate(self):
    #     res = super(hr_holiday, self).action_validate()
    #     for rec in self:
    #         rec.holidays_validate()

    #     return res
    

    #@api.one
    def holidays_validate(self):
        #  and self.type == 'remove'
        
        if self.create_air_ticket_request == 'yes':
            air_ticket_type = self.holiday_status_id.allowed_air_ticket_id
            ctx = dict(self._context, skip_validation=True)
            
            for i in range(0,self.air_ticket_num):
                air_ticket_request = self.with_context(ctx).env['air.ticket.request'].create({
                    'description': "Air ticket request for %s" % (self.employee_id.name),
                    'employee_id': self.employee_id.id,
                    'request_reason': 'leave',
                    'leave_request': self.id,
                    'request_date': time.strftime('%Y-%m-%d'),
                    'reserve_ticket_for': (
                        air_ticket_type.relatives_tickets == 'Allow tickets for relatives')
                        and 'Employee and his relatives' \
                                        or 'Employee only',
                    'i_want_to': self.employee_id.nationality_type == 'Saudi' and 'Cash' or 'Reserve a ticket through company',
                    'air_ticket_type': air_ticket_type.id
                })
                
                air_ticket_request.onchange_employee_id()
                air_ticket_request.get_air_ticket_type()
                air_ticket_request.onchange_travel_date()
                air_ticket_request.review()
                air_ticket_request.reserve_ticket_for = (
                                                                    air_ticket_request.air_ticket_type.relatives_tickets == 'Allow tickets for relatives') and \
                                                        'Employee and his relatives' or 'Employee only'
                
                relative_count = 1
                for line in air_ticket_request.air_ticket_details:
                    if line.relation == 'Employee':
                        line.write({'check_box': True, 'ticket_type': 'Return'})
                    if air_ticket_type.relatives_tickets == 'Allow tickets for relatives':
                        if air_ticket_type.number_of_relatives >= relative_count:
                            line.write({'check_box': True, 'ticket_type': 'Return'})
                            relative_count += 1
                    line.get_ticket_price()
        return super(hr_holiday, self).holidays_validate()


class SkipValidate(models.TransientModel):
    _name = 'validate.wizard'
    air_ticket_request_id = fields.Many2one('air.ticket.request', 'Air ticket request')
    total_price = fields.Float('Total air ticket price', related='air_ticket_request_id.ticket_total_price')
    company_share = fields.Float('Company share', related='air_ticket_request_id.company_share')
    a = fields.Integer('A', related='air_ticket_request_id.employee_id.air_ticket_balance')
    aa = fields.Integer('A', related='a')

    #@api.multi
    def approve_air_ticket(self):
        air_ticket_request = self.env['air.ticket.request'].browse(
            self._context.get('default_air_ticket_request_id', False))
        air_ticket_request.approve(skip=True)

    #@api.multi
    def confirm_company_share(self):
        ctx = dict(self._context,
                   default_air_ticket_request_id=self._context.get('default_air_ticket_request_id', False))
        self.with_context(ctx).air_ticket_request_id.approve(confirm_no_company_share=True)


class AirTicketBalanceAllocation(models.Model):
    _name = "air.ticket.balance.allocation"
    _inherit = ['mail.thread',]
    _description = "Air ticket balance allocation"
    _rec_name = "employee_id"
    _order = "id desc"

    employee_id = fields.Many2one('hr.employee', 'Employee')
    allocated_balance = fields.Integer('Allocated balance')
    allocated_date = fields.Date('Allocated date')
    adjusted_date = fields.Date('Adjusted date', related='employee_id.contract_id.adjusted_date')
    last_allocation_date = fields.Date('Last allocation date', compute='get_last_allocation_date')
    last_allocation_date_ = fields.Date('Last allocation date', )
    reason = fields.Char('Reason')
    auto_create = fields.Boolean('Created automatically')
    air_ticket_request_id = fields.Many2one('air.ticket.request', 'Air ticket request')
    confirmed_uid = fields.Many2one('res.users', 'Confirmed by')
    note = fields.Html('Notes')
    attachment_ids = fields.One2many('air.ticket.balance.attachment', 'air_ticket_balance_id', 'Attachments')
    state = fields.Selection([
        ('new', 'New'),
        ('confirmed', 'Confirmed'),
    ], 'Status', default='new', track_visibility='always')
    by_eos = fields.Boolean('Through EOS')

    #@api.one
    @api.depends()
    def get_last_allocation_date(self):
        self.last_allocation_date = self.last_allocation_date_ or self.employee_id.last_reconciliation_date

    #@api.one
    def reverse_allocation(self):
        raise ValidationError(_("If you want to reverse the effect for this air ticket allocation, you have to manually create a new air ticket allocation with\
         a minus or positive value ( based on the condition)\nUse minus to reduce air ticket balance, use positive values to increase air ticket balance."))

    #@api.one
    def confirm(self):
        if not self.adjusted_date:
            raise ValidationError(_("Sorry !!,Employee must have contract with adjusted date first"))
            
        if self.allocated_date < self.adjusted_date:
            raise ValidationError(_("Configuration Error!!\n\
                    Based on the employee historical data, the employee started to work at ( %s ), we found that you selected that ِAllocation date is \
                    ( %s ).\nIt is not logic that the allocation date is less than the hiring date" % (
            self.adjusted_date, self.allocated_date)))
        # if self.allocated_balance > 0 and self.adjusted_date.split('-')[2] != self.allocated_date.split('-')[
        #     2] and not self.by_eos:
        if self.allocated_balance > 0 and self.adjusted_date.weekday() != self.allocated_date.weekday() and not self.by_eos:
            raise ValidationError(_("Attention!!\n\
                    We found that you configured your system give the employee a monthly Air ticket  balance at a certain day from each month ( %s ) , now you are\
                    trying to allocate air ticket balance on a different day ( %s ) . We highly recommend to use a monthly base (except the termination cases or \
                    EOC cases)" % (self.adjusted_date, self.allocated_date)))
        self.last_allocation_date_ = self.employee_id.last_reconciliation_date
        self.state = 'confirmed'
        self.confirmed_uid = self.env.user.id

    @api.constrains('employee_id')
    def check_contract(self):
        if not self.employee_id.contract_id.id:
            raise ValidationError(_("Configuration Error!\n\
                    Not allowed to allocate air ticket balance because their is no active contract for the selected employee."))

    #@api.one
    def unlink(self):
        if self.state == 'confirmed':
            raise ValidationError(_("Not allowed to delete a confirmed transaction."))
        return super(AirTicketBalanceAllocation, self).unlink()

    @api.onchange('employee_id')
    def clear_balance(self):
        self.allocated_balance = False


class AirTicketBalanceAttachment(models.Model):
    _name = "air.ticket.balance.attachment"
    _description = "Air ticket balance allocation Attachment"

    air_ticket_balance_id = fields.Many2one('air.ticket.balance.allocation', 'Job')
    name = fields.Char('Name')
    file = fields.Binary('File')
    note = fields.Char('Notes')


class AirTicketRequestAttachment(models.Model):
    # _inherit = "attachment.file.save"
    _name = "air.ticket.request.attachment"

    air_ticket_request_id = fields.Many2one('air.ticket.request', 'Air ticket request')
    source_id = fields.Many2one('air.ticket.request', 'Air ticket request')
    note = fields.Char('Notes')
    model = fields.Char()
    res_id = fields.Float(string='res_id')
    filename = fields.Char('File name')
    file = fields.Binary(string='File', store=True)
    name = fields.Char(string='Name', required=True)

    @api.model
    def get_file_name(self):
        return "%s-%s%s-%s" % (str(int(self.id)), str(int(self.res_id)), self.name, self.filename)

class Employee(models.Model):
    _inherit = "hr.employee"
    air_ticket_balance = fields.Integer('Air ticket allocation balance', compute='get_air_ticket_balance')
    air_ticket_balance_button = fields.Integer('Air ticket allocation balance', compute='get_air_ticket_balance')
    last_reconciliation_date = fields.Date('Last  Air Ticket Reconciliation Date',
                                           compute='get_last_ait_ticket_allocation_date')

    #@api.one
    @api.depends()
    def get_air_ticket_balance(self):
        if not self.contract_id or not self.contract_id.air_ticket_policy:
            self.air_ticket_balance = 0
            self.air_ticket_balance_button = 0
        else:
            frequency_air_ticket = self.contract_id.air_ticket_policy.frequency_air_ticket
            if frequency_air_ticket in ['Not allowed', 'One time per contract']:
                self.air_ticket_balance = 0
                self.air_ticket_balance_button = 0
            if frequency_air_ticket == 'one time each':
                allocations = self.env['air.ticket.balance.allocation'].search([
                    ['employee_id', '=', self.id],
                    ['state', '=', 'confirmed'],
                ], order='allocated_date desc')
                total_allocation = sum([a.allocated_balance for a in allocations])
                maximum_accumulated_balance = self.contract_id.air_ticket_policy.maximum_accumulated_balance
                self.air_ticket_balance = min([total_allocation, maximum_accumulated_balance])
                if self.contract_id.air_ticket_policy.number_of_months != 0:
                    self.air_ticket_balance_button = min([total_allocation,
                                                      maximum_accumulated_balance]) / self.contract_id.air_ticket_policy.number_of_months and self.contract_id.air_ticket_policy.number_of_months or 0
                else:
                    raise ValidationError(
                _("Data Error !!\n Number Of Months in Contract is Zero"))
            if frequency_air_ticket == 'Unlimited air tickets based on request condition':
                self.air_ticket_balance = 1000
                self.air_ticket_balance_button = 1000

    #@api.one
    @api.depends()
    def get_last_ait_ticket_allocation_date(self):
        self.last_reconciliation_date = False
        allocations = self.env['air.ticket.balance.allocation'].search([
            ['employee_id', '=', self.id],
            ['state', '=', 'confirmed'],
            ['allocated_balance', '>', 0]
        ], order='allocated_date desc')
        if allocations:
            self.last_reconciliation_date = allocations[0].allocated_date

    #@api.multi
    def open_air_ticket_allocations(self):
        return {
            'domain': [['employee_id', '=', self.id]],
            'name': _('Air ticket balance allocation'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'air.ticket.balance.allocation',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_employee_id': self.id}
        }


class Countries(models.Model):
    _inherit = "res.country"

    one_way_price = fields.Float('One way price')
    return_price = fields.Float('Return price')

    @api.constrains('one_way_price', 'return_price')
    def check_prices(self):
        if self.one_way_price < 0 or self.return_price < 0:
            raise ValidationError(
                _("Data Error !!\nAverage air ticket price ( one war / Return ) must be greater than zero"))


class res_country_state(models.Model):
    _inherit = "res.country.state"

    one_way_price = fields.Float('One way price')
    return_price = fields.Float('Return price')

    @api.constrains('one_way_price', 'return_price')
    def check_prices(self):
        if self.one_way_price < 0 or self.return_price < 0:
            raise ValidationError(
                _("Data Error !!\nAverage air ticket price ( one war / Return ) must be greater than zero"))
