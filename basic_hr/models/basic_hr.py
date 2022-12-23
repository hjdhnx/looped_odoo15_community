# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
# from base_tech import *

import logging

# _logger = logging.getLogger(__name__)
# _logger.info(error_msg)

logger = '2019-06-30'


class salary_details(models.Model):
    _name = "salary.details"

    state = fields.Selection([
        ('new', 'New'),
        ('confirmed', 'Confirmed'),
    ], string="Status", default='new', track_visibility='onchange')

    READONLY_STATES = {'confirmed': [('readonly', True)]}

    _ALLOWANCE = [
        ('none', 'None'),
        ('fixed', 'Fixed'),
        ('percentage', 'Percentage from Basic'),
    ]
    # Trial Period
    trial_house_allowance_type = fields.Selection(_ALLOWANCE, 'House Allowance', default='none', states=READONLY_STATES)
    trial_house_allowance = fields.Float('House Allowance', states=READONLY_STATES)
    trial_house_allowance_amount = fields.Float('House Allowance amount', states=READONLY_STATES)
    trial_transportation_allowance_type = fields.Selection(_ALLOWANCE, 'Transportation Allowance', default='none', states=READONLY_STATES)
    trial_transportation_allowance = fields.Float('Transportation Allowance', states=READONLY_STATES)
    trial_transportation_allowance_amount = fields.Float('Transportation Allowance amount', states=READONLY_STATES)
    trial_phone_allowance_type = fields.Selection(_ALLOWANCE, 'Phone Allowance', default='none', states=READONLY_STATES)
    trial_phone_allowance = fields.Float('Phone Allowance', states=READONLY_STATES)
    trial_phone_allowance_amount = fields.Float('Phone Allowance amount', states=READONLY_STATES)
    trial_insurance = fields.Boolean('Insurance Allowance', default=True, states=READONLY_STATES)
    trial_commission = fields.Selection([('illegible', 'Illegible'), ('not_illegible', 'Not Illegible')], 'Commission', default='not_illegible',
                                        states=READONLY_STATES)
    trial_other_allowance = fields.Float('Other Allowance', states=READONLY_STATES)
    trial_other_allowance_name = fields.Char('Other Allowance Name', states=READONLY_STATES)

    @api.constrains('trial_other_allowance', 'trial_other_allowance_name')
    def _check_trial_other_allowance(self):
        if self.trial_other_allowance > 0 and not self.trial_other_allowance_name:
            raise ValidationError(_('Please Select Name For Other Allowance During Trial Period'))

    house_allowance_type = fields.Selection(_ALLOWANCE, 'House Allowance', default='none', states=READONLY_STATES)
    house_allowance = fields.Float('House Allowance', states=READONLY_STATES)
    house_allowance_amount = fields.Float('House Allowance amount', states=READONLY_STATES)
    transportation_allowance_type = fields.Selection(_ALLOWANCE, 'Transportation Allowance', default='none', states=READONLY_STATES)
    transportation_allowance = fields.Float('Transportation Allowance', states=READONLY_STATES)
    transportation_allowance_amount = fields.Float('Transportation Allowance amount', states=READONLY_STATES)
    phone_allowance_type = fields.Selection(_ALLOWANCE, 'Phone Allowance', default='none', states=READONLY_STATES)
    phone_allowance = fields.Float('Phone Allowance', states=READONLY_STATES)
    phone_allowance_amount = fields.Float('Phone Allowance', states=READONLY_STATES)
    insurance = fields.Boolean('Insurance Allowance', default=True, states=READONLY_STATES)
    commission = fields.Selection([('illegible', 'Illegible'),
                                   ('not_illegible', 'Not Illegible')], 'Commission', default='not_illegible', states=READONLY_STATES)
    other_allowance = fields.Float('Other Allowance', states=READONLY_STATES)
    other_allowance_name = fields.Char('Other Allowance Name', states=READONLY_STATES)

    @api.constrains('other_allowance', 'other_allowance_name')
    def _check_other_allowance(self):
        if self.other_allowance > 0 and not self.other_allowance_name:
            raise ValidationError(_('Please Select Name For Other Allowance After Trial Period'))

    @api.model
    def update_allowances_from(self, source, dest):
        self.env[dest._name].write({
            'trial_house_allowance_type': source.trial_house_allowance_type,
            'trial_house_allowance': source.trial_house_allowance,
            'trial_house_allowance_amount': source.trial_house_allowance_amount,
            'trial_transportation_allowance_type': source.trial_transportation_allowance_type,
            'trial_transportation_allowance': source.trial_transportation_allowance,
            'trial_transportation_allowance_amount': source.trial_transportation_allowance_amount,
            'trial_phone_allowance_type': source.trial_phone_allowance_type,
            'trial_phone_allowance': source.trial_phone_allowance,
            'trial_phone_allowance_amount': source.trial_phone_allowance_amount,
            'trial_insurance': source.trial_insurance,
            'trial_commission': source.trial_commission,
            'trial_other_allowance': source.trial_other_allowance,
            'trial_other_allowance_name': source.trial_other_allowance_name,
            'house_allowance_type': source.house_allowance_type,
            'house_allowance': source.house_allowance,
            'house_allowance_amount': source.house_allowance_amount,
            'transportation_allowance_type': source.transportation_allowance_type,
            'transportation_allowance': source.transportation_allowance,
            'transportation_allowance_amount': source.transportation_allowance_amount,
            'phone_allowance_type': source.phone_allowance_type,
            'phone_allowance': source.phone_allowance,
            'phone_allowance_amount': source.phone_allowance_amount,
            'insurance': source.insurance,
            'commission': source.commission,
            'other_allowance': source.other_allowance,
            'other_allowance_name': source.other_allowance_name,
        })

    @api.model
    def update_allowances_from_(self, source, dest):
        dest.trial_house_allowance_type = source.trial_house_allowance_type
        dest.trial_house_allowance = source.trial_house_allowance
        dest.trial_house_allowance_amount = source.trial_house_allowance_amount
        dest.trial_transportation_allowance_type = source.trial_transportation_allowance_type
        dest.trial_transportation_allowance = source.trial_transportation_allowance
        dest.trial_transportation_allowance_amount = source.trial_transportation_allowance_amount
        dest.trial_phone_allowance_type = source.trial_phone_allowance_type
        dest.trial_phone_allowance = source.trial_phone_allowance
        dest.trial_phone_allowance_amount = source.trial_phone_allowance_amount
        dest.trial_insurance = source.trial_insurance
        dest.trial_commission = source.trial_commission
        dest.trial_other_allowance = source.trial_other_allowance
        dest.trial_other_allowance_name = source.trial_other_allowance_name
        dest.house_allowance_type = source.house_allowance_type
        dest.house_allowance = source.house_allowance
        dest.house_allowance_amount = source.house_allowance_amount
        dest.transportation_allowance_type = source.transportation_allowance_type
        dest.transportation_allowance = source.transportation_allowance
        dest.transportation_allowance_amount = source.transportation_allowance_amount
        dest.phone_allowance_type = source.phone_allowance_type
        dest.phone_allowance = source.phone_allowance
        dest.phone_allowance_amount = source.phone_allowance_amount
        dest.insurance = source.insurance
        dest.commission = source.commission
        dest.other_allowance = source.other_allowance
        dest.other_allowance_name = source.other_allowance_name


