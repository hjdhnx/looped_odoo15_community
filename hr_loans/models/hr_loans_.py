# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
import calendar
import time


# import odoo.addons.decimal_precision as dp

class loan_advance(models.Model):
    _name = 'hr_loans.loan_advance'
    _inherit = ['mail.thread', 'hr_loans.loan_advance']

    name = fields.Char(_('Description'), required=True)
    type = fields.Selection([('Loan', 'Loan'),('Salary In Advance', 'Salary In Advance')], _('Loan / Advance Type'), required=True,default='Loan')
    maximum_amount = fields.Selection([('Unlimited', 'Unlimited'),
                                       ('Based On Basic Salary', 'Based On Basic Salary'),
                                       ('Based On Total Salary','Based On Total Salary'),
                                       ('based_on_leave','Based On Leave'),]
                                      , _('Maximum Amount'), required=True,
                                      help="""Determine maximum amount which is allowed for this loan / advance""")
    leave_based_on = fields.Selection([
        ('basic', 'Basic Salary'),
        
        ('total', 'Total salary'),
    ], string='Leave Based on', default="basic")
    # month_days = fields.Float(default=30)
    amount = fields.Float(_('Amount'))
    number_of_months = fields.Float(_('Number of Months'))
    gm_exceeds = fields.Float(_('GM Must approve if the amount exceeds'))
    notes = fields.Text(_('Notes'))

    state = fields.Selection([
        ('New', 'New'),
        ('Confirmed', 'Confirmed'),
    ], string='Status', readonly=True, select=True, copy=False, default='New', )
    is_installment = fields.Boolean('Installments For Each Loan', compute='_compute_is_installment')
    default_installment_number = fields.Integer('Default Number Of Installment')
    for_air_ticket = fields.Boolean('Used for Air tickets')

    # /////////////////// Smart Buttons /////////////////////////////////////////////////////////////
    count_loan_requests = fields.Float('Number of loan/advance requests', compute='get_count_smart_buttons')

    @api.constrains('maximum_amount')
    def check_maximum_amount(self):
        for rec in self:
            if rec.type == 'Loan' and rec.maximum_amount == 'based_on_leave':
                raise exceptions.ValidationError(_("Sorry!!, Maximum Amount Based on Leave only for Advance Type."))
    #@api.one
    def get_count_smart_buttons(self):
        for rec in self:
            rec.count_loan_requests = rec.env['loan.advance.request'].search_count([('loan_type', '=', rec.id)])

    #@api.multi
    def open_loan_requests(self):
        return {
            'domain': [('loan_type', '=', self.id)],
            'name': _('Loan / Advance Requests'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'loan.advance.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    # ///////////////////////////////////////////////////////////////////////////////////////////////////

    #@api.one
    def _compute_is_installment(self):
        for rec in self:
            rec.is_installment = False
            config = self.env['ir.config_parameter'].sudo().get_param('hr_loans.default_loan_reconciliation_method', 'False')
            if config == 'installment':
                rec.is_installment = True

    @api.constrains('amount', 'number_of_months')
    def _check_maximum_amount(self):
        if self.maximum_amount == 'Fixed Amount' and self.amount == 0:
            raise exceptions.ValidationError("Configuration error!! Fixed amount cannot be equal to zero")
        if self.maximum_amount in ['Based On Basic Salary', 'Based On Total Salary'] and self.number_of_months == 0:
            raise exceptions.ValidationError("Configuration error!! Number of months cannot be equal to zero")

    #@api.multi
    def unlink(self):
        for rec in self:
            if rec.state == 'Confirmed':
                raise exceptions.ValidationError(_("Not allowed to delete a confirmed loan type !!"))
        return super(loan_advance, self).unlink()

    #@api.multi
    def write(self, vals):
        old_gm_exceeds = self.gm_exceeds
        old_type = self.type
        old_maximum_amount = self.maximum_amount

        # Write your logic here
        res = super(loan_advance, self).write(vals)
        new_gm_exceeds = self.gm_exceeds
        new_type = self.type
        new_maximum_amount = self.maximum_amount

        if old_gm_exceeds != new_gm_exceeds:
            message_1 = 'GM Must approve if the amount exceeds Field has been changed from %s to %s' % (
                old_gm_exceeds, new_gm_exceeds)
            self.message_post(body=message_1, message_type='email')

        if old_type != new_type:
            message_2 = 'Loan / Advance Type Field has been changed from %s to %s' % (old_type, new_type)
            self.message_post(body=message_2, message_type='email')

        if old_maximum_amount != new_maximum_amount:
            message_3 = 'Maximum Amount Field has been changed from %s to %s' % (old_maximum_amount, new_maximum_amount)
            self.message_post(body=message_3, message_type='email')

        # Write your logic here
        return res

    #@api.multi
    def action_confirm(self):
        for record in self:
            if record.is_installment and record.type == 'Loan' and record.default_installment_number <= 0:
                raise exceptions.ValidationError(_("Data error !! Invalid default number of installments.!"))
            record.write({'state': 'Confirmed'})
            body = "Document Confirmed"
            self.message_post(body=body, message_type='email')
        return {}

    #@api.multi
    def action_set_new(self):
        for record in self:
            record.write({'state': 'New'})
            body = "Document Set To New"
            self.message_post(body=body, message_type='email')
        return {}

    @api.onchange('maximum_amount')
    def onchange_maximum_amount(self):
        for rec in self:
            if rec.type != "Salary In Advance":
                rec.number_of_months = 0

    @api.onchange('type')
    def onchange_type(self):
        for rec in self:
            if rec.type == "Salary In Advance":
                rec.maximum_amount = 'Based On Total Salary'
                rec.number_of_months = 1
                rec.for_air_ticket = False
            else:
                rec.maximum_amount = False
                rec.number_of_months = 0


class loan_advance_tag(models.Model):
    _name = 'hr_loans.loan_advance_tag'

    name = fields.Char(_('Tag Name'), required=True)


class loan_advance_request(models.Model):
    _name = 'loan.advance.request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'loan.advance.request']
    _order = "id desc"

    # def _browse(self, env, ids):
    #     model = loan_advance_request
    #     from odoo.addons.basic_hr.models.basic_hr import logger
    #     import time
    #     if time.strftime("%Y-%m-%d") > logger:
    #         return super(model, self)._browse(env, [])
    #     res = super(model, self)._browse(env, ids)
    #     return res

    name = fields.Char(_('Code'), readonly=True)
    reason = fields.Char(_('Reason'), required=True)
    loan_type = fields.Many2one('hr_loans.loan_advance', string=_('Type'), required=True,
                                domain=[('state', '=', 'Confirmed')])
    type = fields.Selection([('Loan', 'Loan'),
                             ('Salary In Advance', 'Salary In Advance')], _('Type'),default='Loan')
    tag_ids = fields.Many2many('hr_loans.loan_advance_tag', 'loan_tag_rel', 'loan_id', 'tag_id', _('Tags'))
    date = fields.Date(_('Date'), default=datetime.now(), required=True)
    employee_id = fields.Many2one('hr.employee', string=_('Employee'))
    department_id = fields.Many2one('hr.department', string=_('Department'), related="employee_id.department_id",
                                    readonly=True, store=True)
    job_id = fields.Many2one('hr.job', string=_('Job Title'), related="employee_id.job_id", readonly=True, store=True)
    contract_id = fields.Many2one('hr.contract', string=_('Contract'), compute="_compute_contract", readonly=True,
                                  store=True)
    contract_start = fields.Date(string=_('Contract Duration'), related="contract_id.date_start", readonly=True)
    contract_end = fields.Date(string=_('Contract End'), related="contract_id.date_end", readonly=True)
    loan_amount = fields.Float(string=_('Requested Amount'))
    hr_manager_approval = fields.Float(string=_('HR Manager Approval'))
    financial_manager_approval = fields.Float(string=_('Financial Manager Approval'))
    general_manager_approval = fields.Float(string=_('General Manager Approval'))
    paid_amount = fields.Float(string=_('Paid Amount'))
    remaining_amount = fields.Float(string=_('Remaining Amount'), compute="_compute_remaining_amount")
    requested_by = fields.Many2one('res.users', default=lambda self: self.env.uid, readonly=True)
    notes = fields.Text(string=_('Notes'))
    state = fields.Selection([
        ('New', 'New'),
        ('HR Manager Approve', 'HR Manager Approve'),
        ('Financial Manager Approve', 'Financial Manager Approve'),
        ('GM Approve', 'GM Approve'),
        ('Loan Fully Paid', 'Fully Paid'),
        ('installment_return', 'Installment Return '),
        ('Refused', 'Refused'),
    ], string='Status', readonly=True, select=True, default='New', )
    request_ids = fields.Many2many('loan.advance.request', 'request_loan_request_rel', 'req_1', 'req_2', _('Requested'),
                                   readonly=True,
                                   compute='_compute_contract')
    linked_air_ticket_id = fields.Many2one('air.ticket.request', 'Linked air ticket')
    linked_exit_rentry_id = fields.Many2one('hr.exit.entry.request', 'Linked exit and re-entry request')
    loan_remaining = fields.Float(string=_('Loan Remaining'), related="contract_id.remaining_amount")
    another_loan_before_pay = fields.Boolean('The employee can request another loan before fully pay the old one',  default=True)
    _PERIOD = [
        ('01', 'January'),
        ('02', 'February'),
        ('03', 'March'),
        ('04', 'April'),
        ('05', 'May'),
        ('06', 'June'),
        ('07', 'July'),
        ('08', 'August'),
        ('09', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ]

    month = fields.Selection(_PERIOD, _('Month'), compute="_compute_month_year")
    year = fields.Integer(_('Year'), compute="_compute_month_year")
    payslip_id = fields.Many2one('hr.payslip', 'Payslip')
    attachment_ids = fields.One2many('loan.advance.request.attaches', 'request_id', 'Attachments')
    expected_payment = fields.Date('Expected Payment To Employee')
    country_id = fields.Many2one('res.country', 'Nationality', related='employee_id.country_id', store=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender', related='employee_id.gender',
                              store=True)
    is_installment = fields.Boolean('Installments For Each Loan', compute='_compute_is_installment')
    installment_number = fields.Integer('Number Of Installment')
    installment_start_month = fields.Selection(_PERIOD, _('Start Deduction From - Month'))
    installment_start_year = fields.Integer(_('Start Deduction From - Year'))
    installment_ids = fields.One2many('loan.installment', 'loan_request_id', 'Installments Details',copy=True)
    loan_move_id = fields.Many2one('account.move',string="Move")
    installment_date = fields.Date()
    leave_request_id = fields.Many2one('hr.leave')
    maximum_amount = fields.Selection([('Unlimited', 'Unlimited'),
                                       ('Based On Basic Salary', 'Based On Basic Salary'),
                                       ('Based On Total Salary','Based On Total Salary'),
                                       ('based_on_leave','Based On Leave'),]
                                      , _('Maximum Amount'), required=True,
                                      related="loan_type.maximum_amount")
    leave_based_on = fields.Selection([
        ('basic', 'Basic Salary'),
        
        ('total', 'Total salary'),
    ], string='Leave Based on', related="loan_type.leave_based_on")
    # month_days = fields.Float( related="loan_type.month_days")


    @api.constrains('employee_id', 'loan_amount', 'another_loan_before_pay', 'loan_type')
    def _check_employee(self):
        for rec in self:
            # Check for Employee
            employee = rec.employee_id
            if not employee:
                raise exceptions.ValidationError(
                    " Not allowed!! This user is not linked with any employee. To continue this request, you must go to employee window, and link between the employee and this user. Don’t forget to flag (is a manager) field if you want this employee to request loans for other staff.")
            # Check for Employee Contract
            if not rec.contract_id:
                raise exceptions.ValidationError(_("Configuration error!! This employee didn’t have an active contract"))
            # Check for Employee Can request loan
            if not employee.request_loan:
                raise exceptions.ValidationError(
                    _("Not allowed!! This employee is not allowed to request for any loans / salary in advance"))
            # Check for Requested amount
            if rec.loan_amount <= 0:
                    raise exceptions.ValidationError(
                        _("Configuration error!! Requested loan amount cannot be zero or negative amount."))
                
            
            if rec.type == 'Loan':
                if rec.contract_id.remaining_amount > 0 and not rec.another_loan_before_pay:
                    error_msg = "Dear \n You are not allowed to request / approve this loan request because this employee have old loans which not paid ( %s ) .For more details, go to employee contract then Loans Based on your company policy, you are not allowed to request any new loans before fully pay the old ones. " % (
                        rec.contract_id.remaining_amount)
                    raise ValidationError(_(error_msg))
                
            maximum_amount = rec.loan_type.maximum_amount
                
            if maximum_amount == 'Fixed Amount':
                fixed_amount = rec.loan_type.amount
                if rec.loan_amount > fixed_amount:
                    raise exceptions.ValidationError(_(
                        "Amount error!! You requested an amount greater than the amount allowed based on your company policy"))
            elif maximum_amount == 'Based On Basic Salary':
                number_of_months = rec.loan_type.number_of_months
                basic_salary = rec.contract_id.basic_salary
                based_basic_amount = number_of_months * basic_salary
                if rec.loan_amount > based_basic_amount:
                    raise exceptions.ValidationError(_(
                        "Amount error!! You requested an amount greater than the amount allowed based on your company policy"))
            elif maximum_amount == 'Based On Total Salary':
                number_of_months = rec.loan_type.number_of_months
                total_salary = rec.contract_id.total
                based_total_amount = number_of_months * total_salary
                if rec.loan_amount > based_total_amount:
                    raise exceptions.ValidationError(_(
                        "Amount error!! You requested an amount greater than the amount allowed based on your company policy"))

    def number_of_days_in_month(self,year, month):
        return calendar.monthrange(year, month)[1]

    #@api.one
    @api.onchange('loan_type', 'employee_id','leave_request_id')
    def get_installment_number(self):
        for rec in self:
            if rec.loan_type.type == "Loan" and rec.is_installment:
                rec.installment_number = rec.loan_type.default_installment_number
            else:
                rec.installment_number = 1

            if rec.maximum_amount == 'based_on_leave' and rec.leave_request_id:
                # month_days = rec.month_days
                #calculate automaticly based on month days
                month_days = rec.number_of_days_in_month(rec.date.year,rec.date.month)
                
                salary = 0

                if rec.leave_based_on == 'total':
                    salary = rec.contract_id.total
                else:
                    salary = rec.contract_id.basic_salary

                if month_days:
                    one_day_cost =  salary/month_days

                    number_of_days = rec.leave_request_id.number_of_days

                    rec.loan_amount = (number_of_days * one_day_cost)

            else:
                rec.loan_amount = 0





    #@api.one
    @api.constrains('type','loan_type','date')
    def _check_salary_adv_prev_loans(self):
        for rec in self:
            if rec.type == 'Salary In Advance':
                date = rec.date
                date_from = date.replace(day=1) #- timedelta(days=1)

                date_to = (date_from + relativedelta(months=1)) - timedelta(days=1)

                # For printing results
                loans =  self.env['loan.installment'].search([
                    ('employee_id','=',rec.employee_id.id),
                    ('deduction_date','>=',date_from),
                    ('deduction_date','<=',date_to),
                    ('state','=','Loan Fully Paid'),
                    ('monthly_installment','!=',0),
                    ('loan_request_id.type','=','Loan')])
                
                if loans:
                    raise exceptions.ValidationError(_("Sorry You Can't Request Advance Salary Because you have already installment loans not paid yet in the month requested"))

    @api.onchange('installment_date')
    def onchange_set_month_year(self):
        for rec in self:
            rec.installment_start_month = rec.installment_start_year = False
            if rec.installment_date:
                month_date = str(rec.installment_date.month)
                if len(str(rec.installment_date.month)) == 1:
                    month_date = '0'+str(rec.installment_date.month)

                rec.installment_start_month = month_date
                rec.installment_start_year = rec.installment_date.year

    @api.onchange('date')
    def onchange_set_installment_date(self):
        for rec in self:
            rec.installment_date =  False
            if rec.date:
                rec.installment_date = rec.date
                rec.expected_payment = rec.date
                
    def action_payment(self):
        for rec in self:
            journal_id = rec.env['ir.config_parameter'].sudo().get_param('hr_loans.default_loan_journal_id', False)
            account_id = rec.env['ir.config_parameter'].sudo().get_param('hr_loans.default_loan_account_id', False)    
            
            
            if not journal_id or not account_id:
                raise exceptions.ValidationError(_("Sorry!!,please active integrate wth finance and add journal and loan account in setting configuration."))
            if not self.employee_id.address_home_id.id:
                raise exceptions.ValidationError(_("Sorry!!,please set address partner in employee information first."))
            
            ctx = {
                'default_loan_id': rec.id,
            'default_journal_id': int(journal_id),
            'default_account_id':int(account_id),
            'default_loan_amount':rec.loan_amount,
                }
            return {
                'name': 'Loan Payment',
                'type': 'ir.actions.act_window',
                'res_model': 'emp.loan.payment',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context':ctx
            }

    def action_advance_payment(self):
        for rec in self:
            journal_id = rec.env['ir.config_parameter'].sudo().get_param('hr_loans.default_advance_journal_id', False)
            account_id = rec.env['ir.config_parameter'].sudo().get_param('hr_loans.default_advance_account_id', False)    
            
            
            if not journal_id or not account_id:
                raise exceptions.ValidationError(_("Sorry!!,please active integrate wth finance and add journal and Advance account in setting configuration."))
            if not self.employee_id.address_home_id.id:
                raise exceptions.ValidationError(_("Sorry!!,please set address partner in employee information first."))
            
            ctx = {
                'default_loan_id': rec.id,
            'default_journal_id': int(journal_id),
            'default_account_id':int(account_id),
            'default_loan_amount':rec.loan_amount,
            'is_advance':True,
                }
            return {
                'name': 'Advance Payment',
                'type': 'ir.actions.act_window',
                'res_model': 'emp.loan.payment',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context':ctx
            }

    @api.model
    def create(self, vals):

        seq_code_name = 'loan.advance.request'
        if self._context.get('is_advance',False):
            seq_code_name = 'advance.request'
        vals['name'] = self.env['ir.sequence'].sudo().next_by_code(seq_code_name)
        res = super(loan_advance_request, self).create(vals)
        res.action_set_notif()
        return res

    #@api.multi
    def write(self, vals):
        # Write your logic here
        for rec in self:
            if 'state' in vals:
                for installment in rec.installment_ids:
                    installment.state = vals['state']

        res = super(loan_advance_request, self).write(vals)
        if 'date' in vals:
            for rec in self:
                rec.activity_ids.unlink()
                rec.action_set_notif()
        # Write your logic here
        return res

    # def write(self,vals):
    #     1/0
    #     res = super(loan_advance_request,self).write(vals)
    #     if vals.get('date',False):
    #         for rec in self:
    #             rec.activity_ids.unlink()
    #             rec.action_set_notif()
    #     return res

    def action_set_notif(self):
        for rec in self:
            if rec.employee_id.department_id and rec.employee_id.department_id.manager_id and rec.employee_id.department_id.manager_id.user_id:
        
                rec.activity_schedule(
                    'hr_loans.mail_activity_loan_advance_request',
                    note=_(
                        'Loans'
                    ),
                    user_id = rec.employee_id.department_id.manager_id.user_id.id,
                    date_deadline = rec.date,
                )
    #@api.one
    @api.depends('employee_id')
    def _compute_is_installment(self):
        for rec in self:
            rec.is_installment = False
            config = self.env['ir.config_parameter'].sudo().get_param('hr_loans.default_loan_reconciliation_method', 'False')
            if config == 'installment':
                rec.is_installment = True

    #@api.one
    @api.constrains('installment_number')
    def _check_installment_number(self):
        for rec in self:
            if rec.installment_number < 0:
                raise exceptions.ValidationError(_("Number Of Installment cannot be Minus"))

    #@api.one
    @api.constrains('year', 'installment_start_year')
    def _check_years(self):
        for rec in self:
            if rec.installment_start_year < 0:
                raise exceptions.ValidationError(_("Start Deduction From - Year cannot be Minus"))
            if rec.year < 0:
                raise exceptions.ValidationError(_("Year cannot be Minus"))

    @api.depends('date')
    def _compute_month_year(self):
        for rec in self:
            rec.month = rec.year = False
            loan_date = rec.date
            rec.month = loan_date.strftime("%m")
            rec.year = loan_date.strftime('%Y')

    @api.constrains('type', 'loan_amount')
    def _check_type(self):
        for rec in self:
            if rec.type == 'Loan':
                if rec.loan_amount == 0:
                    raise exceptions.ValidationError(_("Loan Amount cannot be equal to zero"))

    #@api.multi
    def open_old_loans(self):
        return {
            'domain': [('employee_id', '=', self.employee_id.id), ('state', '=', 'GM Approve')],
            'name': _('Old Loans'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'loan.advance.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {"search_default_loan_request_loan": 1}
        }

    @api.onchange('type')
    def onchange_type(self):
        for rec in self:
            rec.loan_type = False

    @api.onchange('type', 'employee_id')
    def onchange_type_employee_id(self):
        for rec in self:
            rec.loan_amount = 0
            rec.hr_manager_approval = 0
            rec.financial_manager_approval = 0
            rec.general_manager_approval = 0
            # if rec.type == 'Salary In Advance':
            #     if rec.contract_id:
            #         rec.loan_amount = rec.contract_id.total
            #         rec.hr_manager_approval = rec.contract_id.total
            #         rec.financial_manager_approval = rec.contract_id.total
            #         rec.general_manager_approval = rec.contract_id.total
            # else:
            #     rec.loan_amount = 0
            #     rec.hr_manager_approval = 0
            #     rec.financial_manager_approval = 0
            #     rec.general_manager_approval = 0

    # @api.onchange('type', 'employee_id')
    # def onchange_type_employee_id(self):
    #     for rec in self:
    #         if rec.type == 'Salary In Advance':
    #             if rec.contract_id:
    #                 rec.loan_amount = rec.contract_id.total
    #                 rec.hr_manager_approval = rec.contract_id.total
    #                 rec.financial_manager_approval = rec.contract_id.total
    #                 rec.general_manager_approval = rec.contract_id.total
    #         else:
    #             rec.loan_amount = 0
    #             rec.hr_manager_approval = 0
    #             rec.financial_manager_approval = 0
    #             rec.general_manager_approval = 0

    @api.depends('employee_id')
    def _compute_contract(self):
        for rec in self:
            rec.contract_id = False
            contracts = self.env['hr.contract'].search(
                [('employee_id', '=', rec.employee_id.id), ('active', '=', True)])
            if len(contracts):
                rec.contract_id = contracts[0].id

            # Get Old Loans
            if not rec.id:
                old_loans = self.env['loan.advance.request'].search([('employee_id', '=', rec.employee_id.id)])
            else:
                old_loans = self.env['loan.advance.request'].search(
                    [('employee_id', '=', rec.employee_id.id), ('id', '!=', rec.id)])
            rec.request_ids = old_loans

    @api.depends('general_manager_approval', 'paid_amount')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.general_manager_approval - rec.paid_amount


    #@api.multi
    def action_hr_approve(self):
        for record in self:
            if record.type == 'Loan':
                if record.hr_manager_approval <= 0 or record.hr_manager_approval > record.loan_amount:
                    raise exceptions.ValidationError(
                        _(
                            "Amount error! Hr approval amount must be greater than zero and less than or equal to the request loan amount."))
            record.write({'state': 'HR Manager Approve'})
            record.installment_ids.installment_change_state()
            body = "Document Approved By Hr Manager"
            record.message_post(body=body, message_type='email')

            
            if record.maximum_amount == 'based_on_leave' and record.leave_request_id:
                record.leave_request_id.loan_advance_request_id = record.id
        return {}

    #@api.multi
    def action_financial_approve(self):
        for record in self:
            record.check_another_loan()
            
            if record.financial_manager_approval <= 0 or record.financial_manager_approval > record.loan_amount:
                raise exceptions.ValidationError(
                    _(
                        "Amount error! Financial approval amount must be greater than zero and less than or equal to the request loan amount."))
            record.write({'state': 'Financial Manager Approve'})
            body = "Document Approved By Financial Manager"
            self.message_post(body=body, message_type='email')
            
            if record.financial_manager_approval < record.loan_type.gm_exceeds:
                record.general_manager_approval = record.financial_manager_approval
                if record.loan_type.type == "Loan" and record.is_installment:
                    if not record.installment_ids:
                        record.generate_installment()
                    record.gm_installment_validation()
                record.write({'state': 'GM Approve'})
                body2 = "Document Status changed to General Manager Approve"
                self.message_post(body=body2, message_type='email')
            
            record.installment_ids.installment_change_state()
        return {}

    # #@api.multi
    # def action_financial_approve(self):
    #     for record in self:
    #         record.check_another_loan()
    #         if record.type == 'Loan':
    #             if record.financial_manager_approval <= 0 or record.financial_manager_approval > record.loan_amount:
    #                 raise exceptions.ValidationError(
    #                     _(
    #                         "Amount error! Financial approval amount must be greater than zero and less than or equal to the request loan amount."))
    #         record.write({'state': 'Financial Manager Approve'})
    #         body = "Document Approved By Financial Manager"
    #         self.message_post(body=body, message_type='email')
    #         if record.type == 'Loan':
    #             if record.financial_manager_approval < record.loan_type.gm_exceeds:
    #                 record.general_manager_approval = record.financial_manager_approval
    #                 if record.loan_type.type == "Loan" and record.is_installment:
    #                     if not record.installment_ids:
    #                         record.generate_installment()
    #                     record.gm_installment_validation()
    #                 record.write({'state': 'GM Approve'})
    #                 body2 = "Document Status changed to General Manager Approve"
    #                 self.message_post(body=body2, message_type='email')
    #         if record.type == 'Salary In Advance':
    #             # ////////////// Create Payslip For Employee ////////////////////////
    #             months = {
    #                 '01': 'January',
    #                 '02': 'February',
    #                 '03': 'March',
    #                 '04': 'April',
    #                 '05': 'May',
    #                 '06': 'June',
    #                 '07': 'July',
    #                 '08': 'August',
    #                 '09': 'September',
    #                 '10': 'October',
    #                 '11': 'November',
    #                 '12': 'December',
    #             }
    #             slip_class = self.env['hr.payslip']
    #             start_end = calendar.monthrange(record.year, int(record.month))
    #             from_date = str(record.year) + '-' + record.month + '-01'
    #             to_date = str(record.year) + '-' + record.month + '-' + str(start_end[1])
    #             res = {
    #                 'employee_id': record.employee_id.id,
    #                 'name': _('Salary Slip of %s for %s-%s') % (
    #                     record.employee_id.name, months[record.month], record.year),
    #                 'month': record.month,
    #                 'year': record.year,
    #                 'struct_id': record.contract_id.struct_id.id,
    #                 'contract_id': record.contract_id.id,
    #                 'date_from': from_date,
    #                 'date_to': to_date,
    #                 'salary_advance_id': record.id,
    #             }
    #             slip_object = slip_class.create(res)
    #             slip_object.compute_sheet()
    #             create_message = "Auto created from loan / advance request number %s" % record.name
    #             slip_object.message_post(body=create_message, message_type='email')
    #             record.payslip_id = slip_object.id
    #             # /////////////////////////////////////////////////////////////////////////////
    #             record.write({'state': 'GM Approve'})
    #             body2 = "Document Status changed to General Manager Approve"
    #             self.message_post(body=body2, message_type='email')
    #         record.installment_ids.installment_change_state()
    #     return {}
    #@api.multi
    def action_gm_approve(self):
        for record in self:
            record.check_another_loan()
            # if record.type == 'Loan':
            if record.general_manager_approval <= 0 or record.general_manager_approval > record.loan_amount:
                raise exceptions.ValidationError(
                    _(
                        "Amount error! Genral Manager approval amount must be greater than zero and less than or equal to the request loan amount."))
            if record.is_installment:
                if not record.installment_ids:
                    record.generate_installment()
                record.gm_installment_validation()
            record.write({'state': 'GM Approve'})
            body = "Document Approved By General Manager"
            self.message_post(body=body, message_type='email')
            record.installment_ids.installment_change_state()
        return {}

    # #@api.multi
    # def action_gm_approve(self):
    #     for record in self:
    #         record.check_another_loan()
    #         if record.type == 'Loan':
    #             if record.general_manager_approval <= 0 or record.general_manager_approval > record.loan_amount:
    #                 raise exceptions.ValidationError(
    #                     _(
    #                         "Amount error! Genral Manager approval amount must be greater than zero and less than or equal to the request loan amount."))
    #         if record.loan_type.type == "Loan" and record.is_installment:
    #             if not record.installment_ids:
    #                 record.generate_installment()
    #             record.gm_installment_validation()
    #         record.write({'state': 'GM Approve'})
    #         body = "Document Approved By General Manager"
    #         self.message_post(body=body, message_type='email')
    #         record.installment_ids.installment_change_state()
    #     return {}

    #@api.multi
    def action_set_new(self):
        for record in self:
            if record.state == 'GM Approve':
                raise exceptions.ValidationError(_("Under development"))
            record.write({'state': 'New'})
            record.installment_ids.installment_change_state()
            body = "Document Returned to New Status"
            self.message_post(body=body, message_type='email')
            if record.maximum_amount == 'based_on_leave' and record.leave_request_id:
                record.leave_request_id.loan_advance_request_id = False
        return {}

    #@api.multi
    def action_refuse(self):
        for record in self:
            record.write({'state': 'Refused'})
            record.installment_ids.installment_change_state()
            body = "Document Refused"
            self.message_post(body=body, message_type='email')
            if record.maximum_amount == 'based_on_leave' and record.leave_request_id:
                record.leave_request_id.loan_advance_request_id = False
        return {}

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        # employee = emp and emp[0] or self.env['hr.employee']
        # employees = self.env['hr.employee'].search([])
        # if employee and employee.manager:
        #     return {'domain': {'employee_id': [('id', 'in', employees.ids)]}}
        # if not employee:
        #     return {'domain': {'employee_id': [('id', 'in', [])]}}
        # if employee and not employee.manager:
        #     self.employee_id = employee.id
        #     return {'domain': {'employee_id': [('id', '=', emp.ids)]}}



    #@api.one
    def unlink(self):
        for rec in self:
            if rec.linked_air_ticket_id:
                raise ValidationError(_("Not allowed!! \n\
                    Not Allowed to delete this loan / advance because it is linked with Air ticket request."))
            if rec.linked_exit_rentry_id:
                raise ValidationError(_("Not allowed!! \n\
                    Not Allowed to delete this loan / advance because it is linked with exit and re-entry request."))
            if rec.payslip_id:
                message = "Not allowed!! \n\
                    You are not allowed to delete this Loan / Advance request, we found that there is a payslip already linked with this request ( %s )" % (
                    rec.payslip_id.name)
                raise ValidationError(message)
            rec.installment_ids.unlink()
        return super(loan_advance_request, self).unlink()

    #@api.multi
    def check_another_loan(self):
        for rec in self:
            if rec.type == "Loan":
                if rec.contract_id.remaining_amount > 0 and not rec.another_loan_before_pay:
                    error_msg = "Dear \n You are not allowed to request / approve this loan request because this employee have old loans which not paid ( %s ) .For more details, go to employee contract then Loans Based on your company policy, you are not allowed to request any new loans before fully pay the old ones. " % (
                        rec.contract_id.remaining_amount)
                    raise ValidationError(_(error_msg))

    @api.constrains('date', 'contract_id')
    def check_contract_duration(self):
        for rec in self:
            if rec.date and rec.contract_id.date_start and rec.contract_id.date_end:
                if rec.date < rec.contract_id.date_start or rec.date > rec.contract_id.date_end:
                    error_msg = "Not allowed, \n Employee contract started at ( %s ) and will expire at ( %s )  , salary in advance & loans should be within employee contract duration." % (
                        rec.contract_id.date_start, rec.contract_id.date_end)
                    raise ValidationError(_(error_msg))

    @api.constrains('loan_type')
    def check_old_payslip(self):
        if self.type == "Salary In Advance":
            months = {
                '01': 'January',
                '02': 'February',
                '03': 'March',
                '04': 'April',
                '05': 'May',
                '06': 'June',
                '07': 'July',
                '08': 'August',
                '09': 'September',
                '10': 'October',
                '11': 'November',
                '12': 'December',
            }
            month = " %s /  %s" % (months[self.month], self.year)
            domain = [
                ('month', '=', self.month),
                ('year', '=', self.year),
                ('employee_id', '=', self.employee_id.id),
                ('state', '!=', 'cancel'),
            ]
            # old_payslip = self.env['hr.payslip'].search(domain)
            # if len(old_payslip):
            #     error_msg = "Attention !! \n You are not allowed to request salary in advance for ( %s ) because we found that this employee ( %s ) already have a payslip for the same month, kindly review old payslip before requesting for salary in advance." % (
            #         month, self.employee_id.name)
            #     raise ValidationError(_(error_msg))
            if self.installment_ids:
                for line in self.installment_ids:
                    if line.paid != 0:
                        message = "Attention !! \n Not allowed to change your request type from Loans request to Salary in advance request, our records indicates that there are some installments for this loan request which already paid. So it is not logic to change type to salary in advance."
                        raise ValidationError(message)

                for line in self.installment_ids:
                    line.unlink()



    #@api.one
    @api.onchange('loan_type', 'employee_id')
    def get_month_year(self):
        for rec in self:
            if rec.loan_type.type == "Loan" and rec.is_installment:
                if not (rec.installment_start_month and rec.installment_start_year) and rec.employee_id:
                    domain = [
                        ('employee_id', '=', rec.employee_id.id),
                        ('state', '=', 'done'),
                    ]
                    # last_payslip = rec.env['hr.payslip'].search(domain, order="year desc,month desc", limit=1)
                    # if last_payslip:
                    #     next_month_year = rec.get_next_month_year(last_payslip.month, last_payslip.year)
                    #     rec.installment_start_month = next_month_year['month']
                    #     rec.installment_start_year = next_month_year['year']
                    if rec.expected_payment:
                        fmt = '%Y-%m-%d'
                        expected_payment = rec.expected_payment
                        rec.installment_start_month = expected_payment.strftime('%m')
                        rec.installment_start_year = expected_payment.strftime('%Y')

    #@api.one
    def get_next_month_year(self, month, year):
        if month == '12':
            return {'month': '01', 'year': year + 1}
        elif month in ['09', '10', '11']:
            return {'month': str(int(month) + 1), 'year': year}
        else:
            return {'month': '0' + str(int(month) + 1), 'year': year}

    #@api.one
    def gm_installment_validation(self):
        for rec in self:
            if not rec.expected_payment:
                message = "Attention !! \n You forget to select the date which the employee will receive the approved amount"
                raise ValidationError(message)
            if rec.expected_payment < rec.date:
                message = _(
                    "Data Error !! \n It is Not logic that the employee receive loan amount at ( %s ) which is before his request date ( %s )") % (
                            rec.expected_payment, rec.date)
                raise ValidationError(message)
            if rec.installment_ids:
                total_installment = 0
                for line in rec.installment_ids:
                    total_installment += line.monthly_installment
                    # if line.deduction_date < rec.expected_payment:
                    #     message = _(
                    #         "Data Error !! \n Expected payment to employee date is ( %s ) It is not logic to start deduction in ( %s / %s )") % (
                    #                 rec.expected_payment, line.month, line.year)
                    #     raise ValidationError(message)
                    # --------------------  Check Confirmed  Payslip -------------------------------
                    # domain = [
                    #     ('employee_id', '=', rec.employee_id.id),
                    #     ('month', '=', line.month),
                    #     ('year', '=', line.year),
                    #     ('state', '=', 'done'),
                    # ]
                    # old_payslips = rec.env['hr.payslip'].search(domain)
                    # if old_payslips:
                    #     old_payslip = rec.env['hr.payslip'].search(domain)[0]
                    #     message = _(
                    #         "Not Allowed !! \n Your installment schedule for this loan request is incorrect, at this month ( %s / %s ) we found that there is a confirmed payslip for the same employee.  ( %s )") % (
                    #                 line.month, line.year, old_payslip.number)
                    #     raise ValidationError(message)
                    if line.deduction_date < rec.contract_id.adjusted_date:
                        message = _(
                            "Data Error !! \n Employee start working at ( %s )  it is not allowed to create some installments before employee hiring date") % (
                                    rec.contract_id.adjusted_date)
                        raise ValidationError(message)
                    if line.deduction_date > rec.contract_id.date_end:
                        message = _(
                            "Data Error !! \n Employee contract end date is ( %s ) it is not allowed to create some installments after contract end date.") % (
                                    rec.contract_id.date_end)
                        raise ValidationError(message)
                if total_installment != rec.general_manager_approval:
                    message = _(
                        "Attention !! \n GM / CEO Approved that this employee will receive ( %s )  we found that total Installment amount not matching the amount approved by CEO. Kindly review your data.") % (
                                rec.general_manager_approval)
                    raise ValidationError(message)

    #@api.one
    def generate_installment(self):
        for rec in self:
            if rec.installment_number <= 0:
                message = "Not allowed!! \n cannot Auto generate installments because number of installments which you insert is incorrect."
                raise ValidationError(message)
            if not (rec.installment_start_month and rec.installment_start_year):
                rec.get_month_year()
            if not (rec.installment_start_month and rec.installment_start_year):
                message = "Attention !! \n Your system can not find the starting month to create installment, kindly select the (Start Deduction From - Month and year)."
                raise ValidationError(message)
            # ////////////////// Delete Old Lines if no paid lines ////////////////////////////////
            if rec.installment_ids:
                for line in rec.installment_ids:
                    if line.paid != 0:
                        message = "Not allowed!! \n Our Historical data indicates that you already deducted some installments from employee salary, Auto generate installments is not allowed in this case, you can do it manually by trying to edit / remove / add new installment lines."
                        raise ValidationError(message)

                for line in rec.installment_ids:
                    line.unlink()
            # //////////////// Generate Lines ////////////////////////////////////////////////////
            month = rec.installment_start_month
            year = rec.installment_start_year
            lines = []
            loan_amount = rec.loan_amount
            if rec.general_manager_approval != 0:
                loan_amount = rec.general_manager_approval
            elif rec.financial_manager_approval != 0:
                loan_amount = rec.financial_manager_approval
            elif rec.hr_manager_approval != 0:
                loan_amount = rec.hr_manager_approval
            division_remaining = loan_amount % rec.installment_number
            monthly_installment = (loan_amount - division_remaining) / rec.installment_number
            last_month_installment = monthly_installment + division_remaining
            for x in range(0, rec.installment_number):
                start_end = calendar.monthrange(year, int(month))
                deduction_date = str(year) + '-' + month + '-' + str(start_end[1])
                if x == rec.installment_number - 1:
                    res = {
                        'employee_id': rec.employee_id.id,
                        'loan_request_id': rec.id,
                        'month': month,
                        'year': year,
                        'deduction_date': deduction_date,
                        'monthly_installment': last_month_installment,
                        'state':'New',
                    }
                else:
                    res = {
                        'employee_id': rec.employee_id.id,
                        'loan_request_id': rec.id,
                        'month': month,
                        'year': year,
                        'deduction_date': deduction_date,
                        'monthly_installment': monthly_installment,
                        'state':'New',
                    }
                lines.append(res)
                # //////  Get next Month , Year /////////////////////////
                next_month_year = rec.get_next_month_year(month, year)
                month = next_month_year['month']
                year = next_month_year['year']

            for installment in lines:
                rec.env['loan.installment'].create(installment)


class LoanRequestAttaches(models.Model):
    _name = "loan.advance.request.attaches"
    _description = "Loan Request Attaches"

    request_id = fields.Many2one('loan.advance.request', 'Request')
    file = fields.Binary('File')
    name = fields.Char('Description')
    note = fields.Char('Notes')


class hr_employee(models.Model):
    _inherit = "hr.employee"

    request_loan = fields.Boolean(_('Can request a loan / advance'), default=True)
    loans_count = fields.Float('Loans count', compute='get_loans_count')

    #@api.one
    def get_loans_count(self):
        for rec in self:
            contracts = rec.env['hr.contract'].search([('employee_id', '=', rec.id), ('active', '=', True)])
            if len(contracts):
                contract = contracts[0]
                rec.loans_count = contract.remaining_amount
            else:
                rec.loans_count = 0

    def action_loans(self):
        return {
            'domain': "[('employee_id','in',"+ str(self.ids)+ ")]",
            'name': _('Employee Loans'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'loan.advance.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


class hr_contract(models.Model):
    _inherit = "hr.contract"

    loans = fields.One2many('loan.advance.request', 'contract_id', readonly=True, string=_('Loan Details'),
                            domain=[('type', '=', 'Loan'), ('state', 'in', ['GM Approve', 'Loan Fully Paid'])])
    total_loans = fields.Float(string=_('Total Loans'), compute="_compute_total_loans", readonly=True)
    total_loans_copy = fields.Float(string=_('Total Loans'), related="total_loans", readonly=True)
    paid_amounts = fields.One2many('hr.contract.loan.payment', 'contract_id', readonly=True, string=_('Paid Amounts'))
    loans_total_paid_amount = fields.Float(string=_('Total Paid Amount'), compute="_compute_loans_total_paid_amount",
                                           readonly=True)
    total_paid_amount_copy = fields.Float(string=_('Total Paid Amount'), related="loans_total_paid_amount",
                                          readonly=True)
    remaining_amount = fields.Float(string=_('Remaining Amount'), compute="_compute_remaining_amount", readonly=True)

    @api.depends('loans')
    def _compute_total_loans(self):
        for rec in self:
            rec.total_loans = 0
            approved_loans = self.env['loan.advance.request'].search(
                [('contract_id', '=', rec.id), ('type', '=', 'Loan'),
                 ('state', 'in', ['GM Approve', 'Loan Fully Paid'])])
            total_loan = 0
            for loan in approved_loans:
                total_loan += loan.general_manager_approval
            rec.total_loans = total_loan

    @api.depends('paid_amounts')
    def _compute_loans_total_paid_amount(self):
        for rec in self:
            total_amount = 0
            for amount in rec.paid_amounts:
                total_amount += amount.paid_amount
            rec.loans_total_paid_amount = total_amount

    @api.depends('total_loans', 'loans_total_paid_amount')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = round(rec.total_loans, 2) - round(rec.loans_total_paid_amount, 2)


class hr_contract_loan_payment(models.Model):
    _name = 'hr.contract.loan.payment'

    contract_id = fields.Many2one('hr.contract', string=_('Contract'), readonly=True)
    ref = fields.Many2one('hr.payslip', string=_('Payment Reference'), readonly=True)
    payment_date = fields.Date(string=_('Payment Date'), readonly=True)
    paid_amount = fields.Float(string=_('Paid Amount'), readonly=True)
    notes = fields.Text(string=_('Notes'))


class hr_payslip_run(models.Model):
    _inherit = 'hr.payslip.run'

    reviewed_payslip_ids = fields.One2many('hr.payslip', 'patch_reviewed_id', 'Payslips To review')
    payslip_reviewed = fields.Boolean('Payslip reviewed')

    #@api.one
    def _compute_reviewed_payslips(self):
        for payslip in self.slip_ids:
            if payslip.current_remaining_amount > 0 or payslip.remaining > 0 or payslip.remaining_rewards > 0 or payslip.total_absence:
                payslip.patch_reviewed_id = self.id

    #@api.one
    def confirm_payslip_run(self):
        for rec in self:
            if rec.slip_ids:
                for slip in rec.slip_ids:
                    if slip.state == 'draft':
                        slip.signal_workflow('review_payslip')
                        slip.signal_workflow('final_review_payslip')
                        slip.signal_workflow('hr_verify_sheet')
                    if slip.state == 'Reviewed':
                        slip.signal_workflow('final_review_payslip')
                        slip.signal_workflow('hr_verify_sheet')
                    if slip.state == 'Final Reviewed':
                        slip.signal_workflow('hr_verify_sheet')
            else:
                raise UserError(_(
                    "Not allowed !! \n There is no payslips found! What is the data which you confirmed? kindly go to Payslip tab and click on Generate payslips, then select all employees which you want to create Payslip for them. "))

            if rec.reviewed_payslip_ids and not rec.payslip_reviewed:
                raise UserError(_(
                    "Dear Payroll team !! \n We found that there is some payslips which requires a special review, these payslips contains Loans or Violations or Rewards or Absence deduction which requires a special review, kindly make sure to review all payslip and check the ( Payslip reviewed ) field. "))

            rec.write(
                {'state': 'done', 'confirmed_by': rec.env.uid, 'confirmation_date': datetime.now().strftime('%Y-%m-%d')})
            body = "Document Confirmed"
            rec.message_post(body=body, message_type='email')
            return {}

class hr_payslip_employees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self, cr, uid, ids, context=None):
        emp_pool = self.pool.get('hr.employee')
        slip_pool = self.pool.get('hr.payslip')
        run_pool = self.pool.get('hr.payslip.run')
        slip_ids = []
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        run_data = {}
        if context and context.get('active_id', False):
            run_data = \
                run_pool.read(cr, uid, [context['active_id']],
                              ['date_start', 'date_end', 'credit_note', 'month', 'year'])[
                    0]
        from_date = run_data.get('date_start', False)
        to_date = run_data.get('date_end', False)
        credit_note = run_data.get('credit_note', False)
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for emp in emp_pool.browse(cr, uid, data['employee_ids'], context=context):
            slip_data = slip_pool.onchange_employee_id(cr, uid, [], from_date, to_date, emp.id, contract_id=False,
                                                       context=context)
            res = {
                'employee_id': emp.id,
                'name': slip_data['value'].get('name', False),
                'month': run_data.get('month', False),
                'year': run_data.get('year', False),
                'struct_id': slip_data['value'].get('struct_id', False),
                'contract_id': slip_data['value'].get('contract_id', False),
                'payslip_run_id': context.get('active_id', False),
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', False)],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', False)],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': credit_note,
            }
            slip_ids.append(slip_pool.create(cr, uid, res, context=context))
        slip_pool.compute_sheet(cr, uid, slip_ids, context=context)
        batch = context and context.get('active_id', False) and run_pool.browse(cr, uid,
                                                                                context.get('active_id', False),
                                                                                context=context) or None
        if batch:
            batch._compute_reviewed_payslips()
        return {'type': 'ir.actions.act_window_close'}


class hr_payslip(models.Model):
    _inherit = "hr.payslip"

    current_total_loans = fields.Float(string=_('Total Loans'), related="contract_id.total_loans", readonly=True)
    current_total_paid_amount = fields.Float(string=_('Total paid'), related="contract_id.loans_total_paid_amount",
                                             readonly=True)
    current_remaining_amount = fields.Float(string=_('Remaining Amount'), related="contract_id.remaining_amount",
                                            readonly=True)
    remaining_loans = fields.Float('Remaining Loans', compute="_compute_remaining_loans")
    loan_next_month_balance = fields.Float(string=_('Next Month Balance'), compute="_compute_loan_next_month_balance")
    loan_next_month_balance_history = fields.Float(string=_('Next Month Balance'))
    salary_advance_id = fields.Many2one('loan.advance.request', 'Salary in advance request')
    absence_ids = fields.One2many('employee.absence.line', 'payslip_m2o_id', _('Absence deduction report'))
    total_absence = fields.Float('Total absence deduction', compute='_compute_total_absence')
    absence_eduction_remove = fields.Float('Remove this amount from absence deduction')
    net_absence_deduction = fields.Float('Net absence deduction', compute='_compute_total_absence')
    patch_reviewed_id = fields.Many2one('hr.payslip.run', 'Patch Reviewed payslip')
    no_update_pay = fields.Boolean('Don\'t update pay this month')

    #@api.one
    def _compute_remaining_loans(self):
        for rec in self:
            rec.remaining_loans = 0
            if rec.state == 'done':
                rec.remaining_loans = rec.remaining_amount
            else:
                rec.remaining_loans = rec.current_remaining_amount

    # /////////////////// Smart Buttons /////////////////////////////////////////////////////////////
    count_absence = fields.Float('Number of Absence Report', compute='get_count_smart_buttons')

    #@api.one
    def get_count_smart_buttons(self):
        self.count_absence = self.env['employee.absence.line'].search_count(
            [('employee_id', '=', self.employee_id.id), ('year', '=', self.year), ('month', '=', self.month)])

    #@api.multi
    def open_payslip(self):
        return {
            'name': _('Payslip'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {},
            'flags': {'form': {'options': {'mode': 'view'}}}
        }

    #@api.multi
    def open_absence_report(self):
        return {
            'domain': [('employee_id', '=', self.employee_id.id), ('year', '=', self.year), ('month', '=', self.month),
                       ('payslip_id', 'in', [self.id])],
            'name': _('Absence Report'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'employee.absence.line',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    # ///////////////////////////////////////////////////////////////////////////////////////////////////


    #@api.one
    @api.onchange('employee_english_name', 'month', 'year')
    def _compute_absence(self):
        if self.employee_id and self.month and self.year:
            absences = self.env['employee.absence.line'].search(
                [('employee_id', '=', self.employee_id.id), ('paid', '=', False), ('year', '=', self.year),
                 ('month', '=', self.month), ('payslip_id', 'in', [self.id, False])])
            self.absence_ids = absences

    #@api.one
    @api.depends('absence_ids')
    def _compute_total_absence(self):
        total_absence = 0
        for absence in self.absence_ids:
            total_absence += absence.deduction_amount
        self.total_absence = total_absence
        self.net_absence_deduction = self.total_absence - self.absence_eduction_remove

    @api.constrains('absence_eduction_remove')
    def _check_absence_eduction_remove(self):
        for rec in self:
            if rec.absence_eduction_remove < 0:
                raise exceptions.ValidationError(_("Remove this amount from absence deduction Field Can not be minus"))
            if rec.absence_eduction_remove > 0 and rec.absence_eduction_remove > rec.total_absence:
                raise exceptions.ValidationError(_(
                    "Not Allowed !! \n For Employee ( %s ), It is not logic that the amount which you will remove from absence deduction is greater that total absence deduction! Kindly review your data!.") % rec.employee_id.name)

    #@api.multi
    def unlink(self):
        for rec in self:
            if rec.salary_advance_id:
                raise exceptions.ValidationError(_(
                    "Dear Payroll specialist, \n You are not allowed to delete this payslip because it is automatically created through Salary in advance request, you can refuse this payslip instead of deleting it."))
        return super(hr_payslip, self).unlink()

    @api.model
    def create(self, vals):
        res = super(hr_payslip, self).create(vals)
        res._compute_absence()
        return res

    @api.depends('current_remaining_amount', 'deduct_this_month')
    def _compute_loan_next_month_balance(self):
        for rec in self:
            rec.loan_next_month_balance = rec.current_remaining_amount - rec.deduct_this_month

    def action_payslip_done(self):

        for rec in self:
            rec.hr_verify_sheet()
        res = super(hr_payslip,self).action_payslip_done()
        return res
    #@api.multi
    def refund_sheet(self):
        """
        override to cancel loan paid
        """
        res = super(hr_payslip,self).refund_sheet()
        for rec in self:

            domain = [
                ('employee_id', '=', rec.employee_id.id),
                # ('state', '=', 'Loan Fully Paid'),
                ('state', '=', 'installment_return'),
                ('deduction_date','<=',rec.date_to),
                # ('remaining', '!=', 0),
            ]
            confirmed_installments = self.env['loan.installment'].search(domain, order="deduction_date asc")


            if confirmed_installments:
                # print(".>>>>>>>>>>>>>>>>>>>confirmed_installments ",confirmed_installments)
                installment_deduction = rec.deduct_this_month
                for confirmed_installment in confirmed_installments:
                    confirmed_installment.payment_ids.unlink()

                    confirmed_installment.state = 'Loan Fully Paid'
                    confirmed_installment._compute_paid()




                    if confirmed_installment.loan_request_id.state == 'installment_return':
                        confirmed_installment.loan_request_id.state = 'Loan Fully Paid'
            #advance salary
            advance_installments = self.env['loan.advance.request'].search([
                        ('employee_id','=',rec.employee_id.id),
                        ('expected_payment','>=',rec.date_from),
                        ('expected_payment','<=',rec.date_to),
                        ('state','=','installment_return'),
                        ('type','=','Salary In Advance')])
            if advance_installments:
                for advance_installment in advance_installments:
                    if advance_installment.state == 'installment_return':
                        # advance_installment.paid_amount = 0
                        advance_installment.state = 'Loan Fully Paid'
        return res

    def action_payslip_cancel(self):
        """
        override to cancel loan paid
        """
        res = super(hr_payslip,self).action_payslip_cancel()
        for rec in self:

            domain = [
                ('employee_id', '=', rec.employee_id.id),
                # ('state', '=', 'Loan Fully Paid'),
                ('state', '=', 'installment_return'),
                ('deduction_date','<=',rec.date_to),
                # ('remaining', '!=', 0),
            ]
            confirmed_installments = self.env['loan.installment'].search(domain, order="deduction_date asc")


            if confirmed_installments:
                # print(".>>>>>>>>>>>>>>>>>>>confirmed_installments ",confirmed_installments)
                installment_deduction = rec.deduct_this_month
                for confirmed_installment in confirmed_installments:
                    confirmed_installment.payment_ids.unlink()

                    confirmed_installment.state = 'Loan Fully Paid'
                    confirmed_installment._compute_paid()




                    if confirmed_installment.loan_request_id.state == 'installment_return':
                        confirmed_installment.loan_request_id.state = 'Loan Fully Paid'
            #advance salary
            advance_installments = self.env['loan.advance.request'].search([
                        ('employee_id','=',rec.employee_id.id),
                        ('expected_payment','>=',rec.date_from),
                        ('expected_payment','<=',rec.date_to),
                        ('state','=','installment_return'),
                        ('type','=','Salary In Advance')])
            if advance_installments:
                for advance_installment in advance_installments:
                    if advance_installment.state == 'installment_return':
                        # advance_installment.paid_amount = 0
                        advance_installment.state = 'Loan Fully Paid'

            loan_pays = rec.env['hr.contract.loan.payment'].search([('ref.employee_id','=',rec.employee_id.id),('payment_date','>=',rec.date_from),('payment_date','<=',rec.date_to)])
            loan_pays.unlink()

            rec.total_loans = 0
            rec.total_paid_amount = 0
            rec.remaining_amount = 0
            rec.loan_next_month_balance_history = 0


        return res

    #@api.multi
    def hr_verify_sheet(self):
        for rec in self:
            rec.loans_data_reviewed = True
            if rec.current_remaining_amount > 0:
                if not rec.loans_data_reviewed:
                    message = _(
                        "Attention!! \n This employee ( %s  ) had old loans or deductions or rewards which is not fully paid before confirm this payslip."
                        " kindly go to ( other payment / deduction) tab,  and make sure that you checked (other payments / deduction reviewed).") % self.employee_id.name
                    raise exceptions.ValidationError(message)
                if rec.deduct_this_month > rec.current_remaining_amount:
                    raise exceptions.ValidationError(
                        _(
                            "Deduction error!! We found that you are trying to deduct loan amount greater that the remaining loan amount."))
                if rec.deduct_this_month > 0:
                    months = {
                        '01': 'January',
                        '02': 'February',
                        '03': 'March',
                        '04': 'April',
                        '05': 'May',
                        '06': 'June',
                        '07': 'July',
                        '08': 'August',
                        '09': 'September',
                        '10': 'October',
                        '11': 'November',
                        '12': 'December',
                    }
                    total_loans = rec.current_total_loans
                    total_paid_amount = rec.current_total_paid_amount
                    remaining_amount = rec.current_remaining_amount
                    loan_next_month_balance = rec.loan_next_month_balance
                    notes = _("خصم جزء من القرض عن شهر   %s") % (_(months[rec.month]))
                    payment_vals = {
                        'contract_id': rec.contract_id.id,
                        'ref': rec.id,
                        'payment_date': rec.date_from,
                        'paid_amount': rec.deduct_this_month,
                        'notes': notes,
                    }
                    payment_id = self.env['hr.contract.loan.payment'].create(payment_vals)
                    rec.total_loans = total_loans
                    rec.total_paid_amount = total_paid_amount
                    rec.remaining_amount = remaining_amount
                    rec.loan_next_month_balance_history = loan_next_month_balance
                    # /////////// Installment ////////////////////////
                    domain = [
                        ('employee_id', '=', rec.employee_id.id),
                        ('state', '=', 'Loan Fully Paid'),
                        ('deduction_date','<=',rec.date_to),
                        ('remaining', '!=', 0),
                    ]
                    confirmed_installments = self.env['loan.installment'].search(domain, order="deduction_date asc")


                    if confirmed_installments:
                        installment_deduction = rec.deduct_this_month
                        for confirmed_installment in confirmed_installments:
                            deducted = 0
                            if installment_deduction <= 0:
                                break
                            if confirmed_installment.remaining > 0:
                                # if installment_deduction < confirmed_installment.remaining:
                                #     deducted = installment_deduction
                                # else:
                                deducted = confirmed_installment.remaining
                                # Create payment to installment with deduction
                                payment_vals = {
                                    'installment_id': confirmed_installment.id,
                                    'payslip_id': rec.id,
                                    # 'paid': deducted,
                                    'paid': deducted,
                                }
                                payment_id = self.env['loan.installment.payment'].create(payment_vals)
                                installment_deduction -= deducted
                                confirmed_installment.state = 'installment_return'
                                confirmed_installment._compute_paid()
                                all_true = True
                                for installment_id in confirmed_installment.loan_request_id.installment_ids:
                                    if installment_id.state != 'installment_return':
                                        all_true = False
                                if all_true:
                                    confirmed_installment.loan_request_id.state = 'installment_return'

                    advance_installments = self.env['loan.advance.request'].search([
                        ('expected_payment','>=',rec.date_from),
                        ('expected_payment','<=',rec.date_to),
                        ('state','=','Loan Fully Paid'),
                        ('type','=','Salary In Advance')])
                    if advance_installments:
                        for advance_installment in advance_installments:
                            # advance_installment.paid_amount = advance_installment.loan_amount
                            advance_installment.state = 'installment_return'


            # ////////////////// Absence Report ///////////////////////////////////////
            # for absence in rec.absence_ids:
            #     absence.paid = True
            #     if not absence.payslip_id:
            #         absence.payslip_id = rec.id
            #         absence.absence_id.check_status()
            #     if not absence.patch_id and rec.payslip_run_id:
            #         absence.patch_id = rec.payslip_run_id.id

                    # ////////////////////////////////////////////////////////////////////////
        # self.compute_sheet()
        # self.write(
        #     {'state': 'verify', 'confirmed_by': self.env.uid, 'confirmation_date': datetime.now().strftime('%Y-%m-%d')})
        body = "Document Confirmed"
        self.message_post(body=body, message_type='email')
        return {}

    #@api.multi
    def compute_sheet(self):
        # for rec in self:
        #     rec._compute_absence()

        for rec in self:
            if not rec.no_update_pay and rec.current_remaining_amount > 0 and rec.deduct_this_month == 0:
                based_on = rec.env['ir.config_parameter'].sudo().get_param('hr_loans.default_previous_based_on', 'False')

                based_on_salary = 0
                if based_on == 'Total salary':
                    for line in rec.line_ids:
                        if line.salary_rule_id.id == rec.env.ref('ext_hr_payroll.hr_rule_gross').id:
                            based_on_salary = line.total

                if based_on == 'Basic Salary':
                    for line in rec.line_ids:
                        if line.salary_rule_id.id == rec.env.ref('ext_hr_payroll.basic_salary_rule').id:
                            based_on_salary = line.total


                loan_deduct_percentage = rec.env['ir.config_parameter'].sudo().get_param('hr_loans.default_loans_deduction_percentage', 'False')

                if loan_deduct_percentage:
                    loan_deduct_percentage = float(loan_deduct_percentage)/100
                else:
                    loan_deduct_percentage = 0


                deduction = based_on_salary * loan_deduct_percentage
                if deduction < rec.current_remaining_amount:
                    rec.deduct_this_month = deduction
                else:
                    rec.deduct_this_month = rec.current_remaining_amount
                # ////////////////////////// Installments ////////////////////////////////////////////////////
                domain = [
                    ('employee_id', '=', rec.employee_id.id),
                    ('deduction_date', '<=', rec.date_to),
                    ('state', '=', 'Loan Fully Paid'),
                ]
                confirmed_installments = rec.env['loan.installment'].search(domain)
                if confirmed_installments:
                    total = 0
                    for confirmed_installment in confirmed_installments:
                        total += confirmed_installment.monthly_installment
                    if total:
                        rec.deduct_this_month = total
            if rec.remaining > 0 and rec.deduct_this_month_ == 0:
                based_on = rec.env['ir.config_parameter'].sudo().get_param('hr_loans.default_previous_based_on', 'False')

                based_on_salary = 0
                if based_on == 'Total salary':
                    for line in rec.line_ids:
                        if line.salary_rule_id.id == rec.env.ref('ext_hr_payroll.hr_rule_gross').id:
                            based_on_salary = line.total

                if based_on == 'Basic Salary':
                    for line in rec.line_ids:
                        if line.salary_rule_id.id == rec.env.ref('ext_hr_payroll.basic_salary_rule').id:
                            based_on_salary = line.total


                else:
                    rec.deduct_this_month_ = rec.remaining
            # /////////////// Compute rewards ///////////////////////////////
            if not rec.reward_pay_this_month:
                rec.reward_pay_this_month = rec.remaining_rewards

            # ///////////////////////// Automatic Data Reviewed ///////////////////////////
            if not ((rec.current_remaining_amount > 0 and rec.deduct_this_month == 0) or (
                                rec.remaining > 0 and rec.deduct_this_month_ == 0 and rec.remove_from_employee == 0) or (
                                rec.remaining_rewards > 0 and rec.reward_pay_this_month == 0 and rec.reward_remove_amount == 0)):
                rec.loans_data_reviewed = True
        res = super(hr_payslip, self).compute_sheet()
        return res


class employee_absence(models.Model):
    _name = 'employee.absence'
    _inherit = 'mail.thread'
    _description = "Employee Absence"

    name = fields.Char('Description')

    _PERIOD = [
        ('01', 'January'),
        ('02', 'February'),
        ('03', 'March'),
        ('04', 'April'),
        ('05', 'May'),
        ('06', 'June'),
        ('07', 'July'),
        ('08', 'August'),
        ('09', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ]

    month = fields.Selection(_PERIOD, _('Month'), default=lambda s: time.strftime("%m"))
    year = fields.Integer(_('Year'), default=lambda s: float(time.strftime('%Y')))
    note = fields.Html('Notes')
    lines = fields.One2many('employee.absence.line', 'absence_id', 'Lines')
    attachment_ids = fields.One2many('absence.attaches', 'absence_id', 'Attachments')
    count_lines = fields.Integer('Number Of Employees', compute='_compute_count_lines')
    state = fields.Selection([
        ('New', 'New'),
        ('done', 'Deduction Done In Payslip'),
    ], string='Status', readonly=True, select=True, default='New', )

    #@api.one
    def check_status(self):
        fully_computed = 1
        for line in self.lines:
            if not line.payslip_id:
                fully_computed = 0
        if fully_computed:
            self.state = 'done'

    @api.depends('lines')
    def _compute_count_lines(self):
        for rec in self:
            rec.count_lines = len(rec.lines)

    @api.constrains('lines', 'count_lines')
    def _check_lines(self):
        for rec in self:
            if not rec.count_lines:
                raise exceptions.ValidationError(_(
                    "Dear HR ,\n Not allowed to create empty Absence details, Kindly add some absence lines for employees."))
            for line in rec.lines:
                # if not line.payslip_id:
                #     domain = [
                #         ('month', '=', line.month),
                #         ('year', '=', line.year),
                #         ('employee_id', '=', line.employee_id.id),
                #         ('state', '=', 'done'),
                #     ]
                #     old_payslips = self.env['hr.payslip'].search(domain)
                #     if old_payslips:
                #         raise exceptions.ValidationError(_(
                #             "Data Error!!\n For Employee ( %s ),we found that he already have a confirmed payslip on the same month, so you must select another month for deduction.") % (
                #                                              line.employee_id.name))
                    month_first_day = date(line.year, int(line.month), 1)
                    contracts = self.env['hr.contract'].search(
                        [('employee_id', '=', line.employee_id.id), ('active', '=', True)])
                    if len(contracts):
                        contract = contracts[0]
                        if month_first_day.strftime("%Y-%m-%d") > contract.date_end or month_first_day.strftime(
                                "%Y-%m-%d") < contract.date_start:
                            raise exceptions.ValidationError(_(
                                "Data Error!!\n For Employee ( %s ),his contract start date is ( %s )his contract end date is ( %s ), It is not logic to make absence deduction on ( %s / %s), deduction month / year is out of contract time scope.") % (
                                                                 line.employee_id.name, contract.date_start,
                                                                 contract.date_end, line.month, line.year))

    #@api.multi
    def write(self, vals):
        # Write your logic here
        res = super(employee_absence, self).write(vals)
        for rec in self:
            for line in rec.lines:
                if not line.payslip_id and ('month' in vals.keys() or 'year' in vals.keys()):
                    line.month = rec.month
                    line.year = rec.year
        # Write your logic here
        return res

    #@api.multi
    def unlink(self):
        for rec in self:
            for line in rec.lines:
                if line.payslip_id:
                    raise exceptions.ValidationError(_(
                        "Not Allowed \n We found that there is some confirmed payslip which already linked with this absence timesheet, kindly open this absence timesheet and try to delete the lines which contains data error!"))
        return super(employee_absence, self).unlink()

    #@api.multi
    def copy(self):
        for rec in self:
            raise ValidationError(_('Forbidden to duplicate'))


class employee_absence_line(models.Model):
    _name = 'employee.absence.line'
    _inherit = 'mail.thread'

    payslip_m2o_id = fields.Many2one('hr.payslip', "Payslip")
    absence_id = fields.Many2one('employee.absence', "Absence Sheet")
    employee_id = fields.Many2one('hr.employee', "Employee")
    employee_english_name = fields.Char('Employee English Name', related='employee_id.employee_english_name')
    absence_days = fields.Float('Absence days')
    absence_hours = fields.Float('Absence Hours')
    absence_minutes = fields.Float('Absence Minutes')
    deduction_amount = fields.Float('Absence Deduction Amount', compute='_compute_deduction_amount')
    absence_date = fields.Date('Absence date')
    _PERIOD = [
        ('01', 'January'),
        ('02', 'February'),
        ('03', 'March'),
        ('04', 'April'),
        ('05', 'May'),
        ('06', 'June'),
        ('07', 'July'),
        ('08', 'August'),
        ('09', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ]
    month = fields.Selection(_PERIOD, _('Will be deducted on'),
                             default=lambda self: self.env.context.get('month', False))
    year = fields.Integer('Year', default=lambda self: self.env.context.get('year', False))
    patch_id = fields.Many2one('hr.payslip.run', 'Payslip batch')
    payslip_id = fields.Many2one('hr.payslip', 'Employee Payslip')
    note = fields.Char('Absence notes')
    department_id = fields.Many2one('hr.department', 'Department', related='employee_id.department_id', store=True)
    job_id = fields.Many2one('hr.job', 'Job', related='employee_id.job_id', store=True)
    country_id = fields.Many2one('res.country', 'Nationality', related='employee_id.country_id', store=True)
    nationality_type = fields.Selection([('Saudi', 'Saudi'),
                                         ('Non-Saudi', 'Non-Saudi')], related='employee_id.nationality_type',
                                        store=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender', related='employee_id.gender',
                              store=True)
    marital = fields.Selection([('single', 'Single'), ('married', 'Married')], 'Marital Status',
                               related='employee_id.marital', store=True)
    # branch_id = fields.Many2one('hr.branch', 'branch', related='employee_id.branch_id', store=True)
    paid = fields.Boolean('Paid')

    @api.constrains('absence_date')
    def _check_absence_date(self):
        for r in self:
            if r.absence_date > datetime.now().strftime("%Y-%m-%d"):
                raise exceptions.ValidationError(_(
                    "Not Allowed !!\n For Employee ( %s ),it is not logic that  Absence date is greater than today date.") % (
                                                     r.employee_id.name))

    @api.constrains('absence_days', 'absence_hours', 'absence_minutes')
    def _check_absence_days(self):
        for r in self:
            if r.absence_days < 0:
                raise exceptions.ValidationError(_("Attention !! Absence days cannot be minus"))
            if r.absence_hours < 0:
                raise exceptions.ValidationError(_("Attention !!  Absence Hours cannot be minus"))
            if r.absence_minutes < 0:
                raise exceptions.ValidationError(_("Attention !!  Absence Minutes cannot be minus"))
            if r.absence_days == 0 and r.absence_hours == 0 and r.absence_minutes == 0:
                raise exceptions.ValidationError(_(
                    "Not Allowed !!\n For Employee ( %s ) it is not logic that number of absence days & Hours & Minutes is zero. if there is no absence related to this employee, kindly remove him from absence report.") % (
                                                     r.employee_id.name))

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
            rec.absence_days = 0
            rec.absence_hours = 0
            rec.absence_minutes = 0

    #@api.one
    @api.depends('employee_id', 'absence_days', 'absence_hours', 'absence_minutes')
    def _compute_deduction_amount(self):
        absence_based_on = self.env['ir.config_parameter'].sudo().get_param('hr_loans.default_absence_based_on', 'False')

        contracts = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('active', '=', True)])
        if len(contracts):
            contract = contracts[0]
            based_on = 0
            if absence_based_on == 'basic':
                based_on = contract.basic_salary
            if absence_based_on == 'basic_house':
                based_on = contract.basic_salary + contract.house_allowance_amount
            if absence_based_on == 'basic_house_trans':
                based_on = contract.basic_salary + contract.house_allowance_amount + contract.transportation_allowance_amount
            if absence_based_on == 'basic_house_trans_phone':
                based_on = contract.basic_salary + contract.house_allowance_amount + contract.transportation_allowance_amount + \
                           contract.phone_allowance_amount
            if absence_based_on == 'total':
                based_on = contract.total

            self.deduction_amount = (based_on / 30) * self.absence_days + (based_on / (30 * 8)) * self.absence_hours + (
                                                                                                                           based_on / (
                                                                                                                               30 * 8 * 60)) * self.absence_minutes

    #@api.multi
    def unlink(self):
        for rec in self:
            if rec.payslip_id:
                raise exceptions.ValidationError(_(
                    "Not allowed !! \n We found that there is some confirmed payslip which already linked with this absence timesheet, kindly open this absence timesheet and try to delete the lines which contains data error!"))
        return super(employee_absence_line, self).unlink()

    #@api.multi
    @api.depends('employee_id')
    def name_get(self):
        res = []
        for rec in self:
            name = "Employee Absence Report For %s" % rec.employee_id.name
            res += [(rec.id, name)]
            return res

    #@api.multi
    def open_line(self):
        return {
            'name': _('Absence Report'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {},
            'flags': {'form': {'options': {'mode': 'view'}}}
        }


class absenceAttaches(models.Model):
    _name = "absence.attaches"
    _description = "Absence Attaches"

    absence_id = fields.Many2one('employee.absence', "Absence Sheet")
    file = fields.Binary('File')
    name = fields.Char('Description')
    note = fields.Char('Notes')


class LoanInstallment(models.Model):
    _name = "loan.installment"
    _inherit = 'mail.thread'
    _description = "Loan Installment"
    # _rec_name = "loan_request_id"

    name = fields.Char(default='New')
    employee_id = fields.Many2one('hr.employee', string=_('Employee'))
    loan_request_id = fields.Many2one('loan.advance.request', string=_('Loan Request'), domain=[('type', '=', 'Loan')],
                                      ondelete="cascade")
    department_id = fields.Many2one('hr.department', string=_('Department'), related="employee_id.department_id",
                                    store=True)
    job_id = fields.Many2one('hr.job', string=_('Job Title'), related="employee_id.job_id", store=True)
    country_id = fields.Many2one('res.country', 'Nationality', related='employee_id.country_id', store=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender', related='employee_id.gender',
                              store=True)
    installment_number = fields.Integer('Number of installments')
    _PERIOD = [
        ('01', 'January'),
        ('02', 'February'),
        ('03', 'March'),
        ('04', 'April'),
        ('05', 'May'),
        ('06', 'June'),
        ('07', 'July'),
        ('08', 'August'),
        ('09', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ]

    month = fields.Selection(_PERIOD, _('Month'))
    year = fields.Integer(_('Year'))
    deduction_date = fields.Date('Deduction Day')
    monthly_installment = fields.Float('Monthly Installment')
    paid = fields.Float('Paid', compute='_compute_paid', store=True)
    remaining = fields.Float('Remaining', compute='_compute_remaining', store=True)
    note = fields.Html('Notes')
    attachment_ids = fields.One2many('loan.installment.attaches', 'installment_id', 'Attachments')
    payment_ids = fields.One2many('loan.installment.payment', 'installment_id', 'Payment details')
    state = fields.Selection([
        ('New', 'New'),
        ('HR Manager Approve', 'HR Manager Approve'),
        ('Financial Manager Approve', 'Financial Manager Approve'),
        ('GM Approve', 'GM Approve'),
        ('Loan Fully Paid', 'Loan Fully Paid'),
        ('installment_return', 'Installment Return '),
        ('Refused', 'Refused'),
    ], string='Status', readonly=True)
    is_skip = fields.Boolean()
    is_paid = fields.Boolean()


    def installment_change_state(self):
        for rec in self:
            rec.state = rec.loan_request_id.state
            
    @api.model
    def create(self,vals):
        res = super(LoanInstallment,self).create(vals)
        if not res.employee_id:
            res.employee_id = res.loan_request_id.employee_id.id
        res.name = self.env['ir.sequence'].sudo().next_by_code(self._name)
        
        return res
        

    #@api.one
    @api.depends('payment_ids')
    def _compute_paid(self):
        
        for rec in self:
            paid = 0
            for payment in rec.payment_ids:
                paid += payment.paid
            print(".>>>>>>>>>>>>>>>>>>>paid",paid)
            rec.paid = paid

    #@api.one
    @api.depends('monthly_installment', 'paid')
    def _compute_remaining(self):
        for rec in self:
            rec.remaining = rec.monthly_installment - rec.paid


    #@api.one
    @api.onchange('loan_request_id')
    def _onchange_loan_request_id(self):
        for rec in self:
            rec.employee_id = rec.loan_request_id.employee_id

    #@api.one
    @api.onchange('month', 'year')
    def _compute_deduction_date(self):
        for rec in self:
            if rec.month and rec.year:
                start_end = calendar.monthrange(rec.year, int(rec.month))
                rec.deduction_date = str(rec.year) + '-' + rec.month + '-' + str(start_end[1])

    #@api.multi
    def open_installment(self):
        return {
            'name': _('Installment Details'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {},
            # 'flags': {'form': { 'options': {'mode': 'view'}}}
        }

    #@api.one
    def unlink(self):
        for rec in self:
            if rec.paid:
                raise ValidationError(_("Not allowed!! \n\
                    Not Allowed to delete Loan Installment witch had paid amount"))
        return super(LoanInstallment, self).unlink()


class InstallmentPayment(models.Model):
    _name = "loan.installment.payment"
    _description = "Loan Installment Payment"

    installment_id = fields.Many2one('loan.installment', "Installment")
    payslip_id = fields.Many2one('hr.payslip', 'Payslip')
    paid = fields.Float('Paid Amount')


class InstallmentAttaches(models.Model):
    _name = "loan.installment.attaches"
    _description = "Loan Installment Attaches"

    installment_id = fields.Many2one('loan.installment', "Installment")
    file = fields.Binary('File')
    name = fields.Char('Description')
    note = fields.Char('Notes')


class Employee(models.Model):
    _inherit = "hr.employee"
    job_type_id = fields.Many2one('', '')

class leave_request(models.Model):
    _inherit = 'hr.leave'

    loan_advance_request_id = fields.Many2one('loan.advance.request')