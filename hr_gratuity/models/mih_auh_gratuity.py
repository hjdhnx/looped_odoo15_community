# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date
import datetime
from odoo.exceptions import UserError


class MihAuhGratuitySheet(models.Model):
    _name = 'mih.auh.gratuity.sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'id'
    _description = 'Mih Auh Gratuity Sheet'

    
    custom_type = fields.Selection(
        selection= [
            ('less_than_five_year', 'Less Than 5 Year'),
            ('greater_than_five_year', 'Greater Than 5 Year'),
        ],
        string="Type",
        default='less_than_five_year',
    )
    custom_contract_id = fields.Many2one(
        'hr.contract',
        string='Contract',
        readonly=True
    )
    custom_move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True,
        copy=False
    )
    custom_employee_id = fields.Many2one(
        'hr.employee', 
        string='Emplopyee'
    )
    custom_date_of_join = fields.Date(
        string="Date of Join", 
    )
    custom_late_working_day = fields.Date(
        string="Late Working Day", 
    )
    no_of_days = fields.Float(
        string='No of Days',
        compute='_compute_no_of_days'
    )
    custom_lop = fields.Float(
        string='LOP'
    )
    custom_eligible_days = fields.Float(
        string='Eligible Days',
        compute='_compute_eligible_days'
    )
    eligible_days_f_five_years = fields.Float(
        string='Eligible days for first 5 years',
        compute='_compute_eligible_days_f_five_years'
    )
    eligible_days_a_five_years = fields.Float(
        string='Eligible days for after 5 Years',
        compute='_compute_eligible_days_a_five_years'
    )
    esob_days = fields.Float(
        string='ESOB for 1825 days(for 1st 5 year)',
        compute='_compute_esob_days',
        digits=(16, 10)
    )
    esob_a_days = fields.Float(
        string='ESOB for 1825 days(After 5 year)',
        compute='_compute_esob_a_days',
        digits=(16, 10)
    )
    custom_esob_days_sum = fields.Float(
        string='ESOB Days',
        compute='_compute_esob_days_sum'
    )
    custom_basic_salary = fields.Float(
        string='Basic Salary'
    )
    custom_allowance = fields.Float(
        string='Allowance'
    )
    custom_net_salary = fields.Float(
        stirng='Net Salary',
        compute='_compute_custom_net_salary'
    )
    custom_per_day_salary = fields.Float(
        stirng='Per Day Salary',
        compute='_compute_custom_per_day_salary'
    )
    custom_esob_amounts = fields.Float(
        string='EOSB Amount',
        compute='_compute_custom_esob_amounts',
        digits=(16, 7)
    )
    custom_partner_id = fields.Many2one(
        'res.partner',
        string="Partner",
    )
    custom_debit_account_id = fields.Many2one(
        'account.account',
        string='Debit Account',
    )
    custom_credit_account_id = fields.Many2one(
        'account.account',
        string='Credit Account',
    )
    custom_journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        copy=False
    )
    created_by = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True, copy=False,
    )
    created_date = fields.Date(
        string='Created Date', 
        default=fields.Date.today(),
        readonly=True,
    )
    currency_id = fields.Many2one('res.currency', 
        string='Currency', 
        default=lambda self: self.env.user.company_id.currency_id,
        required=True, 
        readonly=True,
    )
    internal_note = fields.Text(
        string='Internal Notes',
        copy=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('lock','Locked'),
        ],
        string="Status",
        default='draft',
        track_visibility='onchange',
        required=True,
        copy=False
    )

    def show_custom_journal_entries(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('id','=', self.custom_move_id.id)]
        return action

    def action_lock(self):
        return self.write({'state': 'lock'})

    def action_unlock(self):
        return self.write({'state': 'draft'})

    def unlink(self):
        for rec in self:
            if rec.state == 'lock':
                raise UserError(_('You can not delete Gratuity Sheet Which is locked.'))
        return super(MihAuhGratuitySheet, self).unlink()

    @api.onchange('custom_employee_id')
    def onchange_custom_employee_id(self):
        for rec in self:
            rec.custom_date_of_join = rec.custom_employee_id.date_of_join

    @api.depends('custom_type','custom_late_working_day','custom_date_of_join')
    def _compute_no_of_days(self):
        for rec in self:
            rec.no_of_days = 0
            if rec.custom_type == 'less_than_five_year':
                if rec.custom_late_working_day and rec.custom_date_of_join:
                    rec.no_of_days = (rec.custom_late_working_day - rec.custom_date_of_join).days + 1
                else:
                    pass
            else:
                if rec.custom_late_working_day and rec.custom_date_of_join:
                    rec.no_of_days = (rec.custom_late_working_day - rec.custom_date_of_join).days + 1
                else:
                    pass

    @api.depends('custom_type','no_of_days','custom_lop')
    def _compute_eligible_days(self):
        for rec in self:
            if rec.custom_type == 'less_than_five_year':
                rec.custom_eligible_days = rec.no_of_days - rec.custom_lop
            else:
                rec.custom_eligible_days = rec.no_of_days - rec.custom_lop

    @api.depends('custom_eligible_days', 'eligible_days_f_five_years' ,'custom_type')
    def _compute_eligible_days_f_five_years(self):
        for rec in self:
            if rec.custom_type == 'less_than_five_year':
                if rec.custom_eligible_days >= 1825:
                    rec.eligible_days_f_five_years = 1825
                elif rec.custom_eligible_days < (rec.custom_eligible_days):
                    rec.eligible_days_f_five_years = rec.custom_eligible_days
                else:
                    rec.eligible_days_f_five_years = rec.custom_eligible_days
            else:
                if rec.custom_eligible_days >= 1825:
                    rec.eligible_days_f_five_years =  1825
                else:
                    rec.eligible_days_f_five_years = 0

    @api.depends('custom_eligible_days', 'eligible_days_a_five_years', 'custom_type')
    def _compute_eligible_days_a_five_years(self):
        for rec in self:
            if rec.custom_type == 'less_than_five_year':
                ced = (rec.custom_eligible_days * 5)
                if rec.custom_eligible_days > ced:
                    rec.eligible_days_a_five_years = rec.custom_eligible_days - ced
                else:
                    rec.eligible_days_a_five_years = 0
            else:
                ced = (rec.custom_eligible_days)
                if rec.custom_eligible_days > 1825:
                    rec.eligible_days_a_five_years = rec.custom_eligible_days - 1825
                else:
                    rec.eligible_days_a_five_years = 0

    @api.depends('custom_type','custom_eligible_days','eligible_days_f_five_years')
    def _compute_esob_days(self):
        for rec in self:
            if rec.custom_type == 'less_than_five_year':
                rec.esob_days = (rec.custom_eligible_days * 21)/365
            else:
                rec.esob_days = (rec.eligible_days_f_five_years * 21)/365

    @api.depends('custom_type','eligible_days_a_five_years')
    def _compute_esob_a_days(self):
        for rec in self:
            if rec.custom_type == 'less_than_five_year':
                rec.esob_a_days = (rec.eligible_days_a_five_years * 21)/365
            else:
                rec.esob_a_days = (rec.eligible_days_a_five_years * 21)/365

    @api.depends('custom_type','esob_days','esob_a_days')
    def _compute_esob_days_sum(self):
        for rec in self:
            if rec.custom_type == 'less_than_five_year':
                rec.custom_esob_days_sum = rec.esob_days + rec.esob_a_days
            else:
                rec.custom_esob_days_sum = rec.esob_days + rec.esob_a_days

    @api.depends('custom_type','custom_basic_salary','custom_allowance')
    def _compute_custom_net_salary(self):
        for rec in self:
            if rec.custom_type == 'less_than_five_year':
                rec.custom_net_salary = rec.custom_basic_salary + rec.custom_allowance
            else:
                rec.custom_net_salary = rec.custom_basic_salary + rec.custom_allowance

    @api.depends('custom_type','custom_basic_salary')
    def _compute_custom_per_day_salary(self):
        for rec in self:
            if rec.custom_type == 'less_than_five_year':
                rec.custom_per_day_salary = (rec.custom_basic_salary * 12)/365
            else:
                rec.custom_per_day_salary = (rec.custom_basic_salary * 12)/365

    @api.depends('custom_type','custom_per_day_salary','custom_esob_days_sum')
    def _compute_custom_esob_amounts(self):
        for rec in self:
            if rec.custom_type == 'less_than_five_year':
                rec.custom_esob_amounts = rec.custom_per_day_salary * rec.custom_esob_days_sum
            else:
                rec.custom_esob_amounts = round(rec.custom_per_day_salary,2) * round(rec.custom_esob_days_sum,2)
