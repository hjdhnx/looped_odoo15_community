# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, exceptions, _

class hr_loans_configuration(models.TransientModel):
    _name = 'hr.loans.config.settings'
    _inherit = 'res.config.settings'
    
    # hr_presence_control_login = fields.Boolean(string="Based on user status in system", config_parameter='hr.hr_presence_control_login')
    
    default_integrate_with_finance = fields.Boolean('Integrate with finance',
        help ="""Integrate with finance""",default_model='hr.loans.config.settings')
    default_loan_account_id = fields.Many2one('account.account')
    default_loan_journal_id = fields.Many2one('account.journal')
    
    default_integrate_traffic_violation = fields.Boolean('Integrate with traffic violation system',
        help ="""Integrate with traffic violation system""",default_model='hr.loans.config.settings')
    default_another_loan_before_pay = fields.Boolean('The employee can request another loan before fully pay the old one',
        help ="""Check to allow overlapping loans / salary in advance.""",default_model='hr.loans.config.settings')
    default_loans_deduction_percentage = fields.Float('Loans monthly deduction percentage from salary',
        help ="""Loans monthly deduction percentage from salary """,default_model='hr.loans.config.settings',default=25.0)
    default_violations_deduction_percentage = fields.Float('Violations monthly deduction percentage from salary',
        help ="""Violations monthly deduction percentage from salary""",default_model='hr.loans.config.settings',default=100.0)
    default_previous_based_on = fields.Selection([('Basic Salary', 'Basic Salary'),
                            ('Total salary', 'Total salary')],'Previous Percentage Based On',
        help ="""previous percentage based on""",default_model='hr.loans.config.settings', default='Total salary')
    default_absence_based_on = fields.Selection([('basic', 'Basic Salary'),
                                                    ('basic_house', 'Basic + House'),
                                                    ('basic_house_trans', 'Basic + House + Transportation'),
                                                    ('basic_house_trans_phone', 'Basic + House + Transportation + Phone'),
                                                    ('total', 'Total salary')]
        ,'Employee absence deduction based on',default_model='hr.loans.config.settings', default='total')
    default_loan_reconciliation_method = fields.Selection([('percentage', 'Percentage From Salary'),
                                                    ('installment', 'Installments For Each Loan')]
        ,'Loans Reconciliation Method',default_model='hr.loans.config.settings', default='percentage',config_parameter='hr_loans.default_loan_reconciliation_method')
    module_installment_menu = fields.Boolean('Show Installment Menu')

    #@api.one
    @api.onchange('default_integrate_with_finance')
    def onchange_integrate_with_finance_set_accounts(self):
        for rec in self:
            rec.default_loan_account_id = rec.default_loan_journal_id = False
            

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