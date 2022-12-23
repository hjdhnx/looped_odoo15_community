# -*- coding: utf-8 -*-

from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import time
import calendar
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)


# _logger.info(error_msg)


class hrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.constrains('month', 'employee_id', 'date_from', 'date_to', 'year')
    def check_old_payroll(self):
        """
        prevent payroll if employee have old payroll with same month and year
        """
        for rec in self:
            count = rec.search_count(
                [('employee_id', '=', rec.employee_id.id), ('month', '=', rec.month), ('year', '=', rec.year)])

            if count > 1:
                raise ValidationError(_('Sorry you Have old Payroll with same Month!!'))

    @api.onchange('employee_id')
    def oncahnge_employee_set_contract(self):
        for rec in self:
            if rec.employee_id and rec.employee_id.contract_id:
                rec.contract_id = rec.employee_id.contract_id
                rec.struct_id = rec.contract_id.structure_type_id.default_struct_id.id
                rec._onchange_employee()
            else:
                rec.contract_id = False
                rec.struct_id = False

    def action_payslip_done(self):
        """
            Generate the accounting entries related to the selected payslips
            A move is created for each journal and for each month.
        """
        res = super(hrPayslip, self).action_payslip_done()
        # for rec in self:
        #     rec._action_create_account_move()
        # for rec in self:
        #     print(".>>>>>>>>>>>>>>>>>>>>>>>",rec.employee_id.name,rec.move_id)

        # # 1/0
        return res

    def action_payslip_draft(self):
        res = super(hrPayslip, self).action_payslip_draft()
        for rec in self:
            rec.line_ids.unlink()
        return res

    def action_payslip_cancel(self):
        """
        Override cancel
        """
        moves = self.mapped('move_id')
        moves.button_cancel()
        # moves.unlink()
        self.write({'state': 'cancel'})
        self.mapped('payslip_run_id').action_close()
        # return super(hrPayslip, self).action_payslip_cancel()

    # def action_payslip_done(self):
    #     for rec in self:
    #         super(hrPayslip,rec).action_payslip_done()
    #     for rec in self:
    #         print(".>>>>>>>>>>>>>>>>>>>>>>>",rec.employee_id.name,rec.move_id)

    #     1/0

    # return res


