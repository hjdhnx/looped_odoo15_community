# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from datetime import timedelta
import calendar
from dateutil.relativedelta import relativedelta
from odoo import tools
import math
import pytz
from dateutil import tz
import os



class effective_notice(models.Model):
    _name = 'effective.notice'
    _inherit = ['mail.thread']
    _rec_name = 'desc'

    name = fields.Char(_('Code'), readonly=True)
    desc = fields.Char('Description', required=True)
    employee_id = fields.Many2one('hr.employee', string=_('Employee'), required=True, default=lambda self: self.env.context.get('active_id', False))
    employee_number = fields.Char(_('Employee Number'), related="employee_id.employee_number", readonly=True, store=True)
    department_id = fields.Many2one('hr.department', string=_('Department'), related="employee_id.department_id", readonly=True, store=True)
    job_id = fields.Many2one('hr.job', string=_('Job Title'), related="employee_id.job_id", readonly=True, store=True)
    country_id = fields.Many2one('res.country', _('‫‪Nationality‬‬'), related="employee_id.country_id", readonly=True, store=True)
    start_work = fields.Date(string="Starting Work at", required=True)
    payslip_date = fields.Date(string="Payslip Date")
    type = fields.Selection([('New Employee', 'New Employee')], _('Effective Notice Type'), required=True, default='New Employee')
    created_by = fields.Many2one('res.users', default=lambda self: self.env.uid, readonly=True, string="Created By")
    notes = fields.Text(string="Notes")

    effective_ids = fields.Many2many('effective.notice', 'effective.notice_rel', 'eff_1', 'eff_2', _('Previous Effective Notices'), readonly=True,
                                     compute='_compute_previous')
    state = fields.Selection([
        ('New', 'New'),
        ('Department manager approval', 'Department manager approval'),
        ('HR department approval', 'HR department approval'),
        ('Refused', 'Refused'),
    ], string='Status', select=True, default='New', )

    leave_request_id = fields.Many2one('hr.leave', string='Leave Request')
    leave_start_date = fields.Datetime('Leave Start Date', related="leave_request_id.date_from", )
    leave_end_date = fields.Datetime('Leave End Date', related="leave_request_id.date_to", )
    expected_working_day = fields.Date('Expected working day', related="leave_request_id.expected_working_day")
    count_leave_allocations = fields.Integer('Number of Leave Allocations', compute='get_count_smart_buttons')
    count_deductions = fields.Integer('Number of Deductions', compute='get_count_smart_buttons')

    #@api.one
    @api.depends('employee_id', 'leave_request_id')
    def get_count_smart_buttons(self):
        leave_allocations = self.env['hr.leave'].search(['|', ('early_return_from_leave', '=', self.id), ('late_return_from_leave', '=', self.id)])
        self.count_leave_allocations = len(leave_allocations)
        deductions = self.env['employee.deductions.violations'].search(
            ['|', ('early_return_from_leave', '=', self.id), ('late_return_from_leave', '=', self.id)])
        self.count_deductions = len(deductions)

    #@api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'New':
                raise exceptions.ValidationError(_("Not allowed to delete a confirmed"))
        return super(effective_notice, self).unlink()

    #@api.multi
    def action_department_manager_approval(self):
        for record in self:
            record.write({'state': 'Department manager approval'})
            body = "This Record Approved By Department Manager"
            self.message_post(body=body, message_type='email')
        return {}

    #@api.multi
    def action_hr_department_approval(self):
        for record in self:

            # //////////////  Check For Old Leave Request /////////////////////////////////////////////
            old_leave_requests = self.env['hr.leave'].search(
                [('state', '!=', 'refuse'), ('employee_id', '=', record.employee_id.id), ('date_from', '<=', record.start_work),
                 ('date_to', '>=', record.start_work), ('id', '!=', record.leave_request_id.id)])
            if old_leave_requests:
                for old_leave_request in old_leave_requests:
                    error_msg = "Not allowed !! \n Based on the old leave Requests, there is a leave request start between ( %s ) the employee Returned back to work on ( %s ) which located in a leave ( %s ) Kindly review your data." % (
                        old_leave_request.date_from, old_leave_request.expected_working_day, old_leave_request.name)
                    raise ValidationError(_(error_msg))


            # //////////////  Check For Old Working schedule Days /////////////////////////////////////////////
            checked_date = record.start_work
            week_day = checked_date.weekday()
            contracts = self.env['hr.contract'].search([('employee_id', '=', record.employee_id.id), ('active', '=', True)])
            if len(contracts):
                contract = contracts[0]
            else:
                contract = False
            day_on_working_days = 0
            if contract and contract.attendance_ids:
                for attendance_id in contract.attendance_ids:
                    if week_day == int(attendance_id.dayofweek):
                        day_on_working_days = 1
                if not day_on_working_days:
                    weekday_error_msg = "Not allowed !! \n It is not logic that the employee will start working on ( %s ), because we found that this day is a weakly rest for this employee. " % record.start_work
                    raise ValidationError(_(weekday_error_msg))

            if record.type == 'New Employee':
                record.employee_id.start_working_date = record.start_work

            # /////////////////////////////////////////////////////////////////////////////////////
            if record.type == 'New Employee':
                old_effective_notices = self.env['effective.notice'].search(
                    [('state', '=', 'HR department approval'), ('employee_id', '=', record.employee_id.id), ('type', '=', 'New Employee')])
                if old_effective_notices:
                    raise exceptions.ValidationError(
                        "Dear Hr Manager. \n You cannot approve this effective notice, we found that this employee has old effective notices with type = New employee. Each employee can create effective notices as a new employee one time only. if this employee resigned and back to work, you must create a new employee with a different employee number.")
            # ////////////////////////////////////////////////////////////////////////////////////

            return self.hr_department_approval()

    #@api.multi
    def early_back_from_leave(self):
        for record in self:
            if record.leave_request_id.leave_request_extend_id:
                error_msg = "Attention !! \n We found that this leave request is already extended with another leave request ( %s ).So it is not logic to create a return from a leave for an extended leave. you are allowed to create a Return from leave for the new extended leave." % record.leave_request_id.leave_request_extend_id.name
                raise ValidationError(_(error_msg))
            if record.leave_request_id.holiday_status_id.type == 'Non Annual Leave':
                return self.hr_department_approval()
            if record.leave_request_id.holiday_status_id.type == 'Annual Leave':
                if record.leave_request_id.holiday_status_id.reconciliation_method == 'Stop payslip during leave and use leave reconciliation':
                    return self.early_leave_reconciliation_wizard()

    #@api.multi
    def early_leave_reconciliation_wizard(self):
        for record in self:
            ctx = {'record_id': record.id, }
            return {
                'domain': "[]",
                'name': _('Reconciliation Confirmation'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'early.leave.reconciliation.wizard',
                'view_id': self.env.ref('mits_hr_leaves.early_leave_reconciliation_wizard').id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': ctx,
            }

    #@api.multi
    def early_leave_reconciliation(self, choice):
        for record in self:
            if choice == 'reallocate':
                if record.leave_request_id.leave_reconciliation_amount > 0:
                    from_dt = record.leave_start_date
                    to_dt = record.start_work
                    timedelta_custom = to_dt - from_dt
                    new_leave_duration = timedelta_custom.days
                    # //////////////////////////// Compute recon Amount
                    based_on_value = 0
                    if record.leave_request_id.holiday_status_id.reconciliation_method == 'Stop payslip during leave and use leave reconciliation':
                        if record.leave_request_id.request_reason == 'annual' and record.leave_request_id.contract_id and record.leave_request_id.holiday_status_type == 'Annual Leave':
                            if record.leave_request_id.reconciliation_based_on == 'basic':
                                based_on_value = record.leave_request_id.basic_salary
                        new_leave_reconciliation_amount = (based_on_value / 30) * (new_leave_duration)
                    else:
                        new_leave_reconciliation_amount = 0
                    # /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                    if new_leave_reconciliation_amount > record.leave_request_id.leave_reconciliation_amount:
                        raise exceptions.ValidationError("Data Error! \n Unhandled case !")
                    if new_leave_reconciliation_amount < record.leave_request_id.leave_reconciliation_amount:
                        if new_leave_reconciliation_amount >= record.leave_request_id.paid_amount:
                            record.leave_request_id.leave_reconciliation_amount = new_leave_reconciliation_amount
                        else:
                            deduction_vals = {
                                'desc': 'auto deduction due to early return from leave',
                                'employee_id': record.employee_id.id,
                                'deduction_date': datetime.today().strftime('%Y-%m-%d'),
                                'deduction_reason': 'other',
                                'decision': 'deduction',
                                'deduction_type': 'fixed',
                                'deduction_value': record.leave_request_id.paid_amount - new_leave_reconciliation_amount,
                                'auto_deduction': True,
                                'early_return_from_leave': record.id,
                            }
                            leave_deduction_id = self.env['employee.deductions.violations'].create(deduction_vals)
                            leave_deduction_id.confirm()

            # ///////// Add Report As Attachment
            old_end_date = record.leave_request_id.date_to
            # //////////////////////////// Make end date = startwork - 1 day ///////////////////////////////////
            body = "This leave Request had been modified due to early return from leave"
            self.message_post(body=body, message_type='email')
            new_leave_end_date = record.start_work - timedelta(days=1)
            record.leave_request_id.date_to = new_leave_end_date.strftime('%Y-%m-%d %H:%M:%S')
            record.leave_request_id.expected_working_day = record.start_work

            # //////////////////////////// Make Reallocation ///////////////////////////////////
            last_allocation = self.env['hr.leave'].search([('type', '=', 'add'), ('employee_id', '=', record.employee_id.id), ('state', '=', 'validate')],
                                                             limit=1, order="allocation_date desc")
            if last_allocation:
                allocation_date = last_allocation.allocation_date
            else:
                contracts = self.env['hr.contract'].search([('employee_id', '=', record.employee_id.id), ('active', '=', True)])
                if len(contracts):
                    contract = contracts[0]
                if contract:
                    allocation_date = contract.adjusted_date
            date_1 = record.start_work
            date_2 = old_end_date
            diff = date_2 - date_1
            early_returned_days = diff.days + 1
            vals = {
                'name': 'Re-allocate annual leave balance due to early return from leave',
                'employee_id': record.employee_id.id,
                'allocation_date': allocation_date,
                'number_of_days': early_returned_days,
                'type': 'add',
                'system_created': True,
                'approved_by': self.env.uid,
                'holiday_status_id': record.leave_request_id.holiday_status_id.id,
                'early_return_from_leave': record.id,
            }
            leave_allocation_id = self.env['hr.leave'].create(vals)
            leave_allocation_id.signal_workflow('validate')
            if leave_allocation_id.double_validation:
                leave_allocation_id.signal_workflow('second_validate')

            # ///////////////////////////////////////////////////////////////////////////////////
            return self.hr_department_approval()

    #@api.multi
    def late_back_from_leave_wizard(self):
        for record in self:
            absence = record.start_work - record.leave_request_id.date_to
            absence_days = absence.days
            leave_balance = str(record.employee_id.leaves_count)
            message = "Attention !! \n Dear Hr manager, \n There is ( %s ) days absence. Employee annual leave balance is ( %s ) " % (
                absence_days, leave_balance)
            ctx = {'record_id': record.id, 'default_message': message}
            return {
                'domain': "[]",
                'name': _('Late Back From Leave'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'late.back.from.leave.wizard',
                'view_id': self.env.ref('mits_hr_leaves.late_back_from_leave_wizard').id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': ctx,
            }

    #@api.multi
    def late_back_from_leave(self, choice):
        for record in self:
            if choice == 'deduct':
                # //////////////////////////// Make Reallocation ///////////////////////////////////
                contracts = self.env['hr.contract'].search([('employee_id', '=', record.employee_id.id), ('active', '=', True)])
                if len(contracts):
                    contract = contracts[0]

                last_allocation = self.env['hr.leave'].search(
                    [('type', '=', 'add'), ('employee_id', '=', record.employee_id.id), ('state', '=', 'validate')], limit=1, order="allocation_date desc")
                if last_allocation:
                    allocation_date = last_allocation.allocation_date
                else:

                    if contract:
                        allocation_date = contract.adjusted_date
                date_2 = record.start_work
                date_1 = record.leave_request_id.date_to
                diff = date_2 - date_1
                late_returned_days = diff.days - 1
                minus_late_returned_days = late_returned_days * -1
                vals = {
                    'name': 'Deduct annual leave balance due to late return from leave',
                    'employee_id': record.employee_id.id,
                    'allocation_date': allocation_date,
                    'number_of_days': minus_late_returned_days,
                    'type': 'add',
                    'system_created': True,
                    'approved_by': self.env.uid,
                    'holiday_status_id': contract.annual_leave_policy.id,
                    'allow_minus_value': True,
                    'late_return_from_leave': record.id,
                }
                leave_allocation_id = self.env['hr.leave'].create(vals)
                leave_allocation_id.signal_workflow('validate')
                if leave_allocation_id.double_validation:
                    leave_allocation_id.signal_workflow('second_validate')


                    # ///////////////////////////////////////////////////////////////////////////////////
            if choice == 'extend':
                leave_request = record.leave_request_id
                extend_start = leave_request.date_to + timedelta(1)
                extend_end = record.start_work - timedelta(1)
                ctx = self.env.context.copy()
                custom_context = {
                    "default_employee_id": leave_request.employee_id.id,
                    "default_date_from": extend_start.strftime('%Y-%m-%d %H:%M:%S'),
                    "default_date_to": extend_end.strftime('%Y-%m-%d %H:%M:%S'),
                    "default_original_leave_request_id": leave_request.id,
                    'popup': True,
                    'return_from_leave': record.id,
                    'readonly_by_pass': True
                }
                ctx.update(custom_context)
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'hr.leave',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': self.env.ref('mits_hr_leaves.leave_request_form').id,
                    'context': ctx,
                    'target': 'current',
                }
            if choice == 'absent':
                leave_request = record.leave_request_id
                ctx = self.env.context.copy()
                custom_context = {
                    "default_employee_id": leave_request.employee_id.id,
                    "default_desc": 'Deduction due to late return from leave',
                    "default_deduction_date": record.start_work,
                    'popup': True,
                    'return_from_leave': record.id,
                    'readonly_by_pass': True,
                    'default_auto_deduction': True,
                    'default_late_return_from_leave': record.id,
                }
                ctx.update(custom_context)
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'employee.deductions.violations',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': self.env.ref('hr_loans.employee_deductions_violations_form').id,
                    'context': ctx,
                    'target': 'current',
                }

            # ///////////////////////////////////////////////////////////////////////////////////
            return self.hr_department_approval()

    #@api.multi
    def hr_department_approval(self):
        for record in self:
            if record.type == 'Return From Leave':
                if record.leave_request_id.return_from_leave:
                    raise exceptions.ValidationError(
                        "Not Allowed !! \n We found that the leave which you selected is already linked with another Return from leave, it is not logic to create 2 return from leave for the same leave request,  kindly review old return from leave  for the same employee.")
                else:
                    record.leave_request_id.return_from_leave = record.id

            record.write({'state': 'HR department approval'})
            body = "This Record approved by hr department "
            self.message_post(body=body, message_type='email')
        return {}

    #@api.multi
    def action_Refuse(self):
        for record in self:
            record.write({'state': 'Refused'})
            body = "This Record Refused"
            self.message_post(body=body, message_type='email')
        return {}

    #@api.multi
    def action_set_to_new(self):
        for record in self:
            record.write({'state': 'New'})
            body = "This Record Set To New"
            self.message_post(body=body, message_type='email')
        return {}

    @api.depends('employee_id')
    def _compute_previous(self):
        for rec in self:
            # Get Old Effective notices
            if not rec.id:
                old_notices = self.env['effective.notice'].search([('employee_id', '=', rec.employee_id.id)])
            else:
                old_notices = self.env['effective.notice'].search([('employee_id', '=', rec.employee_id.id), ('id', '!=', rec.id)])
            self.effective_ids = old_notices

    # @api.onchange('employee_id')
    # def onchange_employee_id(self):
    #     employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
    #     employees = self.env['hr.employee'].search([])
    #     if employee and employee[0].manager:
    #         return {'domain': {'employee_id': [('id', 'in', employees.ids)]}}
    #     if not employee:
    #         return {'domain': {'employee_id': [('id', 'in', [])]}}
    #     if employee and not employee[0].manager:
    #         self.employee_id = employee[0].id
    #         return {'domain': {'employee_id': [('id', '=', employee[0].id)]}}

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].sudo().next_by_code('effective.notice')
        res = super(effective_notice, self).create(vals)
        return res

    @api.onchange('type')
    def onchange_type(self):
        self.leave_request_id = ''


