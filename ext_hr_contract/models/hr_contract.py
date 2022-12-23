# -*- coding: utf-8 -*-

# from openerp.osv import expression
# from openerp.tools.float_utils import float_round as round
# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta


class hr_contract(models.Model):
    _inherit = "hr.contract"

    _ALLOWANCE = [
        ('none', 'None'),
        ('fixed', 'Fixed'),
        ('percentage', 'Percentage from Basic'),
    ]
    employee_eng_name = fields.Char('Employee arabic name', related='employee_id.employee_english_name')
    employee_number = fields.Char('employee number', related='employee_id.employee_number')
    active = fields.Boolean(_('Active'), default=True)
    trial_wage = fields.Float(_('trial Basic Salary'))
    trial_house_allowance_type = fields.Selection(_ALLOWANCE, _('trial House Allowance'), default='none')
    trial_house_allowance = fields.Float(_('trial House Allowance'))
    trial_house_allowance_amount = fields.Float(_('trial House Allowance'), compute='_get_trial_allowance')
    trial_transportation_allowance_type = fields.Selection(_ALLOWANCE, _('trial Transportation Allowance'), default='none')
    trial_transportation_allowance = fields.Float(_('trial Transportation Allowance'))
    trial_transportation_allowance_amount = fields.Float(_('trial Transportation Allowance'), compute='_get_trial_allowance')
    trial_phone_allowance_type = fields.Selection(_ALLOWANCE, _('trial Phone Allowance'), default='none')
    trial_phone_allowance = fields.Float(_('trial Phone Allowance'))
    trial_phone_allowance_amount = fields.Float(_('trial Phone Allowance'), compute='_get_trial_allowance')
    trial_insurance = fields.Boolean(_('Trial Medical Insurance Covered'), default=True)
    trial_commission = fields.Selection([('illegible', 'Illegible'), ('not_illegible', 'Not Illegible')], _('trial Commission'), default='not_illegible')
    trial_other_allowance = fields.Float(_('Other Allowance'))
    trial_other_allowance_name = fields.Char(_('Other Allowance Name'))
    trial_total = fields.Float(_('Total'), compute='_get_trial_total', readonly=True)
    date_end = fields.Date('End Date', readonly=True, compute='_compute_date_end',store=True)
    duration_type = fields.Selection([('Limited Time Contract', 'Limited Time Contract'),
                                      ('Unlimited Time Contract', 'Unlimited Time Contract')], string='Duration Type')
    duration_months = fields.Float(string="Duration In Months")
    total_contract_duration = fields.Char(string='Total Contract Duration', readonly=True, compute='_compute_total_contract_duration', multi=True)
    total_contract_remaining = fields.Char(string='Remaining before expiry', readonly=True, compute='_compute_total_contract_duration', multi=True)
    last_active_duration = fields.Char(string='Total Contract Duration', readonly=True)
    job_id = fields.Many2one('hr.job', 'Job Title', related='employee_id.job_id')
    marital = fields.Selection([('single', 'Single'), ('married', 'Married')], 'Single / Married')
    end_reminder = fields.Integer('Reminder To Review Before End On Contractual Year',help='If = 3, this mean that your system will send a notification and Email to the employee and HR manager to re-check the contract renewing 3 months before the end of contractual year.')
    locked = fields.Boolean('Locked')
    trial_date_start = fields.Date('Trial Start Date',)
    trial_date_end = fields.Date('Trial End Date', )
    trial_in_month = fields.Integer(default=3)
    # journal_id = fields.Many2one('account.journal', 'Salary Journal', readonly=False, required=False,
    #     company_dependent=True,
    #     default=lambda self: self.env['account.journal'].sudo().search([
    #         ('type', '=', 'general'), ('company_id', '=', self.env.company.id)], limit=1))
    #

    notice_days = fields.Integer(string="Notice Period", default=30)
    contract_template = fields.Char()


    @api.onchange('trial_date_start','trial_date_end','trial_in_month','start_work')
    def onchange_set_trial_end_Date(self):
        for rec in self:
            rec.trial_date_start = False
            rec.trial_date_end = False
            if rec.start_work:
                rec.trial_date_start = rec.start_work
            
            if rec.trial_date_start and rec.trial_in_month:
                rec.trial_date_end = rec.trial_date_start + relativedelta(months=rec.trial_in_month)
            return

    @api.constrains('trial_date_start', 'trial_date_end', 'date_start')
    def _check_trial_date(self):
        # if self.trial_date_start > self.trial_date_end:
        #     raise ValidationError('Date Error!! End of trial period date must be greater than or equal start trial period date')
        if self.date_start < self.trial_date_end:
            raise ValidationError('Date error!! Contract start date must be greater than or equal to end trial period date')

    @api.onchange('employee_id')
    def onchange_employee_set_data(self):
        for rec in self:
            # rec.department_id = False
            if rec.employee_id.marital:
                rec.marital = rec.employee_id.marital
            

    #@api.multi
    def toggle_locked(self):
        for record in self:
            record.locked = not record.locked

    #@api.one
    @api.constrains('end_reminder')
    def check_end_reminder(self):
        if self.end_reminder <= 0:
            raise ValidationError(_('Data Error !!\n Renew each must be a positive number with no decimal value!'))

    #@api.multi
    def write(self, vals):
        if self.locked and not self._context.get('button_toggle',False):
            raise ValidationError(_('Not allowed to change this contract because your HR manager already locked the contract. If you think that there is any data error in the contract which requires corrections, kindly contact with HR manager. he have the access rights to unlock the contract.'))

        old_active = self.active

        # Write your logic here
        res = super(hr_contract, self).write(vals)

        new_active = self.active
        if old_active and not new_active:
            self.last_active_duration = self.total_contract_duration

        # Write your logic here
        return res

    @api.depends('trial_date_start', 'date_start', 'date_end')
    def _compute_total_contract_duration(self):
        for rec in self:
            rec._compute_date_end()
            now = datetime.now()
            start_date = rec.date_start
            if rec.trial_date_start:
                start_date = rec.trial_date_start
            end_date = rec.date_end
            if rec.date_end:
                end_date = rec.date_end

            duration = relativedelta(end_date, start_date)
            remaining = relativedelta(end_date, now)
            rec.total_contract_duration = self.alphabet_date(duration)
            rec.total_contract_remaining = self.alphabet_date(remaining)
            # total_str = ''
            # if duration.years:
            #     total_str += _('%s years, ' %(duration.years))
            # if duration.months:
            #     total_str += _('%s months, ' %(duration.months))
            # if duration.days:
            #     total_str += _('%s days' %(duration.days))

    @api.model
    def alphabet_date(self, datetime):
        total_str = ''
        if datetime.years:
            total_str += _('%s years, ' % (datetime.years))
        if datetime.months:
            total_str += _('%s months, ' % (datetime.months))
        if datetime.days:
            total_str += _('%s days' % (datetime.days))
        return total_str

    #@api.multi
    @api.depends('duration_type', 'duration_months', 'date_start')
    def _compute_date_end(self):
        for rec in self:
            if rec.date_start:
                if rec.duration_type != "Limited Time Contract":
                    rec.duration_months = 1000
                duration_months = rec.duration_months
                number_dec = duration_months - int(duration_months)
                int_duration_months = int(duration_months)
                int_days = int(number_dec * 30)
                # date_start = datetime.strptime(rec.date_start, "%Y-%m-%d")
                date_start = rec.date_start
                end_date = date_start + relativedelta(months=int_duration_months, days=int_days)
                rec.date_end = end_date

    @api.constrains('trial_other_allowance', 'trial_other_allowance_name')
    def _check_trial_other_allowance(self):
        if self.trial_other_allowance > 0 and not self.trial_other_allowance_name:
            raise ValidationError(_('Please Select Name For Other Allowance During Trial Period'))

    @api.constrains('duration_months')
    def _check_duration_months(self):
        if self.duration_months <= 0 and self.duration_type == "Limited Time Contract":
            raise ValidationError('Configuration Error!! Contract duration in months cannot equal to zero.')

    #@api.multi
    @api.depends('trial_wage', 'trial_house_allowance_amount', 'trial_transportation_allowance_amount', 'trial_phone_allowance_amount', 'trial_other_allowance')
    def _get_trial_total(self):
        for record in self:
            record.trial_total = record.trial_wage + record.trial_house_allowance_amount + record.trial_transportation_allowance_amount + record.trial_phone_allowance_amount + record.trial_other_allowance

    #@api.multi
    @api.depends('trial_wage', 'trial_house_allowance_type', 'trial_house_allowance', 'trial_transportation_allowance_type', 'trial_transportation_allowance',
                 'trial_phone_allowance_type', 'trial_phone_allowance')
    def _get_trial_allowance(self):
        for record in self:
            if record.trial_house_allowance_type == 'none':
                record.trial_house_allowance_amount = record.trial_house_allowance = 0.0
            elif record.trial_house_allowance_type == 'fixed':
                record.trial_house_allowance_amount = record.trial_house_allowance
            else:
                record.trial_house_allowance_amount = record.trial_house_allowance * record.trial_wage / 100.0

            if record.trial_transportation_allowance_type == 'none':
                record.trial_transportation_allowance_amount = record.trial_transportation_allowance = 0.0
            elif record.trial_transportation_allowance_type == 'fixed':
                record.trial_transportation_allowance_amount = record.trial_transportation_allowance
            else:
                record.trial_transportation_allowance_amount = record.trial_transportation_allowance * record.trial_wage / 100.0

            if record.trial_phone_allowance_type == 'none':
                record.trial_phone_allowance_amount = record.trial_phone_allowance = 0.0
            elif record.trial_phone_allowance_type == 'fixed':
                record.trial_phone_allowance_amount = record.trial_phone_allowance
            else:
                record.trial_phone_allowance_amount = record.trial_phone_allowance * record.trial_wage / 100.0

    basic_salary = fields.Float(_('Basic Salary'))
    house_allowance_type = fields.Selection(_ALLOWANCE, _('House Allowance type'), default='none')
    house_allowance = fields.Float(_('House Allowance'))
    house_allowance_amount = fields.Float(_('House Allowance Amount'), compute='_get_allowance')
    transportation_allowance_type = fields.Selection(_ALLOWANCE, _('Transportation Allowance Type'), default='none')
    transportation_allowance = fields.Float(_('Transportation Allowance'))
    transportation_allowance_amount = fields.Float(_('Transportation Allowance Amount'), compute='_get_allowance')
    phone_allowance_type = fields.Selection(_ALLOWANCE, _('Phone Allowance Type'), default='none')
    phone_allowance = fields.Float(_('Phone Allowance'))
    phone_allowance_amount = fields.Float(_('Phone Allowance Amount'), compute='_get_allowance')

        
    food_allowance_type = fields.Selection(_ALLOWANCE, _('Food Allowance Type'), default='none')
    food_allowance = fields.Float(_('Food Allowance'))
    food_allowance_amount = fields.Float(_('Food Allowance Amount'), compute='_get_allowance')
    
    school_allowance_type = fields.Selection(_ALLOWANCE, _('School Allowance Type'), default='none')
    school_allowance = fields.Float(_('School Allowance'))
    school_allowance_amount = fields.Float(_('School Allowance Amount'), compute='_get_allowance')

    other2_allowance_type = fields.Selection(_ALLOWANCE, _('Other 2 Allowance Type'), default='none')
    other2_allowance = fields.Float(_('Other 2 Allowance'))
    other2_allowance_amount = fields.Float(_('Other 2 Allowance Amount'), compute='_get_allowance')
    
    


    insurance = fields.Boolean(_('Medical Insurance Covered'), default=True)
    commission = fields.Selection([('illegible', 'Illegible'),
                                   ('not_illegible', 'Not Illegible')], _('Commission'), default='not_illegible')
    other_allowance = fields.Float(_('Other Allowance'))
    other_allowance_name = fields.Char(_('Other Allowance Name'))
    total = fields.Float(_('Total'), compute='_get_total', readonly=True)
    # struct_id = fields.Many2one('hr.payroll.structure',string="Salary Structure")

    business_owner_id = fields.Many2one('hr.employee.business_owner',_('Business Owner'), related="employee_id.business_owner_id")
    @api.constrains('other_allowance', 'other_allowance_name')
    def _check_other_allowance(self):
        if self.other_allowance > 0 and not self.other_allowance_name:
            raise ValidationError(_('Please Select Name For Other Allowance After Trial Period'))

    #@api.multi
    @api.depends('basic_salary','food_allowance_amount','school_allowance_amount','other2_allowance_amount', 'house_allowance_amount', 'transportation_allowance_amount', 'phone_allowance_amount', 'other_allowance')
    def _get_total(self):
        for record in self:
            record.total = record.basic_salary + record.house_allowance_amount + record.transportation_allowance_amount + record.phone_allowance_amount + record.food_allowance_amount + record.school_allowance_amount + record.other2_allowance_amount + record.other_allowance

    #@api.multi
    @api.depends('basic_salary','other2_allowance','other2_allowance_type','school_allowance','school_allowance_type','food_allowance_type','food_allowance', 'house_allowance_type', 'house_allowance', 'transportation_allowance_type', 'transportation_allowance', 'phone_allowance_type',
                 'phone_allowance')
    def _get_allowance(self):
        for record in self:
            record.wage = record.basic_salary
            if record.house_allowance_type == 'none':
                record.house_allowance_amount = record.house_allowance = 0.0
            elif record.house_allowance_type == 'fixed':
                record.house_allowance_amount = record.house_allowance
            else:
                record.house_allowance_amount = record.house_allowance * record.basic_salary / 100.0

            if record.transportation_allowance_type == 'none':
                record.transportation_allowance_amount = record.transportation_allowance = 0.0
            elif record.transportation_allowance_type == 'fixed':
                record.transportation_allowance_amount = record.transportation_allowance
            else:
                record.transportation_allowance_amount = record.transportation_allowance * record.basic_salary / 100.0

            if record.phone_allowance_type == 'none':
                record.phone_allowance_amount = record.phone_allowance = 0.0
            elif record.phone_allowance_type == 'fixed':
                record.phone_allowance_amount = record.phone_allowance
            else:
                record.phone_allowance_amount = record.phone_allowance * record.basic_salary / 100.0

            if record.food_allowance_type == 'none':
                record.food_allowance_amount = record.food_allowance = 0.0
            elif record.food_allowance_type == 'fixed':
                record.food_allowance_amount = record.food_allowance
            else:
                record.food_allowance_amount = record.food_allowance * record.basic_salary / 100.0
            
            if record.school_allowance_type == 'none':
                record.school_allowance_amount = record.school_allowance = 0.0
            elif record.school_allowance_type == 'fixed':
                record.school_allowance_amount = record.school_allowance
            else:
                record.school_allowance_amount = record.school_allowance * record.basic_salary / 100.0

            if record.other2_allowance_type == 'none':
                record.other2_allowance_amount = record.other2_allowance = 0.0
            elif record.other2_allowance_type == 'fixed':
                record.other2_allowance_amount = record.other2_allowance
            else:
                record.other2_allowance_amount = record.other2_allowance * record.basic_salary / 100.0

    #@api.one
    @api.constrains('active', 'trial_date_start', 'trial_date_end')  # 'default_credit_account_id', 'default_debit_account_id'
    def _check_currency(self):
        if self.employee_id:
            count = self.search_count([['employee_id', '=', self.employee_id.id], ['active', '=', True]])
            if count >= 2:
                raise UserError(_('Configuration Error!\n'
                                  'We found that there is another active contract for the same employee.'))
        if self.date_start and self.date_end:
            if self.date_start > self.date_end:
                raise UserError(_('Configuration Error!\nContract end date must be greater than contract start date.'))

