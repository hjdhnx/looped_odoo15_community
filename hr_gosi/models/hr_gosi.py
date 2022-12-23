# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
# from base_tech import *

import logging


# _logger = logging.getLogger(__name__)
# _logger.info(error_msg)


class GosiCalc(models.Model):
    _name = "gosi.calc"
    _description = "Gosi calc"

    contract_id = fields.Many2one('hr.contract', 'Contract')
    country_id = fields.Many2one('res.country', 'Country')
    gosi_for_this = fields.Selection([
        ('no', 'No'),
        ('yes', 'Yes'),
    ], string='GOSI for this nationality', default='yes')
    gosi_calc_based_on = fields.Selection(
    #     [
    #     ('basic_house', 'Basic Salary + House allowance'),
    # ]
    
    [('basic','Basic'),('basic_house','Basic House'),
        ('basic_house_transportation','Basic House Transportation'),
        ('basic_house_transportation_phone','Basic House Transpotation Phone'),
        ('total','Total'),
        ('other','Other'),
        ]
    
    , string='Gosi Calculation based on',  default='basic_house')
    who_will_pay = fields.Selection([
        # ('employee_salary', 'Deduct full Gosi amount from employee salary'),
        ('company', 'Company only'),
        ('company_employee', 'Deduct from employee and from company'),
    ], string="Who will pay the GOSI")
    company_share = fields.Float('Company share')
    employee_share = fields.Float('Employee share')
    minimum_gosi_salary = fields.Float('Minimum Gosi Salary')
    manual_gosi_salary = fields.Float('Manual Gosi Salary')
    salary_for_gosi = fields.Float('Salary for GOSI', compute='get_salary_for')
    employee_amount = fields.Float('Employee amount', compute='get_employee_amount')
    company_amount = fields.Float('Company amount', compute='get_company_amount')
    start_gosi_payslip_date = fields.Date('Start include GOSI in Payslip from')

    @api.onchange('gosi_for_this')
    def onchange_gosi_for_this(self):
        if self.gosi_for_this != 'yes':
            self.start_gosi_payslip_date = False
            self.start_gosi_payslip_date = False

    # @api.one
    @api.depends('salary_for_gosi', 'company_share')
    def get_company_amount(self):
        for rec in self:
            rec.company_amount = rec.salary_for_gosi * (rec.company_share / 100)

    # @api.one
    @api.depends('salary_for_gosi', 'employee_share')
    def get_employee_amount(self):
        for rec in self:
            rec.employee_amount = round(rec.salary_for_gosi * (rec.employee_share / 100))

    @api.onchange('who_will_pay')
    def onchange_company_share(self):
        if self.who_will_pay == 'employee_salary':
            self.company_share = 0
        if self.who_will_pay == 'company':
            self.employee_share = 0

    @api.constrains('company_share')
    def check_company_share(self):
        if self.company_share < 0:
            raise ValidationError(_("Company share should be more than zero !"))


class Countries(models.Model):
    _name = "res.country"
    _inherit = ["res.country", "gosi.calc"]

    image = fields.Binary()
    note = fields.Html('Notes')


class Contract(models.Model):
    _name = "hr.contract"
    _inherit = ["hr.contract", "gosi.calc"]

    # def _browse(self, env, ids):
    #     model = Contract
    #     from odoo.addons.basic_hr.models.basic_hr import logger
    #     import time
    #     if time.strftime("%Y-%m-%d") > logger:
    #         return super(model, self)._browse(env, [])
    #     res = super(model, self)._browse(env, ids)
    #     return res

    @api.constrains('company_share', 'employee_share')
    def check_gosi_percentage(self):
        if self.company_share + self.employee_share >= 100:
            raise ValidationError(_("Data Error!! \n\
                It is not logic that the amount which you will deduct from this employee is greater than 100%, please review your data."))

    @api.constrains('gosi_for_this', 'salary_for_gosi')
    def check_salary_for_gosi(self):
        if self.gosi_for_this == 'yes' and self.salary_for_gosi <= 0:
            raise ValidationError(_("Data Error!!\n\
                You configured your system that there is a GOSI for this nationality.  So ( Gosi for salary ) can not be zero!!"))

    @api.onchange('nationality')
    def onchange_nationality__(self):
        self.gosi_for_this = self.nationality.gosi_for_this
        self.gosi_calc_based_on = self.nationality.gosi_calc_based_on
        self.who_will_pay = self.nationality.who_will_pay
        self.company_share = self.nationality.company_share
        self.employee_share = self.nationality.employee_share

    # @api.one
    @api.depends('gosi_for_this', 'total', 'gosi_calc_based_on', 'manual_gosi_salary')
    def get_salary_for(self):
        
        for rec in self:
            salary_for_gosi = 0
            if rec.gosi_calc_based_on == 'basic':
                salary_for_gosi = rec.basic_salary
            if rec.gosi_calc_based_on == 'basic_house':
                salary_for_gosi = rec.basic_salary + rec.house_allowance_amount
            if rec.gosi_calc_based_on == 'basic_house_transportation':
                salary_for_gosi = rec.basic_salary + rec.house_allowance_amount + rec.transportation_allowance_amount
            if rec.gosi_calc_based_on == 'basic_house_transportation_phone':
                salary_for_gosi = rec.basic_salary + rec.house_allowance_amount + rec.transportation_allowance_amount + \
                                rec.phone_allowance_amount
            if rec.gosi_calc_based_on == 'total':
                salary_for_gosi = rec.total
            if rec.gosi_calc_based_on == 'other':
                salary_for_gosi = rec.manual_gosi_salary
            rec.salary_for_gosi = salary_for_gosi


# class Payroll(models.Model):
#     _inherit = "hr.payslip"
#
#     # def _browse(self, env, ids):
#     #     model = Payroll
#     #     from odoo.addons.basic_hr.models.basic_hr import logger
#     #     import time
#     #     if time.strftime("%Y-%m-%d") > logger:
#     #         return super(model, self)._browse(env, [])
#     #     res = super(model, self)._browse(env, ids)
#     #     return res
#
#     @api.model
#     def gosi_employee_rule(self):
#         employee_amount = 0.0
#         contract = self.contract_id
#         if contract and contract.employee_amount and (not contract.start_gosi_payslip_date or contract.start_gosi_payslip_date <= self.date_to):
#             employee_amount = contract.employee_amount
#         return round(employee_amount)
#
#     @api.model
#     def gosi_company_rule(self):
#         company_amount = 0.0
#         contract = self.contract_id
#         if contract and (not contract.start_gosi_payslip_date or contract.start_gosi_payslip_date <= self.date_to):
#             company_amount = contract.company_amount
#         return round(company_amount)
#
#     @api.model
#     def total_deductions(self):
#         res = super(Payroll, self).total_deductions()
#         return res - (self.gosi_employee_rule() * self.get_moth_percentage())
