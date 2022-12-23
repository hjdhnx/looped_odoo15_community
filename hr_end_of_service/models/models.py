# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class loanAdvanceRequest(models.Model):
    _inherit = 'loan.advance.request'

    loan_left_amount = fields.Float(compute="_get_loan_left_amount",string="Remaining Amount")

    # @api.depends('loan_ids','line_ids','leave_balance_money')
    def _get_loan_left_amount(self):
        for rec in self:
            rec.loan_left_amount = 0
            # if rec.loan_ids:
            # for loan in rec.loan_ids:
                # for line in loan.installment_ids:
            rec.loan_left_amount = sum([ line.monthly_installment - line.paid for line in rec.installment_ids]) 
            # rec.total_loans = sum([ line.monthly_installment - line.paid for line in loan.installment_id for loan in rec.loan_ids])
            
class hrPayslip(models.Model):
    _inherit = 'hr.payslip'

    last_payslip = fields.Boolean()

class hrEndOFServiceAllowanceDeduct(models.Model):
    _name = 'hr.end_of_service.allowance_deduct'

    rule_id = fields.Many2one('hr.salary.rule')
    category_id =fields.Many2one('hr.salary.rule.category',related="rule_id.category_id")
    account_id = fields.Many2one('account.account',string="Account Debit",related="rule_id.account_debit")
    account_code = fields.Char(string="Account Code",related="account_id.code")
    amount = fields.Float()
    end_of_service_id = fields.Many2one('hr.end_of_service')
    