class effective_notice_employee(models.Model):
    _inherit = 'hr.employee'

    start_working_date = fields.Datetime(string="Start Working Date", readonly=True)
    effective_count = fields.Float('Effective Notices count', compute='get_effective_count')

    #@api.one
    def get_loans_count(self):
        self.effective_count = len(self.env['effective.notice'].search([['employee_id', '=', self.id]]))

    def action_effective_notices(self,):
        return {
            'domain': "[('employee_id','in',[" + ','.join(map(str, self.ids)) + "])]",
            'name': _('Effective Notices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'effective.notice',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

class contract_work_permit_line(models.Model):
    _name = "contract.work.permit.line"

    name = fields.Char("Name")
    dayofweek = fields.Selection(
        [('0', 'Monday'), ('1', 'Tuesday'), ('2', 'Wednesday'), ('3', 'Thursday'), ('4', 'Friday'), ('5', 'Saturday'), ('6', 'Sunday')], 'Day of Week',
        required=True, select=True)
    date_from = fields.Date('Starting Date')
    date_to = fields.Date('End Date')
    hour_from = fields.Float('Work from', required=True, help="Start and End time of working.", select=True)
    hour_to = fields.Float("Work to", required=True)
    contract_id = fields.Many2one("hr.contract", "Contract", required=True,ondelete='cascade')


class hr_contract(models.Model):
    _inherit = "hr.contract"


    annual_leave_policy = fields.Many2one('hr.leave.type', string='Annual Leave Policy', required=True)
    first_effective_notice = fields.Many2one('effective.notice', string='First Effective Notice', )
    start_work = fields.Date(string="Starting Work at",)
    start_work_ = fields.Date(string="Starting Work at", )
    # trial_date_start = fields.Date('Trial Start Date', )
    # trial_date_end = fields.Date('Trial End Date', )
    leaves_calc_on = fields.Date('Leaves Will Be Calculated On', readonly=True, compute="_compute_leaves_calc_on", store=True)
    adjusted_date = fields.Date('Adjusted date', compute="_compute_adjusted_date", store=True)
    attendance_ids = fields.One2many('contract.work.permit.line', 'contract_id', string='Working Time')
    res_attendance_ids = fields.One2many('resource.calendar.attendance',string='Working Time',related="resource_calendar_id.attendance_ids")
    can_request_air_ticket = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='can request air ticket',related="annual_leave_policy.can_request_air_ticket")
    
    #@api.one
    def set_start_work(self):
        for rec in self:
            rec.start_work_ = rec.start_work

    #@api.one
    @api.onchange('first_effective_notice', 'start_work_')
    def get_start_work(self):
        for rec in self:
            if rec.first_effective_notice:
                rec.start_work = rec.first_effective_notice.start_work #rec.start_work_ or rec.first_effective_notice.start_work
                rec.date_start = rec.first_effective_notice.start_work
    @api.onchange('employee_id')
    def onchange_employee(self):
        if not self.employee_id:
            self.job_id = False
            self.department_id = False
        if self.employee_id.job_id:
            self.job_id = self.employee_id.job_id.id
        if self.employee_id.department_id:
            self.department_id = self.employee_id.department_id.id

        self.first_effective_notice = False
        self.resource_calendar_id = False
        return {'domain': {
            'first_effective_notice': [('employee_id', '=', self.employee_id.id), ('state', '!=', 'Refused'), ('type', '=', 'New Employee')]}}

    @api.depends('annual_leave_policy', 'start_work', 'trial_date_start', 'date_start')
    def _compute_leaves_calc_on(self):
        for rec in self:
            if rec.annual_leave_policy.start_calc_from == "First Effective Notice":
                rec.leaves_calc_on = rec.start_work
            if rec.annual_leave_policy.start_calc_from == "Contract Start Date":
                rec.leaves_calc_on = rec.date_start
            if rec.annual_leave_policy.start_calc_from == "Trial Period Start Date":
                rec.leaves_calc_on = rec.trial_date_start

    #@api.multi
    @api.onchange('resource_calendar_id')
    def get_attendance_ids(self):
        for rec in self:
            if rec.resource_calendar_id:
                attendance_ids = self.env['resource.calendar.attendance'].search([['calendar_id', '=', rec.resource_calendar_id.id]])
                line_vals = []
                for attendance_id in attendance_ids:
                    vals = (0,0,{
                        'name': attendance_id.name,
                        'dayofweek': attendance_id.dayofweek,
                        'date_from': attendance_id.date_from,
                        'date_to': attendance_id.date_to,
                        'hour_from': attendance_id.hour_from,
                        'hour_to': attendance_id.hour_to,
                        'contract_id': rec.id,
                    })
                    line_vals.append(vals)
                rec.attendance_ids = line_vals
            else:
                rec.attendance_ids = False

    @api.depends('leaves_calc_on')
    def _compute_adjusted_date(self):
        for rec in self:
            if rec.leaves_calc_on:
                date = rec.leaves_calc_on
                day = date.day
                if day in [29, 30, 31]:
                    date = date.replace(day=28)
                rec.adjusted_date = date



class LeaveReconciliationPaidLine(models.Model):
    _name = "leave.reconciliation.paid.line"

    request_id = fields.Many2one('hr.leave', 'Leave Request')
    date = fields.Date('Date')
    amount = fields.Float('Amount')
    reconciliation_id = fields.Many2one('hr.leave.reconciliation', 'Leave Reconciliation')
    eos = fields.Char()
    note = fields.Char('Notes')


class ExitRentryValidateion(models.Model):
    _name = "exit.rentry.validation"

    validation_from = fields.Selection([
        ('leave', 'Leave'),
        ('air_ticket', 'Air ticket'),
        ('exit_rentry', 'Exit Re-entry'),
    ])
    leave_request_id = fields.Many2one('hr.leave', 'Leave request')
    exit_rentry_id = fields.Many2one('hr.exit.entry.request', 'Exit Re-entry')
    employee_id = fields.Many2one('hr.employee', 'Employee')

    air_ticket_id = fields.Many2one('air.ticket.request', 'Air ticket request')

    #@api.one
    def create_exit_rentry(self):
        if self.validation_from == 'leave':
            self.leave_request_id.create_exit_rentry()
        if self.validation_from == 'air_ticket':
            self.air_ticket_id.create_exit_rentry()
        if self.validation_from == 'exit_rentry':
            ctx = dict(self._context.copy(), exit_rentry_validation=True)
            self.with_context(ctx).exit_rentry_id.confirm()


class LeaveAttachments(models.Model):
    _name = "leave.attachment"

    leave_request_id = fields.Many2one('hr.leave', 'Leave request')
    name = fields.Char('Description')
    file = fields.Binary('Attachments', #compute='get_file', inverse='set_file'
    )
    file_name = fields.Char('File name')
    note = fields.Char('Notes')

    @api.onchange('file_name')
    def file_name_(self):
        self.name = self.file_name

    # #@api.one
    # def set_file(self):
    #     open(self.get_file_name, 'w').write(self.file.decode('base64'))

    # #@api.one
    # def get_file(self):
    #     file = False
    #     try:
    #         file = open(self.get_file_name, 'r').read().encode('base64')
    #     except:
    #         pass
    #     self.file = file

    #@api.one
    def unlink(self):
        os.remove(self.get_file_name)
        return super(LeaveAttachments, self).unlink()

    #@api.one
    def get_file_name(self):
        return "%s-%s-%s" % (self._name, self.name, self.id)


class Employee(models.Model):
    _inherit = "hr.employee"


    leaves_count = fields.Integer('Number of Leaves', compute='_get_leaves_count')
    leaves_count_float = fields.Float('Number of Leaves', compute='_get_leaves_count')
    all_allocation_count = fields.Integer('Number of Allocation', compute='_get_leaves_count')
    non_annual_leave_balance = fields.One2many('non.annual.leave.balance', 'employee_id', string="Non Annual leave Balance")

    #@api.one
    @api.depends()
    def _get_leaves_count(self):
        for rec in self:
            rec.leaves_count = rec.leaves_count_float = 0
            contracts = rec.env['hr.contract'].search([('employee_id', '=', rec.id), ('active', '=', True)])
            if len(contracts):
                contract = contracts[0]
            else:
                contract = False
            if contract and contract.annual_leave_policy:
                leaves = rec.env['hr.leave'].search([['employee_id', '=', rec.id],
                ['holiday_status_id.limit', '=', False],
                ['state', '=', 'validate'],
                    ['holiday_status_id', '=', contract.annual_leave_policy.id]])
                rec.leaves_count = rec.leaves_count_float = sum([l.number_of_days for l in leaves])
            
                leaves = rec.env['hr.leave.allocation'].search([['employee_id', '=', rec.id],
                ['holiday_status_id.limit', '=', False],
                ['state', '=', 'validate'],
                    ['holiday_status_id', '=', contract.annual_leave_policy.id]])
                rec.all_allocation_count = sum([l.number_of_days for l in leaves])
            
            else:
                rec.leaves_count = 0
                rec.all_allocation_count = 0



    @api.model
    def create(self, vals):
        res = super(Employee, self).create(vals)
        self.refresh_non_annual()
        return res

    #@api.multi
    def write(self, vals):
        res = super(Employee, self).write(vals)
        self.refresh_non_annual()
        return res

    #@api.multi
    def refresh_non_annual(self):
        for record in self:
            contracts = self.env['hr.contract'].search([('employee_id', '=', record.id), ('active', '=', True)])
            if len(contracts):
                contract = contracts[0]
            else:
                return
            for balance in record.non_annual_leave_balance:
                balance.unlink()
            if not record.nationality_type or not record.marital or not record.gender or not record.religion:
                return

            nationality_filter = ['All Nationalities']
            if record.nationality_type == 'Saudi':
                nationality_filter.append('Saudi')
            else:
                nationality_filter.append('Non-Saudi')

            marital_filter = ['Both']
            if record.marital == 'single':
                marital_filter.append('Single')
            else:
                marital_filter.append('Married')

            who_request_filter = ['Both']
            if record.gender == 'male':
                who_request_filter.append('Male only')
            else:
                who_request_filter.append('Females only')

            religion_filter = ['All Religions']
            if record.religion == 'single':
                religion_filter.append('Muslim')
            else:
                religion_filter.append('Non-Muslim')

            domain = [
                ('type', '=', 'Non Annual Leave'),
                ('state', '=', 'Approved'),
                ('nationality', 'in', nationality_filter),
                ('marital_status', 'in', marital_filter),
                ('who_request', 'in', who_request_filter),
                ('religion', 'in', religion_filter),
            ]
            non_annual_leaves = self.env['hr.leave.type'].search(domain)
            for non_annual_leave in non_annual_leaves:
                allocations = self.env['hr.leave'].search([
                    ('type', '=', 'add'),
                    ('state', '!=', 'refuse'),
                    ('employee_id', '=', record.id),
                    ('contract_id', '=', contract.id),
                    ('holiday_status_id', '=', non_annual_leave.id),
                    ('allocation_date', '>=', contract.date_start),
                ])
                total_allocation_days = 0
                for allocation in allocations:
                    total_allocation_days += allocation.number_of_days

                requests = self.env['hr.leave'].search([
                    # ('type', '=', 'remove'),
                    ('state', '!=', 'refuse'),
                    ('employee_id', '=', record.id),
                    ('contract_id', '=', contract.id),
                    ('holiday_status_id', '=', non_annual_leave.id),
                    ('date_from', '>=', contract.date_start),
                ], order="date_from desc")
                total_request_days = 0
                for request in requests:
                    total_request_days += request.number_of_days
                total_request_days *= -1

                if len(requests):
                    last_leave_request = requests[0]
                else:
                    last_leave_request = False

                line_data = {
                    'holidays_status_id': non_annual_leave.id,
                    'non_annual_frequency': non_annual_leave.non_annual_frequency,
                    'total_allocated_days': total_allocation_days,
                    'total_requested_days': total_request_days,
                    'last_leave_request': last_leave_request and last_leave_request.id,
                    'employee_id': record.id
                }
                self.env['non.annual.leave.balance'].create(line_data)


class non_annual_leave_balance(models.Model):
    _name = "non.annual.leave.balance"

    holidays_status_id = fields.Many2one('hr.leave.type', string=_('Description'))
    non_annual_frequency = fields.Selection([
        ('contract', 'Per contract'),
        ('financial_year', 'Per financial year ( 1Jan : 31 Dec)'),
        ('contractual_year', 'Each contractual year ( hiring dat to next year)'),
        ('one_time', 'one time per live.'),
        ('per_request', 'based on request (no limitation)'),
    ], string='Non annual leave Frequency')
    total_allocated_days = fields.Integer('Total Days Allocated')
    total_requested_days = fields.Integer('Total Days Requested')
    net_balance = fields.Integer('Net Balance', compute='_compute_net_balance')
    last_leave_request = fields.Many2one('hr.leave', string="Last Leave Request")
    leave_request_date = fields.Datetime('Leave Request Date', related="last_leave_request.date_from")
    employee_id = fields.Many2one('hr.employee', string=_('Employee'), )

    @api.depends('total_allocated_days', 'total_requested_days')
    def _compute_net_balance(self):
        for rec in self:
            rec.net_balance = rec.total_allocated_days + rec.total_requested_days