class hr_payslip_run(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run', 'mail.thread']
    _order = "id desc"

    def action_validate_create_entry(self):
        for rec in self:
            rec.action_validate()
            # rec.slip_ids.compute_sheet()
            # rec.slip_ids.action_payslip_done()

            # return

    def action_validate(self):

        for rec in self:
            if any(not payslip.struct_id for payslip in rec.slip_ids):
                raise ValidationError(_('One of the contract for these payslips has no structure type.'))
            if any(not structure.journal_id for structure in rec.slip_ids.mapped('struct_id')):
                raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

        res = super(hr_payslip_run, self).action_validate()

        return res

    # def action_draft(self):
    #     for rec in self:
    #         rec.slip_ids.action_payslip_cancel()
    #         rec.slip_ids.unlink()
    #         rec.state = 'draft'
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
    count_payslips = fields.Integer('Count payslips', compute='_compute_count_payslips')
    attachment_ids = fields.One2many('hr.payslip.run.attaches', 'batch_id', 'Attachments')

    # //////////////////////// Rules Fields ////////////////////////////////////////////////////////////////
    rule_basic = fields.Float('Total Basic Salary', compute='_compute_rules_fields')
    rule_house_allowance = fields.Float('Total House Allowance', compute='_compute_rules_fields')
    rule_transportation_allowance = fields.Float('Total Transportation Allowance', compute='_compute_rules_fields')
    rule_phone_allowance = fields.Float('Total Phone Allowance', compute='_compute_rules_fields')
    rule_other_llowance = fields.Float('Total Other Allowance', compute='_compute_rules_fields')
    rule_gross = fields.Float('Total Gross', compute='_compute_rules_fields')
    rule_loan_deducted = fields.Float('Total Loan Deducted', compute='_compute_rules_fields')
    rule_deductions_violations = fields.Float('Total Deductions / Violations', compute='_compute_rules_fields')
    rule_employee_rewards = fields.Float('Total Employee Rewards', compute='_compute_rules_fields')
    rule_gosi_employee_share = fields.Float('Total Gosi Employee share', compute='_compute_rules_fields')
    rule_total_deductions = fields.Float('Total Total deductions', compute='_compute_rules_fields')
    rule_net = fields.Float('Total Net', compute='_compute_rules_fields')
    rule_gosi_company_share = fields.Float('Total Gosi Company share', compute='_compute_rules_fields')
    reviewed_by = fields.Many2one('res.users', 'Reviewed By')
    reviewed_date = fields.Date('Reviewed Date')
    final_reviewed_by = fields.Many2one('res.users', 'Final Review By')
    final_reviewed_date = fields.Date('Final Review Date')
    confirmed_by = fields.Many2one('res.users', 'Confirmed By')
    confirmation_date = fields.Date('Confirmation Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('Reviewed', 'Reviewed'),
        ('verify', 'Verify'),
        ('Final Reviewed', 'Final Reviewed'),
        ('done', 'Done'),
        ('close', 'Close'),
        ('paid', 'Paid'),

    ], 'Status', select=True, readonly=True, copy=False)
    note = fields.Html('Notes')

    date_start = fields.Date(string='Date From', required=True, readonly=True,
                             states={'draft': [('readonly', False)]},
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_end = fields.Date(string='Date To', required=True, readonly=True,
                           states={'draft': [('readonly', False)]},
                           default=lambda self: fields.Date.to_string(
                               (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))

    # @api.one
    @api.depends('slip_ids')
    def _compute_rules_fields(self):
        rule_basic = 0
        rule_house_allowance = 0
        rule_transportation_allowance = 0
        rule_phone_allowance = 0
        rule_other_llowance = 0
        rule_gross = 0
        rule_loan_deducted = 0
        rule_deductions_violations = 0
        rule_employee_rewards = 0
        rule_gosi_employee_share = 0
        rule_total_deductions = 0
        rule_net = 0
        rule_gosi_company_share = 0
        for line in self.slip_ids:
            rule_basic += line.rule_basic
            rule_house_allowance += line.rule_house_allowance
            rule_transportation_allowance += line.rule_transportation_allowance
            rule_phone_allowance += line.rule_phone_allowance
            rule_other_llowance += line.rule_other_llowance
            rule_gross += line.rule_gross
            rule_loan_deducted += line.rule_loan_deducted
            rule_deductions_violations += line.rule_deductions_violations
            rule_employee_rewards += line.rule_employee_rewards
            rule_gosi_employee_share += line.rule_gosi_employee_share
            rule_total_deductions += line.rule_total_deductions
            rule_net += line.rule_net
            rule_gosi_company_share += line.rule_gosi_company_share

        self.rule_basic = rule_basic
        self.rule_house_allowance = rule_house_allowance
        self.rule_transportation_allowance = rule_transportation_allowance
        self.rule_phone_allowance = rule_phone_allowance
        self.rule_other_llowance = rule_other_llowance
        self.rule_gross = rule_gross
        self.rule_loan_deducted = rule_loan_deducted
        self.rule_deductions_violations = rule_deductions_violations
        self.rule_employee_rewards = rule_employee_rewards
        self.rule_gosi_employee_share = rule_gosi_employee_share
        self.rule_total_deductions = rule_total_deductions
        self.rule_net = rule_net
        self.rule_gosi_company_share = rule_gosi_company_share

    # @api.one
    def _compute_count_payslips(self):
        self.count_payslips = len(self.slip_ids)

    # @api.one
    def review_payslip_run(self):
        if self.slip_ids:
            for slip in self.slip_ids:
                if slip.state == 'draft':
                    slip.signal_workflow('review_payslip')
        else:
            raise UserError(_(
                "Not allowed !! \n There is no payslips found! What is the data which you reviewed? kindly go to Payslip tab and click on Generate payslips, then select all employees which you want to create Payslip for them. "))
        self.write(
            {'state': 'Reviewed', 'reviewed_by': self.env.uid, 'reviewed_date': datetime.now().strftime('%Y-%m-%d')})
        body = "Document Reviewed"
        self.message_post(body=body, message_type='email')
        return {}

    # @api.one
    def final_review_payslip_run(self):
        if self.slip_ids:
            for slip in self.slip_ids:
                if slip.state == 'draft':
                    slip.signal_workflow('review_payslip')
                    slip.signal_workflow('final_review_payslip')
                if slip.state == 'Reviewed':
                    slip.signal_workflow('final_review_payslip')
        else:
            raise UserError(_(
                "Not allowed !! \n There is no payslips found! What is the data which you reviewed? kindly go to Payslip tab and click on Generate payslips, then select all employees which you want to create Payslip for them. "))

        self.write({'state': 'Final Reviewed', 'final_reviewed_by': self.env.uid,
                    'final_reviewed_date': datetime.now().strftime('%Y-%m-%d')})
        body = "Document Final Reviewed"
        self.message_post(body=body, message_type='email')
        return {}

    # @api.one
    def confirm_payslip_run(self):
        if self.slip_ids:
            for slip in self.slip_ids:
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

        self.write(
            {'state': 'done', 'confirmed_by': self.env.uid, 'confirmation_date': datetime.now().strftime('%Y-%m-%d')})
        body = "Document Confirmed"
        self.message_post(body=body, message_type='email')
        return {}

    # @api.one
    def set_draft_payslip_run(self):
        if self.slip_ids:
            for slip in self.slip_ids:
                if slip.state in ['Reviewed', 'Final Reviewed', 'cancel']:
                    slip.signal_workflow('draft')
        else:
            raise UserError(_("Not allowed !! \n There is no payslips in order to set it to Draft. "))

        self.write({'state': 'draft'})
        body = "Document Set To Draft"
        self.message_post(body=body, message_type='email')
        return {}

    # @api.multi
    def open_payslips(self):
        return {
            'domain': [('id', 'in', self.slip_ids.ids)],
            'name': _('Employee payslip'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.onchange('month', 'year')
    def onchange_period(self):
        if self.month and self.year:
            start_end = calendar.monthrange(self.year, int(self.month))
            self.date_start = str(self.year) + '-' + self.month + '-01'
            self.date_end = str(self.year) + '-' + self.month + '-' + str(start_end[1])


class BatchAttaches(models.Model):
    _name = "hr.payslip.run.attaches"
    _description = "Payslip Batch Attaches"

    batch_id = fields.Many2one('hr.payslip.run', 'Batch')
    file = fields.Binary('File')
    name = fields.Char('Description')
    note = fields.Char('Notes')


class hr_payslip_employees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def _get_employees(self):
        # YTI check dates too
        return self.env['hr.employee'].search(self._get_available_contracts_domain())
        # return self.env['hr.employee'].search([('id','in',[2,3])])

    def compute_sheet(self):
        emp_pool = self.env['hr.employee']
        slip_pool = self.env['hr.payslip']
        run_pool = self.env['hr.payslip.run']
        slip_ids = []

        context = self._context
        data = self.read()[0]
        run_data = data  # {}
        payslip_run = False
        # print(">>>>>>>>>>>>>>>>Self.read00data ",context)
        if context and context.get('active_id', False):
            payslip_run = run_pool.browse(context.get('active_id', False))
            run_data = payslip_run.read(['date_start', 'date_end', 'credit_note', 'month', 'year'])[0]
        # print(">>>>>>>>>>>>>>>>Self.read",run_data)

        from_date = run_data.get('date_start', False)
        to_date = run_data.get('date_end', False)
        credit_note = run_data.get('credit_note', False)
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for emp in emp_pool.browse(data['employee_ids']):
            # slip_data = slip_pool.onchange_employee_id(cr, uid, [], from_date, to_date, emp.id, contract_id=False, context=context)
            res = {
                'employee_id': emp.id,
                'name': "Payslip",  # slip_data['value'].get('name', False),
                'month': run_data.get('month', False),
                'year': run_data.get('year', False),
                # 'struct_id': slip_data['value'].get('struct_id', False),
                # 'contract_id': slip_data['value'].get('contract_id', False),
                'contract_id': emp.contract_id.id if emp.contract_id else False,
                'payslip_run_id': context.get('active_id', False),
                # 'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', False)],
                # 'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', False)],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': credit_note,
            }
            slip_rec = slip_pool.create(res)
            slip_rec._onchange_employee()
            slip_rec.compute_sheet()
            slip_ids.append(slip_rec)

        payslip_run.state = 'verify'

        # slip_pool.compute_sheet(slip_ids)
        return {'type': 'ir.actions.act_window_close'}


class hr_payslip(models.Model):
    _inherit = "hr.payslip"
    # _name = "hr.payslip"
    # _inherit = ['mail.thread']
    # _inherit = ["hr.payslip", 'mail.thread']
    _order = "id desc"

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

    total_loans = fields.Float('Total Loans', readonly=True)
    current_total_loans = fields.Float('Total Loans', readonly=True)

    total_paid_amount = fields.Float('Total paid', readonly=True)
    current_total_paid_amount = fields.Float('Total paid', readonly=True)

    remaining_amount = fields.Float('Remaining Amount', readonly=True)
    current_remaining_amount = fields.Float('Remaining Amount', readonly=True)

    deduct_this_month = fields.Float('Deduct this Month')
    loans_data_reviewed = fields.Boolean('Other payments / Deduction reviewed')
    in_trial_period = fields.Boolean('In trail period', compute='in_trial_period_')
    number_of_days = fields.Integer('Number of days', compute='_compute_number_of_days')
    excluded_days_old = fields.Integer('Excluded days due to old payslip', compute='_compute_excluded_days_old')
    excluded_days_leaves = fields.Integer('Excluded days due to Leaves', compute='_compute_excluded_days_leaves')
    total_excluded_days = fields.Integer('Total days Excluded', compute='_compute_total_excluded_days')
    days_in_payslip = fields.Integer('Days included in payslip', compute='_compute_number_of_days')
    employee_english_name = fields.Char("Employee English Name", related="employee_id.employee_english_name")
    reviewed_by = fields.Many2one('res.users', 'Reviewed By')
    reviewed_date = fields.Date('Reviewed Date')
    final_reviewed_by = fields.Many2one('res.users', 'Final Review By')
    final_reviewed_date = fields.Date('Final Review Date')
    confirmed_by = fields.Many2one('res.users', 'Confirmed By')
    confirmation_date = fields.Date('Confirmation Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('Reviewed', 'Reviewed'),
        ('Final Reviewed', 'Final Reviewed'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], 'Status', select=True, readonly=True, copy=False,
        help='* When the payslip is created the status is \'Draft\'.\
            \n* If the payslip is under verification, the status is \'Waiting\'. \
            \n* If the payslip is confirmed then status is set to \'Done\'.\
            \n* When user cancel payslip the status is \'Rejected\'.')

    # //////////////////////// Rules Fields ////////////////////////////////////////////////////////////////
    rule_basic = fields.Float('Basic Salary')
    rule_house_allowance = fields.Float('House Allowance')
    rule_transportation_allowance = fields.Float('Transportation Allowance')
    rule_phone_allowance = fields.Float('Phone Allowance')
    rule_other_llowance = fields.Float('Other Allowance')
    rule_gross = fields.Float('Gross')
    rule_loan_deducted = fields.Float('Loan Deducted')
    rule_deductions_violations = fields.Float('Deductions / Violations')
    rule_employee_rewards = fields.Float('Employee Rewards')
    rule_absence_deducted = fields.Float('Absence Deductions')
    rule_gosi_employee_share = fields.Float('Gosi Employee share')
    rule_total_deductions = fields.Float('Total deductions')
    rule_net = fields.Float('Net')
    rule_gosi_company_share = fields.Float('Gosi Company share')
    # branch_id = fields.Many2one('hr.branch', 'Branch', related="employee_id.branch_id", store=True)
    department_id = fields.Many2one('hr.department', 'Department', related="employee_id.department_id", store=True)

    # /////////////////// Smart Buttons /////////////////////////////////////////////////////////////
    count_old_payslips = fields.Float('Employee Old payslips', compute='get_count_old_payslips')

    # @api.one
    def get_count_old_payslips(self):
        self.count_old_payslips = self.env['hr.payslip'].search_count(
            [('employee_id', '=', self.employee_id.id), ('id', '!=', self.id)])

    # @api.multi
    def open_old_payslips(self):
        return {
            'domain': [('employee_id', '=', self.employee_id.id), ('id', '!=', self.id)],
            'name': _('Employee Old payslips'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {}
        }

    # ///////////////////////////////////////////////////////////////////////////////////////////////////

    # @api.one
    def review_payslip(self):
        self.compute_sheet()
        self.write(
            {'state': 'Reviewed', 'reviewed_by': self.env.uid, 'reviewed_date': datetime.now().strftime('%Y-%m-%d')})
        body = "Document Reviewed"
        self.message_post(body=body, message_type='email')
        return {}

    # @api.one
    def final_review_payslip(self):
        self.compute_sheet()
        self.write({'state': 'Final Reviewed', 'final_reviewed_by': self.env.uid,
                    'final_reviewed_date': datetime.now().strftime('%Y-%m-%d')})
        body = "Document Final Reviewed"
        self.message_post(body=body, message_type='email')
        return {}

    # @api.one
    def _compute_rules_fields(self):
        for line in self.line_ids:
            if line.code == 'BSC':
                self.rule_basic = line.total
            if line.code == 'HOUSEALL':
                self.rule_house_allowance = line.total
            if line.code == 'TRANSALL':
                self.rule_transportation_allowance = line.total
            if line.code == 'PHOALL':
                self.rule_phone_allowance = line.total
            if line.code == 'OTHERALL':
                self.rule_other_llowance = line.total
            if line.code == 'GROSS':
                self.rule_gross = line.total
            if line.code == 'LOAN':
                self.rule_loan_deducted = line.total
            if line.code == 'DEDUCT':
                self.rule_deductions_violations = line.total
            if line.code == 'REWARD':
                self.rule_employee_rewards = line.total
            if line.code == 'ABSENCE':
                self.rule_absence_deducted = line.total
            if line.code == 'GOSIE':
                self.rule_gosi_employee_share = line.total
            if line.code == 'DED':
                self.rule_total_deductions = line.total
            if line.code == 'NET_RULE':
                self.rule_net = line.total
            if line.code == 'GOSIC':
                self.rule_gosi_company_share = line.total

    # //////////////////////////////////////////////////////////////////////////////////////////////////////

    @api.constrains('deduct_this_month')
    def check_deduct_this_month(self):
        if self.deduct_this_month < 0:
            raise ValidationError('Deduct this month from Loans should be more than zero')

    @api.onchange('month', 'year')
    def onchange_period(self):
        if self.month and self.year:
            start_end = calendar.monthrange(self.year, int(self.month))
            self.date_from = str(self.year) + '-' + self.month + '-01'
            self.date_to = str(self.year) + '-' + self.month + '-' + str(start_end[1])

            # @api.one
            # @api.constrains('date_from', 'date_to')
            # def _check_period(self):
            # counter = self.search_count([['id', '!=', self.id],
            #                              ['employee_id', '=', self.employee_id.id],
            #                              ['date_from', '<=', self.date_from],
            #                              ['date_to', '>=', self.date_from]])
            # if counter:
            #     raise UserError(_('Configuration Error!\n'
            #                       'We found that there is another payslip for the same employee in the same period.'))

    @api.model
    def create(self, vals):
        return super(hr_payslip, self).create(vals)

    # @api.multi
    def compute_sheet(self):
        for rec in self:
            rec.check_old_payslips()
        res = super(hr_payslip, self).compute_sheet()

        ref = self.env.ref

        rules_to_update_rate = [
            'ext_hr_payroll.basic_salary_rule',
            'ext_hr_payroll.house_salary_rule',
            'ext_hr_payroll.transportation_salary_rule',
            'ext_hr_payroll.phone_salary_rule',
            'ext_hr_payroll.other_salary_rule',
            'hr_gosi.hr_rule_gosi_company',
            'hr_gosi.hr_rule_gosi_employee',
            'asc_hr.Food_salary_rule',
            'asc_hr.work_salary_rule',
        ]
        rules_to_update_rate_ids = [ref(rule).id for rule in rules_to_update_rate if ref(rule, False)]

        for rec in self:
            rate = float(rec.days_in_payslip) / 30.00 * 100.00
            for line in rec.line_ids:
                if line.salary_rule_id.id in rules_to_update_rate_ids:
                    line.rate = rate

        for rec in self:
            rec._compute_rules_fields()
            # prevent deduction to be more than percentage
        #     rec.check_max_deduction()
        # # 1/0

        return res

    # @api.one
    @api.depends('date_from', 'date_to', 'excluded_days_old', 'excluded_days_leaves', 'month')
    def _compute_number_of_days(self):
        for rec in self:
            start_date = rec.date_from
            end_date = rec.date_to
            duration = relativedelta(end_date, start_date)
            end_month = int(end_date.strftime("%m"))
            end_year = int(end_date.strftime("%Y"))
            n = calendar.monthrange(end_year, end_month)[1]
            # if duration.days + 1 == n:
            #     duration_days = 29
            # else:
            duration_days = duration.days
            number_of_days = (duration.years * 12 + duration.months) * 30 + duration_days + 1
            rec.number_of_days = duration_days + 1  # number_of_days
            rec.days_in_payslip = rec.number_of_days - rec.total_excluded_days

    # @api.one
    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_excluded_days_old(self):
        for rec in self:
            rec.excluded_days_old = 0
            if rec.employee_id and rec.date_from and rec.date_to:
                if rec.id:
                    domain = [
                        ('date_from', '<=', rec.date_to),
                        ('date_to', '>=', rec.date_from),
                        ('employee_id', '=', rec.employee_id.id),
                        ('id', '!=', rec.id),
                        ('state', '=', 'done'),
                    ]
                else:
                    domain = [
                        ('date_from', '<=', rec.date_to),
                        ('date_to', '>=', rec.date_from),
                        ('employee_id', '=', rec.employee_id.id),
                        ('state', '=', 'done'),
                    ]
                old_payslips = rec.search(domain)
                conflicts = []
                intersections = []
                for old_payslip in old_payslips:
                    vals = {'start': old_payslip.date_from, 'end': old_payslip.date_to}
                    conflicts.append(vals)

                for conflict in conflicts:
                    if conflict['start'] > rec.date_from:
                        intersection_start = conflict['start']
                    else:
                        intersection_start = rec.date_from
                    if conflict['end'] < rec.date_to:
                        intersection_end = conflict['end']
                    else:
                        intersection_end = rec.date_to
                    is_merged = False
                    for intersection in intersections:
                        if intersection['start'] <= intersection_end and intersection['end'] >= intersection_start:
                            if intersection['start'] > intersection_start:
                                intersection['start'] = intersection_start
                            if intersection['end'] < intersection_end:
                                intersection['end'] = intersection_end
                            is_merged = True
                    if not is_merged:
                        intersections.append({'start': intersection_start, 'end': intersection_end})

                excluded_old_count = 0
                for intersection in intersections:
                    start_date = intersection['start']
                    end_date = intersection['end']
                    # /////////////////////////////////////////////////////////////////////////////////////
                    duration = relativedelta(end_date, start_date)
                    if duration.days == 30:
                        duration_days = 29
                    else:
                        duration_days = duration.days
                    number_of_days = (duration.years * 12 + duration.months) * 30 + duration_days + 1
                    # /////////////////////////////////////////////////////////////////////////////////////
                    excluded_old_count += number_of_days
                rec.excluded_days_old = excluded_old_count

    # @api.one
    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_excluded_days_leaves(self):
        for rec in self:
            rec.excluded_days_leaves = 0
            if rec.employee_id and rec.date_from and rec.date_to:
                domain = [
                    ('date_from', '<=', rec.date_to),
                    ('date_to', '>=', rec.date_from),
                    ('employee_id', '=', rec.employee_id.id),
                    # ('type', '=', 'remove'),
                    ('state', '=', 'validate'),
                ]
                old_leaves = rec.env['hr.leave'].search(domain)
                conflicts = []
                intersections = []
                for old_leave in old_leaves:
                    if old_leave.holiday_status_id.reconciliation_method == 'Stop payslip during leave and use leave reconciliation':
                        start_datetime = datetime.strptime(old_leave.date_from, "%Y-%m-%d %H:%M:%S")
                        start_date = start_datetime.strftime('%Y-%m-%d')
                        end_datetime = datetime.strptime(old_leave.date_to, "%Y-%m-%d %H:%M:%S")
                        end_date = end_datetime.strftime('%Y-%m-%d')
                        vals = {'start': start_date, 'end': end_date}
                        conflicts.append(vals)

                for conflict in conflicts:
                    if conflict['start'] > rec.date_from:
                        intersection_start = conflict['start']
                    else:
                        intersection_start = rec.date_from
                    if conflict['end'] < rec.date_to:
                        intersection_end = conflict['end']
                    else:
                        intersection_end = rec.date_to
                    is_merged = False
                    for intersection in intersections:
                        if intersection['start'] <= intersection_end and intersection['end'] >= intersection_start:
                            if intersection['start'] > intersection_start:
                                intersection['start'] = intersection_start
                            if intersection['end'] < intersection_end:
                                intersection['end'] = intersection_end
                            is_merged = True
                    if not is_merged:
                        intersections.append({'start': intersection_start, 'end': intersection_end})
                excluded_leaves_count = 0
                for intersection in intersections:
                    start_date = intersection['start']
                    end_date = intersection['end']
                    # /////////////////////////////////////////////////////////////////////////////////////
                    duration = relativedelta(end_date, start_date)
                    if duration.days == 30:
                        duration_days = 29
                    else:
                        duration_days = duration.days
                    number_of_days = (duration.years * 12 + duration.months) * 30 + duration_days + 1
                    # /////////////////////////////////////////////////////////////////////////////////////
                    excluded_leaves_count += number_of_days
                rec.excluded_days_leaves = excluded_leaves_count

    # @api.one
    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_total_excluded_days(self):
        for rec in self:
            rec.total_excluded_days = 0
            if rec.employee_id and rec.date_from and rec.date_to:
                if rec.id:
                    domain = [
                        ('date_from', '<=', rec.date_to),
                        ('date_to', '>=', rec.date_from),
                        ('employee_id', '=', rec.employee_id.id),
                        ('id', '!=', rec.id),
                        ('state', '=', 'done'),
                    ]
                else:
                    domain = [
                        ('date_from', '<=', rec.date_to),
                        ('date_to', '>=', rec.date_from),
                        ('employee_id', '=', rec.employee_id.id),
                        ('state', '=', 'done'),
                    ]
                old_payslips = rec.search(domain)
                # ////////////////////////////////////////////////////////////////////////////
                leaves_domain = [
                    ('date_from', '<=', rec.date_to),
                    ('date_to', '>=', rec.date_from),
                    ('employee_id', '=', rec.employee_id.id),
                    # ('type', '=', 'remove'),
                    ('state', '=', 'validate'),
                ]
                old_leaves = rec.env['hr.leave'].search(leaves_domain)
                # //////////////////////////////////////////////////////////////////////////////////
                conflicts = []
                intersections = []
                # /////////////////////////////////////////////////////////////////////////////////
                for old_payslip in old_payslips:
                    vals = {'start': old_payslip.date_from, 'end': old_payslip.date_to}
                    conflicts.append(vals)
                # /////////////////////////////////////////////////////////////////////////////////
                for old_leave in old_leaves:
                    if old_leave.holiday_status_id.reconciliation_method == 'Stop payslip during leave and use leave reconciliation':
                        start_datetime = datetime.strptime(old_leave.date_from, "%Y-%m-%d %H:%M:%S")
                        start_date = start_datetime.strftime('%Y-%m-%d')
                        end_datetime = datetime.strptime(old_leave.date_to, "%Y-%m-%d %H:%M:%S")
                        end_date = end_datetime.strftime('%Y-%m-%d')
                        vals = {'start': start_date, 'end': end_date}
                        conflicts.append(vals)
                # ////////////////////////////////////////////////////////////////////////////////////
                for conflict in conflicts:
                    if conflict['start'] > rec.date_from:
                        intersection_start = conflict['start']
                    else:
                        intersection_start = rec.date_from
                    if conflict['end'] < rec.date_to:
                        intersection_end = conflict['end']
                    else:
                        intersection_end = rec.date_to
                    is_merged = False
                    for intersection in intersections:
                        if intersection['start'] <= intersection_end and intersection['end'] >= intersection_start:
                            if intersection['start'] > intersection_start:
                                intersection['start'] = intersection_start
                            if intersection['end'] < intersection_end:
                                intersection['end'] = intersection_end
                            is_merged = True
                    if not is_merged:
                        intersections.append({'start': intersection_start, 'end': intersection_end})
                excluded_total_count = 0
                for intersection in intersections:
                    start_date = intersection['start']
                    end_date = intersection['end']
                    # /////////////////////////////////////////////////////////////////////////////////////
                    duration = relativedelta(end_date, start_date)
                    if duration.days == 30:
                        duration_days = 29
                    else:
                        duration_days = duration.days
                    number_of_days = (duration.years * 12 + duration.months) * 30 + duration_days + 1
                    # /////////////////////////////////////////////////////////////////////////////////////
                    excluded_total_count += number_of_days
                rec.total_excluded_days = excluded_total_count

    @api.model
    def get_moth_percentage(self):
        for rec in self:
            rate = float(rec.days_in_payslip) / 30.00
        return rate

    @api.constrains('date_from', 'date_to', 'contract_id')
    def check_trial_period(self):
        for rec in self:
            if rec.contract_id.trial_date_end and rec.contract_id.trial_date_end:
                if rec.date_from < rec.contract_id.trial_date_end and not rec.date_to < rec.contract_id.trial_date_end:
                    raise ValidationError(_("Attention !! \n date from and date to should be within trial period"))

    @api.constrains('employee_id')
    def check_old_payslips(self):
        for rec in self:
            old_payslips = rec.env['hr.payslip'].search(
                [('state', 'not in', ['cancel', 'done']), ('employee_id', '=', rec.employee_id.id),
                 ('id', '!=', rec.id)])
            # mig after end delete #TODO
            # if old_payslips:
            #     raise ValidationError(_(
            #         "Not allowed !! \n Dear Hr department, We found that this employee ( %s ) already have old payslip which not approved. In order to complete this action, kindly complete the process for old payslips or cancel them.") % rec.employee_id.name)

    # @api.one
    @api.depends('date_from', 'date_to', 'contract_id')
    def in_trial_period_(self):
        for rec in self:
            if rec.date_from < rec.contract_id.trial_date_end:
                rec.in_trial_period = True
            else:
                rec.in_trial_period = False

    @api.model
    def BSC_rule(self):
        basic_salary = not self.in_trial_period and self.contract_id.basic_salary or self.contract_id.trial_wage
        res = basic_salary  # * self.get_moth_percentage()
        return res

    @api.model
    def HOUSEALL_rule(self):
        house_allowance_amount = not self.in_trial_period and self.contract_id.house_allowance_amount or self.contract_id.trial_house_allowance_amount
        return house_allowance_amount  # * self.get_moth_percentage()

    @api.model
    def TRANSALL_rule(self):
        transportation_allowance_amount = not self.in_trial_period and self.contract_id.transportation_allowance_amount or self.contract_id.trial_transportation_allowance_amount
        return transportation_allowance_amount  # * self.get_moth_percentage()

    @api.model
    def PHOALL_rule(self):
        phone_allowance_amount = not self.in_trial_period and self.contract_id.phone_allowance_amount or self.contract_id.trial_phone_allowance_amount
        return phone_allowance_amount  # * self.get_moth_percentage()

    @api.model
    def OTHERALL(self):
        other_allowance = not self.in_trial_period and self.contract_id.other_allowance or self.contract_id.trial_other_allowance
        return other_allowance  # * self.get_moth_percentage()

    @api.model
    def net_rule(self):
        net_gross = self.net_gross()
        total_deductions = self.total_deductions()
        return net_gross + total_deductions  # * self.get_moth_percentage()

    @api.model
    def total_deductions(self):
        return 0.0

    @api.model
    def net_gross(self):
        total_gross = self.BSC_rule() + self.HOUSEALL_rule() + self.TRANSALL_rule() + self.PHOALL_rule() + self.OTHERALL()
        return total_gross * self.get_moth_percentage()

    @api.model
    def get_rule_code_dict(self):
        pass

    # @api.multi
    def refund_sheet(self):
        for record in self:
            # msg = _(
            #     "Attention !! \n If you created a refund for this payslip, your system will create a new payslip for the same employee and same period with negative values to reverse old payslip effect.Are you sure that you want to continue ")
            # raise UserError(msg)
            record.refund_sheet_modified()
            # return self.env.user.show_dialogue(msg, 'hr.payslip', 'refund_sheet_modified', record.id)

    def refund_sheet(self):
        # raise UserError('( loan - deductions - rewards - leaves integration ) while reverse payslip still under development')
        res = super(hr_payslip, self).refund_sheet()
        return res

    # @api.multi
    def action_draft(self):
        for record in self:
            record.check_old_payslips()
            record.write({'state': 'draft'})
        return {}