class hrEndOFService(models.Model):
    _name = 'hr.end_of_service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Gratuity"


    name = fields.Char(copy=False,default='/')
    employee_id = fields.Many2one('hr.employee')
    hr_gratuity_id = fields.Many2one('hr.gratuity',string="Gratuity")
    
    hr_resignation_id = fields.Many2one('prepare.resignation',string="Resignation",related="hr_gratuity_id.hr_resignation_id")
    
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.company, help="Company")
    employee_joining_date = fields.Date(string='Joining Date', readonly=True,
                                        store=True, help="Employee joining date")
    expected_revealing_date = fields.Date(string="Last Date Working",
                                          related="hr_resignation_id.expected_revealing_date")
    contract_id = fields.Many2one('hr.contract',related="employee_id.contract_id")
    contract_start_date = fields.Date(related="employee_id.contract_id.start_work")
    
    department_id = fields.Many2one('hr.department',related='employee_id.department_id')
    job_id = fields.Many2one('hr.job',related='employee_id.job_id')

    total_salary = fields.Float(related="employee_id.contract_id.total",string="Total Salary")
    leave_balance = fields.Float()
    leave_balance_money = fields.Float()


    salary_for_eos = fields.Float()

    employee_gratuity_only_years = fields.Float(related="hr_gratuity_id.employee_gratuity_only_years",string='Gratuity  Years',
                                           readonly=True, store=True, help="Employee gratuity Only Years")
    employee_gratuity_only_months = fields.Float(related="hr_gratuity_id.employee_gratuity_only_months",string='Gratuity Months',
                                           readonly=True, store=True, help="Employee gratuity Only Months")
    employee_gratuity_only_days = fields.Float(related="hr_gratuity_id.employee_gratuity_only_days",string='Gratuity  Days',
                                           readonly=True, store=True, help="Employee gratuity Only Days")
    
    
    resignation_reason_id = fields.Many2one('hr.gratuity.reason',related="hr_resignation_id.gratuity_reason_id",string="Resignation Reason")
    
    journal_id = fields.Many2one('account.journal')
    termination_account_move = fields.Many2one('account.move')
    reason_text = fields.Char('Reason')
    comment_box = fields.Char()
    loan_ids = fields.Many2many('loan.advance.request')

    

    allowance_deductions_ids = fields.One2many('hr.end_of_service.allowance_deduct','end_of_service_id')
    reward_ids = fields.Many2many('hr.employee.rewards')
    show_petty_cash = fields.Boolean(default=False)
    show_custody = fields.Boolean(default=False)
    petty_cash_ids = fields.Many2many('petty.cash')
    hr_custody_ids = fields.Many2many('hr.custody')
    hr_payslip = fields.Many2one('hr.payslip',string="Payslip")
    salary_date_from = fields.Date(string="Salary Date From",related="hr_payslip.date_from")
    salary_date_to = fields.Date(string="Salary Date To",related="hr_payslip.date_to")
    paid_duration  = fields.Float()
    line_ids = fields.Many2many('hr.payslip.line')
    total_loans = fields.Float(compute="_get_amounts")
    total_alw = fields.Float(compute="_get_amounts")
    total_ded = fields.Float(compute="_get_amounts")
    total_net = fields.Float(compute="_get_amounts")
    direct_manager = fields.Many2one('hr.employee', related='employee_id.department_id.manager_id')

    is_manager = fields.Boolean(compute='is_direct_manager', readonly=False)

    @api.depends('direct_manager', 'employee_id','state')
    def is_direct_manager(self):
        for rec in self:
            Manager = self.env.user.employee_id.id
            if rec.state == 'submited':
                if rec.employee_id.coach_id.id == Manager:
                    rec.is_manager = True
                else:
                    rec.is_manager = False
            elif rec.state == 'direct_manager':
                if rec.direct_manager.id == Manager:
                    rec.is_manager = True
                else:
                    rec.is_manager = False
            else:
                rec.is_manager = False

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submited', 'submited'),
        ('direct_manager', 'Direct Manager Approved'),
        ('department_manager', 'Department Manager Approved'),
        ('hr_manager', 'HR Manager Approved'),
        ('ceo_manager', 'CEO Manager Approved'),
        ('complete', 'Completed'),
        ('pay', 'Paid'),
        ('refuse', 'Refuse'),
        ],
        default='draft', track_visibility='onchange')

    def action_submit(self):
        for rec in self:
            rec.state = 'submited'
    def action_direct_manager(self):
        for rec in self:
            rec.state = 'direct_manager'

    def action_department_manager(self):
        for rec in self:
            rec.state = 'department_manager'

    def action_hr_manager(self):
        for rec in self:
            if not rec.hr_payslip:
                raise UserError("Please Select Final Payslip For Employee before any step.")
            rec.state = 'hr_manager'

    def action_ceo_manager(self):
        for rec in self:
            rec.state = 'ceo_manager'

    def action_complete(self):
        for rec in self:
            rec.state = 'complete'

    def action_pay(self):
        for rec in self:
            rec.state = 'pay'

    def action_refuse(self):
        for rec in self:
            rec.state = 'refuse'

    def set_to_draft(self):
        for rec in self:
            rec.state = 'draft'
            

    @api.depends('loan_ids','line_ids','leave_balance_money')
    def _get_amounts(self):
        for rec in self:
            rec.total_loans = rec.total_alw = rec.total_ded = rec.total_net = 0
            if rec.loan_ids:
                for loan in rec.loan_ids:
                    rec.total_loans = rec.total_loans + loan.loan_left_amount
                    # for line in loan.installment_ids:
                    # rec.total_loans = rec.total_loans + sum([ line.monthly_installment - line.paid for line in loan.installment_ids]) 
                # rec.total_loans = sum([ line.monthly_installment - line.paid for line in loan.installment_id for loan in rec.loan_ids])
            if rec.line_ids:
                rec.total_alw = sum([ line.amount for line in rec.line_ids.filtered(lambda slip: slip.category_id.code in ['ALW','BASIC'])]) + rec.leave_balance_money
                rec.total_ded = sum([ line.amount for line in rec.line_ids.filtered(lambda slip: slip.category_id.code in ['DED',])])
            
            if rec.resignation_reason_id.id == rec.env.ref('hr_gratuity_settlement.gratuity_reason_k').id and rec.contract_id.is_active_penalty:
                rec.total_ded = rec.total_ded + rec.contract_id.penalty_value
            rec.total_net = rec.total_alw - rec.total_ded - rec.total_loans


    @api.onchange('hr_payslip')
    def onchange_payroll_set_line_ids(self):
        for rec in self:
            rec.line_ids = False
            if rec.hr_payslip :
                rec.line_ids = rec.hr_payslip.line_ids.filtered(lambda slip: slip.category_id.code in ['ALW','BASIC','DED']).ids


    def get_values(self):
        for rec in self:
            if self.env.ref('hr_end_of_service.default_show_petty_cash').value == '0':
                rec.show_petty_cash = False 
            else:
                rec.show_petty_cash = self.env.ref('hr_end_of_service.default_show_petty_cash').value
            
            if self.env.ref('hr_end_of_service.default_show_custody_eos').value == '0':
                rec.show_custody  = False 
            else:
                rec. show_custody = self.env.ref('hr_end_of_service.default_show_custody_eos').value


    @api.onchange('salary_date_from','salary_date_to')
    def onchange_set_paid_duration(self):
        for rec in self:
            rec.paid_duration = 0
            if rec.salary_date_from and rec.salary_date_to:
                rec.paid_duration = (rec.salary_date_to - rec.salary_date_from).days

    @api.depends('employee_id')
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """ calculating the gratuity pay based on the contract and gratuity
        configurations """
        # self.hr_resignation_id = False
        loan_obj = self.env['loan.advance.request']
        reward_obj = self.env['hr.employee.rewards']
        petty_obj = self.env['petty.cash']
        custody_obj = self.env['hr.custody']
        for rec in self:
            rec.loan_ids = False
            rec.reward_ids = False
            rec.leave_balance = 0
            rec.leave_balance_money = 0
            if rec.employee_id:
                self.get_values()
                employee_id = rec.employee_id
                rec.employee_joining_date = employee_id.contract_id.start_work#contract_sorted[0].date_start

                #remaining leaves
                if rec.contract_id.annual_leave_policy:
                    mapped_days = rec.contract_id.mapped('annual_leave_policy').get_employees_days(rec.mapped('employee_id').ids)
                    
                    # for holiday in self:
                        
                    leave_days = mapped_days[rec.employee_id.id][rec.contract_id.annual_leave_policy.id]
                    
                    # if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                    #     raise ValidationError(_('The number of remaining time off is not sufficient for this time off type.\n'
                    # 
                    #                            'Please also check the time off waiting for validation.'))

                    rec.leave_balance = leave_days['remaining_leaves']
                    if rec.leave_balance :
                        rec.leave_balance_money = 0
                        amount_type = rec.env.ref('hr_end_of_service.default_end_of_service_amount_type').value
                        if amount_type == 'basic_salary':
                            amount = rec.employee_id.contract_id.basic_salary
                        else:
                            amount = rec.employee_id.contract_id.total
    
                        months_days = rec.env.ref('hr_end_of_service.default_end_of_service_months_days').value
                        print(">>>>>>>>>>>>>>>>>>>>>>>>>  ||  ",amount , months_days ,rec.leave_balance )
                        rec.leave_balance_money  = ( amount/float(months_days) ) * rec.leave_balance 

                #loan
                loans = loan_obj.search(
                    [
                        ('employee_id','=',rec.employee_id.id),
                        ('type','=','Loan'),
                        ('state','not in',['New','HR Manager Approve','Financial Manager Approve','GM Approve'])
                
                    ]
                )
                rec.loan_ids = loans.ids

                #allowance deductions
                # rec.employee_id.struct_id

                #rewards
                rewards = reward_obj.search(
                    [
                        ('employee_id','=',rec.employee_id.id),
                        ('state','=','confirmed'),
                        
                    ]
                )
                rec.reward_ids = rewards.ids

                #petty cash
                if rec.show_petty_cash:
                    petties = petty_obj.search(

                        [
                        ('employee_id','=',rec.employee_id.id),
                        
                
                    ]
                    )
                    rec.petty_cash_ids = petties.ids

                #custodies
                if rec.show_custody:
                    custodies = custody_obj.search(

                        [
                        ('employee','=',rec.employee_id.id),
                        
                
                    ]
                    )
                    rec.hr_custody_ids = custodies.ids

                        

    @api.model
    def create(self, vals):
        """ assigning the sequence for the record """
        vals['name'] = self.env['ir.sequence'].next_by_code(self._name)
        return super(hrEndOFService, self).create(vals)

    # def write(self, vals):
    #     for rec in self:
    #         if rec.name == '/':
    #             vals['name']  = self.env['ir.sequence'].next_by_code(self._name)

    #     return super(hrEndOFService, self).write(vals)

