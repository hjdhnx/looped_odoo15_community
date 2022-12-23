# -*- coding: utf-8 -*-
from odoo import api, fields, models


# class hr_loans_configuration(models.TransientModel):
#     _name = 'hr.loans.config.settings'
#     _inherit = 'res.config.settings'

class loan_advancee(models.Model):
    _inherit = 'hr_loans.loan_advance'

    integrate_with_finance = fields.Boolean()
    loan_account_id = fields.Many2one('account.account')
    loan_journal_id = fields.Many2one('account.journal')

    advance_account_id = fields.Many2one('account.account')
    advance_journal_id = fields.Many2one('account.journal')

    integrate_traffic_violation = fields.Boolean()
    another_loan_before_pay = fields.Boolean()
    loans_deduction_percentage = fields.Float()
    violations_deduction_percentage = fields.Float()
    previous_based_on = fields.Selection([('Basic Salary', 'Basic Salary'),
                            ('Total salary', 'Total salary')],'Previous Percentage Based On',
        help ="""previous percentage based on""",default='Total salary')
    absence_based_on = fields.Selection([('basic', 'Basic Salary'),
                                                    ('basic_house', 'Basic + House'),
                                                    ('basic_house_trans', 'Basic + House + Transportation'),
                                                    ('basic_house_trans_phone', 'Basic + House + Transportation + Phone'),
                                                    ('total', 'Total salary')]
        ,'Employee absence deduction based on', default='total')

    loan_reconciliation_method = fields.Selection([('percentage', 'Percentage From Salary'),
                                                    ('installment', 'Installments For Each Loan')]
        ,'Loans Reconciliation Method',default='percentage',)
    module_installment_menu = fields.Boolean('Show Installment Menu')

class hr_loans_setings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    default_integrate_with_finance = fields.Boolean(string='Integrate With Finance',
                                              config_parameter='hr_loans.default_integrate_with_finance',
                                              default_model='hr_loans.loan_advance'
                                              )
    default_loan_account_id = fields.Many2one('account.account',config_parameter='hr_loans.default_loan_account_id',default_model='hr_loans.loan_advance')
    default_loan_journal_id = fields.Many2one('account.journal',config_parameter='hr_loans.default_loan_journal_id',default_model='hr_loans.loan_advance')

    default_advance_account_id = fields.Many2one('account.account',config_parameter='hr_loans.default_advance_account_id',default_model='hr_loans.loan_advance')
    default_advance_journal_id = fields.Many2one('account.journal',config_parameter='hr_loans.default_advance_journal_id',default_model='hr_loans.loan_advance')


    default_integrate_traffic_violation = fields.Boolean('Default Integrate Traffic Violation',
    config_parameter='hr_loans.default_integrate_traffic_violation',
    default_model='hr_loans.loan_advance'
    )




    default_another_loan_before_pay = fields.Boolean('The employee can request another loan before fully pay the old one',
        help ="""Check to allow overlapping loans / salary in advance.""",default_model='hr_loans.loan_advance')
    default_loans_deduction_percentage = fields.Float('Loans monthly deduction percentage from salary',
        help ="""Loans monthly deduction percentage from salary """,default_model='hr_loans.loan_advance',default=25.0)
    default_violations_deduction_percentage = fields.Float('Violations monthly deduction percentage from salary',
        help ="""Violations monthly deduction percentage from salary""",default_model='hr_loans.loan_advance',default=100.0)
    default_previous_based_on = fields.Selection([('Basic Salary', 'Basic Salary'),
                            ('Total salary', 'Total salary')],'Previous Percentage Based On',
        help ="""previous percentage based on""",default_model='hr_loans.loan_advance', default='Total salary')
    default_absence_based_on = fields.Selection([('basic', 'Basic Salary'),
                                                    ('basic_house', 'Basic + House'),
                                                    ('basic_house_trans', 'Basic + House + Transportation'),
                                                    ('basic_house_trans_phone', 'Basic + House + Transportation + Phone'),
                                                    ('total', 'Total salary')]
        ,'Employee absence deduction based on',default_model='hr_loans.loan_advance', default='total')
    default_loan_reconciliation_method = fields.Selection([('percentage', 'Percentage From Salary'),
                                                    ('installment', 'Installments For Each Loan'),]
        ,'Loans Reconciliation Method',default_model='hr_loans.loan_advance', default='percentage',config_parameter='hr_loans.default_loan_reconciliation_method')
    module_installment_menu = fields.Boolean('Show Installment Menu')

    def set_values(self):
        res = super(hr_loans_setings, self).set_values()
        self.env['ir.config_parameter'].set_param('hr_loans.default_loan_reconciliation_method', self.default_loan_reconciliation_method)
        self.env['ir.config_parameter'].set_param('hr_loans.default_integrate_traffic_violation', self.default_integrate_traffic_violation)
        self.env['ir.config_parameter'].set_param('hr_loans.default_another_loan_before_pay', self.default_another_loan_before_pay)
        self.env['ir.config_parameter'].set_param('hr_loans.default_loans_deduction_percentage', self.default_loans_deduction_percentage)
        self.env['ir.config_parameter'].set_param('hr_loans.default_previous_based_on', self.default_previous_based_on)
        self.env['ir.config_parameter'].set_param('hr_loans.default_absence_based_on', self.default_absence_based_on)
        self.env['ir.config_parameter'].set_param('hr_loans.default_loan_reconciliation_method', self.default_loan_reconciliation_method)
        self.env['ir.config_parameter'].set_param('hr_loans.module_installment_menu', self.module_installment_menu)
        
        self.env['ir.config_parameter'].set_param('hr_loans.default_integrate_with_finance', self.default_integrate_with_finance)
        self.env['ir.config_parameter'].set_param('hr_loans.default_loan_journal_id', self.default_loan_journal_id.id)
        self.env['ir.config_parameter'].set_param('hr_loans.default_loan_account_id', self.default_loan_account_id.id)

        print(">>>>>>>>>>>>>>>>>>SET VALS")
        self.env['ir.config_parameter'].set_param('hr_loans.default_advance_journal_id', self.default_advance_journal_id.id)
        self.env['ir.config_parameter'].set_param('hr_loans.default_advance_account_id', self.default_advance_account_id.id)
        
        
        return res


    @api.constrains('default_loans_deduction_percentage', 'default_violations_deduction_percentage')
    def _check_percentage(self):
        for rec in self:
            if rec.default_loans_deduction_percentage < 0 or rec.default_violations_deduction_percentage < 0:
                raise exceptions.ValidationError("Dear HR, \n It is not logic that ( Loans monthly deduction percentage from salary ) or ( Violations monthly deduction percentage from salary ) is minus")
            if rec.default_loans_deduction_percentage == 0 or rec.default_violations_deduction_percentage == 0:
                raise exceptions.ValidationError("Dear HR, \n It is not logic that ( Loans monthly deduction percentage from salary ) or ( Violations monthly deduction percentage from salary ) is zero, this mean that no amounts will be deducted from employee.")
            if rec.default_loans_deduction_percentage > 100 or rec.default_violations_deduction_percentage > 100:
                raise exceptions.ValidationError("Dear HR, \n It is not logic to deduct more than 100% from unpaid loans / unpaid deductions")

    #@api.one
    @api.onchange('default_loan_reconciliation_method')
    def onchange_reconciliation_method(self):
        for rec in self:
            if rec.default_loan_reconciliation_method == 'installment':
                rec.module_installment_menu = True
            else:
                rec.module_installment_menu = False