class Loan_type(models.Model):
    _name = "hr_loans.loan_advance"
    _description = "Loan Types"
    #for perminant mig
    name = fields.Char(_('Loan / advance description'), required=True)
    type = fields.Selection([('Loan', 'Loan'),], _('Loan / Advance Type'), required=True,default='Loan')
    maximum_amount = fields.Selection([('Unlimited', 'Unlimited'),
                                       ('Based On Basic Salary', 'Based On Basic Salary'),]
                                      , _('Maximum Amount'), required=True,
                                      help="""Determine maximum amount which is allowed for this loan / advance""")
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


class loan_advance_request(models.Model):
    _name = 'loan.advance.request'
    _description = "Loan request"


class contract(models.Model):
    _inherit = "hr.contract"
    remaining_rewards = fields.Float()


class Employee(models.Model):
    _inherit = "hr.employee"

    wage = fields.Float()
    employee_status = fields.Selection([
        ('work', 'on work'),
        ('finished', 'Finished'),
        ('escape', 'Escape'),
        ('stop', 'Stop'),
    ], string="Employee status")

    total = fields.Float('Total salary', )
    joining_date = fields.Date('Join date', )
    salary_pay_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank'),
    ], string="Salary pay method")
    provision_air_ticket = fields.Float('Provision (air ticket)', )
    provision_leave = fields.Float('Provision (Leave)')
    provision_eoc = fields.Float('Provision (EOC)')
    housing_way = fields.Selection([])
    house_allowance_amount = fields.Float('House Allowance')
    transportation_allowance_amount = fields.Float('Transportation Allowance', )
    phone_allowance_amount = fields.Float('Phone Allowance')
    food_allowance_amount = fields.Float('Food Allowance', )
    work_allowance_amount = fields.Float('Nature of Work Allowance', )