# -*- coding: utf-8 -*-
# from base_tech import *

from odoo import models, fields, api, _
import datetime
from odoo.exceptions import UserError, ValidationError
import time
from dateutil.relativedelta import relativedelta


# _logger = logging.getLogger(__name__)
# _logger.info(error_msg)

class DeductionViolationCategory(models.Model):
    _name = "deduction.violation.category"
    _inherit = "mail.thread"
    _description = "Deduction / Violation category"
    _order = "id desc"

    READONLY_STATES = {'confirmed': [('readonly', True)]}
    code = fields.Char('code')
    name = fields.Char('Arabic name', states=READONLY_STATES)
    english_name = fields.Char('English name', states=READONLY_STATES)
    sub_type_ids = fields.One2many('deduction.violation.type', 'deduction_categ_id', 'Sub types')
    note = fields.Html('Notes', states=READONLY_STATES)
    state = fields.Selection([
        ('new', 'New'),
        ('confirmed', 'Confirmed'),
    ], string='Status', track_visibility='onchange', default='new')

    def action_new(self):
        self.state = 'new'
    #@api.one
    def confirm(self):
        self.state = 'confirmed'

    #@api.multi
    def open_employee_deductions(self):
        return {
            'domain': [['deduction_violation_category_id', '=', self.id]],
            'name': _('Employee deductions - violations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'employee.deductions.violations',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_deduction_violation_category_id': self.id},
        }

    @api.model
    def create(self, vals):
        res = super(DeductionViolationCategory, self).create(vals)
        res.code = self.env['ir.sequence'].next_by_code(self._name)
        return res

    #@api.one
    def unlink(self):
        if self.state == 'confirmed':
            raise ValidationError(_("Can not delete while confirmed"))


class DeductionViolationType(models.Model):
    _name = "deduction.violation.type"
    _inherit = "mail.thread"
    _description = "Deduction / Violation Types"
    _order = "id desc"

    # def _browse(self, env, ids):
    #     model = DeductionViolationType
    #     from odoo.addons.basic_hr.models.basic_hr import logger
    #     import time
    #     if time.strftime("%Y-%m-%d") > logger:
    #         return super(model, self)._browse(env, [])
    #     res = super(model, self)._browse(env, ids)
    #     return res

    state = fields.Selection([
        ('new', 'New'),
        ('confirmed', 'Confirmed'),
    ], string='Status', track_visibility='onchange', default='new')
    code = fields.Char('code')
    name = fields.Char('Violation / deduction Arabic Description')
    english_name = fields.Char('Violation / deduction English Description')
    deduction_categ_id = fields.Many2one('deduction.violation.category', 'Deduction / Violation category')
    deduction_based_on = fields.Selection([
        ('basic', 'Basic Salary'),
        ('basic_house', 'Basic Salary + House allowance'),
        ('basic_house_transportation', 'Basic Salary + House allowance + transportation'),
        ('basic_house_transportation_phone', 'Basic salary + House + transportation + phone'),
        ('total', 'Total salary'),
    ], string='Deduction based on')
    # First time
    deduction_type1 = fields.Selection([
        ('verbal', 'Verbal warning'),
        ('letter', 'Send notification letter'),
        ('deduction', 'Deduct from employee salary'),
        ('deduction_action', 'Deduct from employee salary + other action'),
    ], string="Deduction type")
    template1_id = fields.Many2one('mail.template', 'Notification letter', domain=lambda self: [['model', '=', self._name]])
    deduction_percentage1 = fields.Float('Deduction percentage')
    other_action1 = fields.Selection([
        ('terminate', 'Termination without rewards'),
        ('terminate_rewards', 'Termination with rewards'),
        ('other', 'Other action'),
    ], string='Other action')
    other_action_desc1 = fields.Char('Other action description')
    # second time
    deduction_type2 = fields.Selection([
        ('verbal', 'Verbal warning'),
        ('letter', 'Send notification letter'),
        ('deduction', 'Deduct from employee salary'),
        ('deduction_action', 'Deduct from employee salary + other action'),
    ], string="Deduction type")
    template2_id = fields.Many2one('mail.template', 'Notification letter', domain=lambda self: [['model', '=', self._name]])
    deduction_percentage2 = fields.Float('Deduction percentage')
    other_action2 = fields.Selection([
        ('terminate', 'Termination without rewards'),
        ('terminate_rewards', 'Termination with rewards'),
        ('other', 'Other action'),
    ], string='Other action')
    other_action_desc2 = fields.Char('Other action description')
    # Third time
    deduction_type3 = fields.Selection([
        ('verbal', 'Verbal warning'),
        ('letter', 'Send notification letter'),
        ('deduction', 'Deduct from employee salary'),
        ('deduction_action', 'Deduct from employee salary + other action'),
    ], string="Deduction type")
    template3_id = fields.Many2one('mail.template', 'Notification letter', domain=lambda self: [['model', '=', self._name]])
    deduction_percentage3 = fields.Float('Deduction percentage')
    other_action3 = fields.Selection([
        ('terminate', 'Termination without rewards'),
        ('terminate_rewards', 'Termination with rewards'),
        ('other', 'Other action'),
    ], string='Other action')
    other_action_desc3 = fields.Char('Other action description')
    # Forth time
    deduction_type4 = fields.Selection([
        ('verbal', 'Verbal warning'),
        ('letter', 'Send notification letter'),
        ('deduction', 'Deduct from employee salary'),
        ('deduction_action', 'Deduct from employee salary + other action'),
    ], string="Deduction type")
    template4_id = fields.Many2one('mail.template', 'Notification letter', domain=lambda self: [['model', '=', self._name]])
    deduction_percentage4 = fields.Float('Deduction percentage')
    other_action4 = fields.Selection([
        ('terminate', 'Termination without rewards'),
        ('terminate_rewards', 'Termination with rewards'),
        ('other', 'Other action'),
    ], string='Other action')
    other_action_desc4 = fields.Char('Other action description')

    confirm_uid = fields.Many2one('res.users', 'Confirmed by')
    employee_deduction_ids = fields.One2many('employee.deductions.violations', 'violation_type_id', 'Employees Deduction History')
    attachment_ids = fields.One2many('deduction.type.attaches', 'type_id', 'Attachments')
    note = fields.Html('Notes')
    model_name = fields.Char('Model name', default=lambda self: self._name)

    #@api.multi
    def employee_history(self):
        return {
            'domain': [['violation_type_id', '=', self.id]],
            'name': _('Employees Deduction History'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'employee.deductions.violations',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_violation_type_id': self.id},
        }

    #@api.one
    def confirm(self):
        self.state = 'confirmed'
        self.confirm_uid = self.env.user.id

    #@api.one
    def reset(self):
        self.state = 'new'

    @api.onchange('deduction_type1')
    def onchange_other_action1(self):
        self.other_action_desc1 = False

    @api.onchange('deduction_type1')
    def onchange_deduction_type1(self):
        self.template1_id = False
        self.deduction_percentage1 = False
        self.other_action1 = False

    @api.onchange('deduction_type2')
    def onchange_other_action2(self):
        self.other_action_desc2 = False

    @api.onchange('deduction_type2')
    def onchange_deduction_type2(self):
        self.template2_id = False
        self.deduction_percentage2 = False
        self.other_action2 = False

    @api.onchange('deduction_type3')
    def onchange_other_action3(self):
        self.other_action_desc3 = False

    @api.onchange('deduction_type3')
    def onchange_deduction_type3(self):
        self.template3_id = False
        self.deduction_percentage3 = False
        self.other_action3 = False

    @api.onchange('deduction_type4')
    def onchange_other_action4(self):
        self.other_action_desc4 = False

    @api.onchange('deduction_type4')
    def onchange_deduction_type4(self):
        self.template4_id = False
        self.deduction_percentage4 = False
        self.other_action4 = False

    @api.constrains(
        'deduction_type1', 'deduction_percentage1',
        'deduction_type2', 'deduction_percentage2',
        'deduction_type3', 'deduction_percentage3',
        'deduction_type4', 'deduction_percentage4',
    )
    def check_deduction_percentage(self):
        if self.deduction_type1 in ['deduction', 'deduction_action'] and self.deduction_percentage1 <= 0:
            raise ValidationError(_("Deduction percentage can not be zero"))
        if self.deduction_type2 in ['deduction', 'deduction_action'] and self.deduction_percentage2 <= 0:
            raise ValidationError(_("Deduction percentage can not be zero"))
        if self.deduction_type3 in ['deduction', 'deduction_action'] and self.deduction_percentage3 <= 0:
            raise ValidationError(_("Deduction percentage can not be zero"))
        if self.deduction_type4 in ['deduction', 'deduction_action'] and self.deduction_percentage4 <= 0:
            raise ValidationError(_("Deduction percentage can not be zero"))

    @api.model
    def create(self, vals):
        res = super(DeductionViolationType, self).create(vals)
        res.code = self.env['ir.sequence'].next_by_code(self._name)
        return res

    #@api.one
    def unlink(self):
        if self.state == 'confirmed':
            raise ValidationError(_("can not delete while confirmed"))
        super(DeductionViolationType, self).unlink()


class EmployeeDeductionsViolations(models.Model):
    _name = "employee.deductions.violations"
    _inherit = "mail.thread"
    _description = "Employee deductions - violations"
    _order = "id desc"
    _rec_name = "employee_id"

    # def _browse(self, env, ids):
    #     model = EmployeeDeductionsViolations
    #     from odoo.addons.basic_hr.models.basic_hr import logger
    #     import time
    #     if time.strftime("%Y-%m-%d") > logger:
    #         return super(model, self)._browse(env, [])
    #     res = super(model, self)._browse(env, ids)
    #     return res
    MONTHS_SELECTION = {'1': 'January', '2': 'February', '3': 'March', '4': 'April', '5': 'May', '6': 'June', '7': 'July', '8': 'August',
                        '9': 'September', '10': 'October', '11': 'November', '12': 'December'}
    state = fields.Selection([
        ('new', 'New'),
        ('reviewed', 'Reviewed'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='new', track_visibility='onchange')
    code = fields.Char('Code')
    deduction_violation_category_id = fields.Many2one('deduction.violation.category', 'Violation - deduction category',
                                                related='violation_type_id.deduction_categ_id', store=True)
    violation_type_id = fields.Many2one('deduction.violation.type', 'Violation Type')
    desc = fields.Char('Description')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    contract_id = fields.Many2one('hr.contract', 'Contract', related='employee_id.contract_id', store=True)
    department_id = fields.Many2one('hr.department', 'Department', related='employee_id.department_id', store=True)
    adjusted_date = fields.Date('Adjusted date', related='contract_id.adjusted_date')
    deduction_date = fields.Date('Deduction date')
    month = fields.Char('Month', compute='get_month', store=True)
    deduction_reason = fields.Selection([
        ('manual', 'Manual deduction'),
        ('violation', 'Violation'),
        ('other', 'Other'),
    ], string='Deduction Reason')
    previous_violations = fields.Integer('Previous violations', compute='get_previous_violations', store=True)
    decision = fields.Selection([
        ('verbal', 'Verbal warning'),
        ('letter', 'Send notification letter'),
        ('deduction', 'Deduct from employee salary'),
        ('deduction_action', 'Deduct from employee salary + other action'),
    ], string='Decision')
    template_id = fields.Many2one('mail.template', 'Notification letter', domain=lambda self: [['model', '=', self._name]])
    deduction_percentage = fields.Float('Deduction percentage')
    other_action = fields.Selection([
        ('terminate', 'Termination without rewards'),
        ('terminate_rewards', 'Termination with rewards'),
        ('other', 'Other action'),
    ], string='Other action')
    action_desc = fields.Char('Other action description')
    deduction_based_on = fields.Selection([
        ('basic', 'Basic Salary'),
        ('basic_house', 'Basic Salary + House allowance'),
        ('basic_house_transportation', 'Basic Salary + House allowance + transportation'),
        ('basic_house_transportation_phone', 'Basic salary + House + transportation + phone'),
        ('total', 'Total salary'),
    ], string='Deduction based on')
    deduction_type = fields.Selection([
        ('fixed', 'Fixed amount'),
        ('percentage', 'percentage'),
    ], string='Deduction type')
    deduction_value = fields.Float('Deduction value')
    minus_deduction = fields.Boolean('Accept minus deduction value', default=False)
    amount = fields.Float('Amount', compute='get_amount',store=True)
    note = fields.Html('Note')
    attachment_ids = fields.One2many('deductions.violations.attaches', 'source_id', 'Attachments')
    reverse_deduction_id = fields.Many2one('employee.deductions.violations', 'Reversed Deduction')
    source_deduction_id = fields.Many2one('employee.deductions.violations', 'Source deduction')
    deduction_reverse_reason = fields.Char('Deduction reverse reason')
    old_deduction_id = fields.Many2one('employee.deductions.violations')
    old_employee_deduction_ids = fields.One2many('employee.deductions.violations', 'old_deduction_id', 'Employee Old Deductions',
                                           compute='get_old_employee_deduction_ids')
    early_return_from_leave = fields.Many2one('effective.notice', 'Early Return from leave')
    late_return_from_leave = fields.Many2one('effective.notice', 'Late Return from leave')
    auto_deduction = fields.Boolean('Automatic deduction')

    #@api.one
    @api.constrains('amount', 'decision')
    def check_amount(self):
        for rec in self:
            if rec.amount == 0 and rec.decision in ['deduction', 'deduction_action']:
                decision_selection = {
                    'verbal': 'Verbal warning',
                    'letter': 'Send notification letter',
                    'deduction': 'Deduct from employee salary',
                    'deduction_action': 'Deduct from employee salary + other action'
                }
                raise ValidationError(_("Attention!! \n\
                    The deduction decision which you selected is  ( %s ). It is not logic that the deducted amount is Zero!" % decision_selection[self.decision]))




    @api.model
    def create(self, vals):

        res = super(EmployeeDeductionsViolations, self).create(vals)
        res.code = self.env['ir.sequence'].next_by_code(self._name)
        if self.env.context.get('return_from_leave', False):
            return_from_leave_id = self.env.context.get('return_from_leave', False)
            return_from_leave = self.env['effective.notice'].search([('id', '=', return_from_leave_id)])
            return_from_leave.hr_department_approval()
        return res



    @api.onchange('deduction_percentage')
    def onchange_deduction_percentage(self):
        for rec in self:
            rec.deduction_value = rec.deduction_percentage

    #@api.one
    @api.depends('employee_id')
    def get_old_employee_deduction_ids(self):
        for rec in self:
            rec.old_employee_deduction_ids = False
            domain = [['employee_id', '=', rec.employee_id.id], ['deduction_date', '<=', rec.deduction_date]]
            if not isinstance(rec.id, models.NewId):
                domain.append(['id', '!=', rec.id])
            old_deductions = rec.search(domain)
            rec.old_employee_deduction_ids = [d.id for d in old_deductions]


    #@api.one
    @api.constrains('deduction_value', 'minus_deduction')
    def check_minus_deduction(self):
        for rec in self:
            if rec.deduction_value < 0 and not rec.minus_deduction:
                raise ValidationError(_("Attention!!\n\
                Not allowed to create a deduction with a minus value, Minus value mean that you will give the employee a reward.\n\
                If you want to give this employee a special reward, Go to Rewards window.\n\
                But, If you want to reverse old deduction, you must open the old deduction transaction and click on (reverse Deduction button)."))

    #@api.one
    @api.constrains('deduction_date', 'adjusted_date')
    def check_dates(self):
        for rec in self:
            if rec.deduction_date < rec.adjusted_date:
                raise ValidationError(_("Data Error! \n\
                    The employee start to work at ( %s ), it is not logic to create a deduction before the hiring date!" % (self.adjusted_date)))

    #@api.one
    @api.depends('deduction_date')
    def get_month(self):
        for rec in self:
            month = rec.deduction_date.month #.split('-')[1]
            year = rec.deduction_date.year #.split('-')[0]
            rec.month = '%s - %s' % (rec.MONTHS_SELECTION[str(month)], str(year))

    #@api.multi
    def open_old_violations(self):
        return {
            'domain': [['employee_id', '=', self.employee_id.id], ['id', '!=', self.id]],
            'name': _('Employee deductions - violations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'employee.deductions.violations',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_employee_id': self.employee_id.id},
        }

    #@api.one
    @api.constrains('contract_id')
    def check_contract(self):
        for rec in self:
            if rec.deduction_type == 'percentage':
                if not rec.contract_id.id:
                    raise ValidationError(_("Calculation Error!! \n\
                    Your system is trying to calculate the deduction amount, unfortunately, your system could not find active contract for the selected employee."))

    #@api.one
    @api.depends('deduction_type', 'contract_id', 'deduction_value', 'deduction_based_on')
    def get_amount(self):
        for rec in self:
            rec.amount = 0
            if rec.deduction_type == 'fixed':
                rec.amount = rec.deduction_value
            if rec.deduction_type == 'percentage':
                based_on_value = 0
                if rec.deduction_based_on == 'basic':
                    based_on_value = rec.contract_id.basic_salary
                if rec.deduction_based_on == 'basic_house':
                    based_on_value = rec.contract_id.basic_salary + rec.contract_id.house_allowance_amount
                if rec.deduction_based_on == 'basic_house_transportation':
                    based_on_value = rec.contract_id.basic_salary + rec.contract_id.house_allowance_amount + rec.contract_id.transportation_allowance_amount
                if rec.deduction_based_on == 'basic_house_transportation_phone':
                    based_on_value = rec.contract_id.basic_salary + rec.contract_id.house_allowance_amount + rec.contract_id.transportation_allowance_amount + \
                                    rec.contract_id.phone_allowance_amount
                if rec.deduction_based_on == 'total':
                    based_on_value = rec.contract_id.total
                rec.amount = (based_on_value / 30) * (rec.deduction_value / 100)

    @api.onchange('deduction_type')
    def onchange_deduction_type(self):
        for rec in self:
            rec.deduction_value = False
        

    @api.onchange('deduction_based_on')
    def onchange_deduction_based_on(self):
        # self.deduction_value = False
        for rec in self:
            if rec.deduction_reason != 'violation':
                rec.deduction_type = False

    @api.onchange('deduction_reason', 'violation_type_id')
    def onchange_deduction_reason(self):
        for rec in self:
            if rec.deduction_reason == 'violation':
                rec.deduction_type = 'percentage'
                if rec.violation_type_id:
                    rec.deduction_based_on = rec.violation_type_id.deduction_based_on or False

    #@api.one
    @api.onchange('decision')
    def empty_data(self):
        pass
        # self.template_id = False
        # self.deduction_percentage = False
        # self.other_action = False
        # self.action_desc = False

    @api.onchange('decision', 'deduction_percentage', 'violation_type_id')
    def get_deduction_type(self):
        for rec in self:
            if rec.decision == 'violation':
                rec.deduction_type = rec.deduction_percentage

    @api.onchange('previous_violations', 'violation_type_id')
    def get_decision(self):
        for rec in self:
            rec.empty_data()
            rec.get_previous_violations()
            if rec.violation_type_id:
                times = rec.previous_violations + 1
                times = times <= 4 and str(times) or '4'
                rec.decision = getattr(rec.violation_type_id, 'deduction_type%s' % times)
                rec.template_id = getattr(rec.violation_type_id, 'template%s_id' % times)
                rec.deduction_percentage = getattr(rec.violation_type_id, 'deduction_percentage%s' % times)
                rec.other_action = getattr(rec.violation_type_id, 'other_action%s' % times)
                rec.action_desc = getattr(rec.violation_type_id, 'other_action_desc%s' % times)

    #@api.one
    @api.depends('violation_type_id', 'employee_id')
    def get_previous_violations(self):
        for rec in self:
            rec.previous_violations = len(rec.search([
                ['state', '=', 'confirmed'],
                ['employee_id', '=', rec.employee_id.id],
                ['violation_type_id', '=', rec.violation_type_id.id],
                ['reverse_deduction_id', '=', False],
                ['source_deduction_id', '=', False],
                ['deduction_reverse_reason', '=', False],
            ])) or 0.00

    @api.onchange('employee_id')
    def onchange_employee(self):
        for rec in self:
            if not rec.env.context.get('popup', False):
                rec.deduction_date = False
                rec.deduction_reason = False
                rec.deduction_value = False

    #@api.multi
    def open_confirm_other_action(self):
        ctx = {'deduction_violation_id': self.id, 'default_action': self.action_desc}
        return {
            'domain': [],
            'name': _('Attention'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'confirm.other.action',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }

    #@api.multi
    def confirm(self, confirm_other_action=False):
        for rec in self:
            previous_violations = len(rec.search([
                ['state', '=', 'confirmed'],
                ['employee_id', '=', rec.employee_id.id],
                ['violation_type_id', '=', rec.violation_type_id.id],
                ['reverse_deduction_id', '=', False],
                ['source_deduction_id', '=', False],
                ['deduction_reverse_reason', '=', False],
            ]))
            if previous_violations != rec.previous_violations:
                raise ValidationError(_("Attention!! \n\
                When you created this deduction, the previous violation was (%s) .. when you confirm this deduction, we found that the previous violation is (%s)\
                which means that the deduction value may vary due to increasing / decreasing the number of previous violation \n\
                To solve this point. you must change the violation which you selected at Violation Type and re-select it again." % (
                    rec.previous_violations, previous_violations)))
            if rec.decision == 'letter' and not rec.reverse_deduction_id.id and not rec.employee_id.work_email:
                raise ValidationError(_("Your system could not find E-mail address for the employee which you selected. Kindly go to Employee window and write the \
                employee email at Work Email field."))
            if rec.decision == 'deduction_action' and rec.other_action == 'other':
                if not (isinstance(confirm_other_action, bool) and confirm_other_action):
                    return rec.open_confirm_other_action()
            rec.state = 'confirmed'

    #@api.one
    def review(self):
        for rec in self:
            rec.state = 'reviewed'

    #@api.one
    @api.constrains('contract_id')
    def check_contract(self):
        for rec in self:
            if not rec.contract_id.id:
                raise ValidationError(_("There is no active contract for this employee!!"))

    #@api.one
    def unlink(self):
        for rec in self:
            if rec.auto_deduction:
                raise ValidationError(_("Not allowed to delete a record which is automatically created by the system, try to refuse or set to new."))
        return super(EmployeeDeductionsViolations, self).unlink()


class DeductionTypeAttaches(models.Model):
    _name = "deduction.type.attaches"
    _description = "DeductionType Attaches"

    type_id = fields.Many2one('deduction.violation.type', 'deduction violation type')
    file = fields.Binary('File')
    name = fields.Char('Description')
    note = fields.Char('Notes')


class DeductionViolationAttaches(models.Model):
    _name = "deductions.violations.attaches"
    _description = "deductions violations Attaches"

    source_id = fields.Many2one('employee.deductions.violations', 'Employee deductions - violations')
    file = fields.Binary('File')
    name = fields.Char('Description')
    note = fields.Char('Notes')


class ConfirmOtherAction(models.TransientModel):
    _name = "confirm.other.action"

    action = fields.Char(string='Other action')

    #@api.multi
    def confirm(self):
        deduction_violation_id = self._context.get('deduction_violation_id', False)
        self.env['employee.deductions.violations'].browse(deduction_violation_id).confirm(confirm_other_action=True)


class Contract(models.Model):
    _inherit = "hr.contract"

    deduction_violation_ids = fields.One2many('employee.deductions.violations', 'contract_id', 'Old deductions - Violations', domain=[['state', '=', 'confirmed']])
    total_deduction_amount = fields.Float('Total deduction amount', compute='get_total_deduction_amount')
    total_deduction_amount_ = fields.Float('Total deduction amount', related='total_deduction_amount')
    paid_amount_ids = fields.One2many('contract.paid.violation', 'contract_id', 'Paid amounts')
    total_paid_amount = fields.Float('Total paid amount', compute='get_total_paid_amount')
    total_paid_amount_ = fields.Float('Total paid amount', related='total_paid_amount')
    remaining = fields.Float('Remaining', compute='get_remaining')

    #@api.one
    @api.depends('total_deduction_amount', 'total_paid_amount')
    def get_remaining(self):
        for rec in self:
            rec.remaining = round(rec.total_deduction_amount, 2) - round(rec.total_paid_amount, 2)

    #@api.one
    @api.depends('deduction_violation_ids')
    def get_total_deduction_amount(self):
        for rec in self:
            rec.total_deduction_amount = round(sum([l.amount for l in rec.deduction_violation_ids]), 2)

    #@api.one
    @api.depends('paid_amount_ids')
    def get_total_paid_amount(self):
        for rec in self:
            rec.total_paid_amount = round(sum([float(l.amount) for l in rec.paid_amount_ids]), 2)


class ContractPaidViolation(models.Model):
    _name = "contract.paid.violation"

    contract_id = fields.Many2one('hr.contract', 'Contract')
    # reference_id = fields.Many2one('hr.payslip', 'Payment reference')
    date = fields.Char('Payment date')
    amount = fields.Float('Payment amount')
    note = fields.Char('Notes')


class Payroll(models.Model):
    _inherit = "hr.payslip"

    total_deduction = fields.Float('Total deductions', compute='get_total_deduction')
    total_deduction_ = fields.Float('Total deductions')
    total_paid = fields.Float('Total paid', compute='get_total_paid')
    total_paid_ = fields.Float('Total paid')
    remaining = fields.Float('Remaining', compute='get_remaining')
    remaining_ = fields.Float('Remaining')
    remaining_deduction = fields.Float('Remaining Violations', compute="_compute_remaining_deduction")
    deduct_this_month_ = fields.Float('Deduct this month')
    remove_from_employee = fields.Float('Remove this amount from employee')
    next_month_balance = fields.Float('Next Month balance', compute='get_next_month_balance')
    next_month_balance_history = fields.Float('Next Month balance')

    #@api.one
    def _compute_remaining_deduction(self):
        for rec in self:
            if rec.state == 'done':
                rec.remaining_deduction = rec.remaining_
            else:
                rec.remaining_deduction = rec.remaining

    @api.constrains('remove_from_employee')
    def check_remove_from_employee(self):
        for rec in self:
            if rec.remove_from_employee < 0:
                raise ValidationError(_("Remove this amount from employee can not be less than zero"))

    #@api.one
    @api.depends('remaining', 'remove_from_employee', 'deduct_this_month_')
    def get_next_month_balance(self):
        for rec in self:
            rec.next_month_balance = rec.remaining - rec.remove_from_employee - rec.deduct_this_month_

    #@api.one
    @api.constrains('deduct_this_month_')
    def check_deduct_this_month_(self):
        for rec in self:
            if rec.deduct_this_month_ < 0:
                raise ValidationError(_("Deduct this month can not be lees than zero"))

    #@api.one
    @api.depends('total_deduction', 'total_paid')
    def get_remaining(self):
        for rec in self:
            rec.remaining = rec.total_deduction - rec.total_paid
            if rec.remaining == 0:
                rec.remove_from_employee = 0

    #@api.one
    @api.depends('contract_id')
    def get_total_deduction(self):
        for rec in self:
            rec.total_deduction = rec.total_deduction_ or rec.contract_id.total_deduction_amount

    #@api.one
    @api.depends('contract_id')
    def get_total_paid(self):
        for rec in self:
            rec.total_paid = rec.total_paid_ or rec.contract_id.total_paid_amount

    #@api.one
    #need mig
    # def hr_verify_sheet(self):
    #     if self.remaining and not self.loans_data_reviewed:
    #         raise ValidationError(_("Attention!! \n\
    #         This employee  ( %s  ) had old loans or deductions or rewards which is not fully paid before confirm this payslip. kindly go to ( other payment /\
    #          deduction) tab,  and make sure that you checked (other payments / deduction reviewed).") % (self.employee_id.name))
    #     if self.next_month_balance < 0:
    #         raise ValidationError(_("Validation Error!\n\
    #             It seems that you deducted an amount bigger than the employee deduction balance. kindly review your data.\nEmployee: %s" % self.employee_id.display_name))
    #     self.total_deduction_ = self.total_deduction
    #     self.total_paid_ = self.total_paid
    #     self.remaining_ = self.remaining
    #     self.next_month_balance_history = self.next_month_balance
    #     if self.deduct_this_month_:
    #         self.env['contract.paid.violation'].create({
    #             'contract_id': self.contract_id.id,
    #             'reference_id': self.id,
    #             'date': self.date_to,
    #             'amount': self.deduct_this_month_,
    #         })
    #     if self.remove_from_employee:
    #         self.env['contract.paid.violation'].create({
    #             'contract_id': self.contract_id.id,
    #             'reference_id': self.id,
    #             'date': self.date_to,
    #             'amount': self.remove_from_employee,
    #         })
    #     return super(Payroll, self).hr_verify_sheet()

    @api.model
    def loan_deduction_rule(self):
        loan_installments = self.env['loan.installment'].search([
            ('employee_id','=',self.employee_id.id),
            ('deduction_date','>=',self.date_from),
            ('deduction_date','<=',self.date_to),
            ('state','=','Loan Fully Paid'),
            ('loan_request_id.type','=','Loan')])

        monthly_installment = sum([inst.monthly_installment for inst in loan_installments])
        # return self.deduct_this_month * -1
        return monthly_installment * -1

    @api.model
    def salary_advance_deduction_rule(self):
        advance_installments = self.env['loan.advance.request'].search([
            ('employee_id','=',self.employee_id.id),
            ('expected_payment','>=',self.date_from),
            ('expected_payment','<=',self.date_to),
            ('state','=','Loan Fully Paid'),
            ('type','=','Salary In Advance')])

        monthly_installment = sum([inst.loan_amount for inst in advance_installments])
        # return self.deduct_this_month * -1
        return monthly_installment * -1

    @api.model
    def violation_deduction_rule(self):
        return self.deduct_this_month_ * -1

    @api.model
    def rewards_rule(self):
        return self.reward_pay_this_month

    @api.model
    def total_deductions(self):
        res = super(Payroll, self).total_deductions()
        return res + self.loan_deduction_rule() + self.violation_deduction_rule() + self.rewards_rule()


class Employee(models.Model):
    _inherit = "hr.employee"

    deductions_count = fields.Float('Deduction count', compute='get_deductions_count')

    #@api.one
    def get_deductions_count(self):
        for rec in self:
            contracts = rec.env['hr.contract'].search([('employee_id', '=', rec.id), ('active', '=', True)])
            if len(contracts):
                contract = contracts[0]
                rec.deductions_count = contract.remaining
            else:
                rec.deductions_count = 0

    #@api.multi
    def open_deductions(self):
        return {
            'domain': [['employee_id', '=', self.id]],
            'name': _('Employee deductions - violations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'employee.deductions.violations',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_employee_id': self.id},
        }
