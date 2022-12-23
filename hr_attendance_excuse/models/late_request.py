# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime, time, timedelta
from odoo.fields import Date, Datetime
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class LateRequest(models.Model):
    _name = 'late.request'
    _inherit = 'mail.thread'
    # _rec_name = 'employee_id'
    _description = 'Late Request'

    name = fields.Char(default='/')
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False,default=lambda self:self.env.user.employee_id.id , track_visibility='onchange')
    penalty_id = fields.Many2one(comodel_name="hr.attendance.penalty", string="Penalty",
     required=False, )
    hours = fields.Float(string="Penality Hours", required=False, 
    # related="penalty_id.hours"
    )
    days = fields.Float(string="Days", required=False, 
    # related="penalty_id.days"
    )
    note = fields.Text(string="Late Reason", required=False, )
    date = fields.Date(string="Date", required=False, default=date.today(), track_visibility='onchange')

    state = fields.Selection(string="state",
                             selection=[('draft', 'Draft'), ('confirm', 'Confirmed'), ('approve', 'Approved'),('refuse','Refuse') ],
                             required=False, default='draft', track_visibility='onchange')

    late_request_id = fields.Many2one('late.request.type',string="Type",track_visibility='onchange')
    period_type = fields.Selection([('hours','Hour'),('days','Days')],related="late_request_id.period_type",
    required=1)
    
    employee_current_hours = fields.Float(string="Used Hours",compute="get_employee_limit_data",store=True)
    employee_current_days = fields.Float(string="Used Days",compute="get_employee_limit_data",store=True)

    employee_left_hours = fields.Float(string="Remaining Hours",compute="get_employee_limit_data",store=True)
    employee_left_days = fields.Float(string="Remaining Days",compute="get_employee_limit_data",store=True)
    department_id = fields.Many2one('hr.department',related="employee_id.department_id",readonly=1)
    job_id = fields.Many2one('hr.job',related="employee_id.job_id",readonly=1)
    manager_id = fields.Many2one('hr.employee',related="employee_id.department_id.manager_id",readonly=1)
    employee_number = fields.Char('Number',related='employee_id.employee_number',readonly=1)
    refuse_reason = fields.Char()
    amount = fields.Float()

    # start_time = fields.Float()
    # end_time = fields.Float()
    @api.constrains('employee_id','penalty_id','late_request_id','date')
    def check_limit(self):
        for rec in self:
            if rec.employee_current_hours or rec.employee_current_days :
                if rec.period_type == 'hours':
                    total_current_balance  = rec.employee_current_hours + rec.hours
                    if total_current_balance > rec.late_request_id.hours_limit:
                        raise UserError(_("Sorry!!,you Exceed  Hours Limit."))

                if rec.period_type == 'days':
                    total_current_balance  = rec.employee_current_days + rec.days
                    if total_current_balance > rec.late_request_id.days_limit:
                        raise UserError(_("Sorry!!,you Exceed Days Limit."))

        
    @api.depends('employee_id','penalty_id','late_request_id','date')
    def get_employee_limit_data(self):
        for rec in self:
            rec.employee_current_hours = rec.employee_current_days = rec.employee_left_hours = rec.employee_left_days = 0
            if rec.employee_id and rec.penalty_id and rec.late_request_id and rec.date:
                month_start_date = rec.date.replace(day=1)
                month_end_date = rec.date
                
                month_end_date = ((month_end_date + relativedelta(months=1)).replace(day=1)) + relativedelta(days=-1)
                
                prevs_late = self.env['late.request'].search([
                        ('id','!=',rec._origin.id),
                        ('employee_id','=',rec.employee_id.id),
                        ('late_request_id','=',rec.late_request_id.id),
                        ('date','>=',month_start_date),
                        ('date','<=',month_end_date),
                        ('state','=','approve')
                        ])
                if prevs_late:
                    if rec.period_type == 'hours':
                        rec.employee_current_hours = sum([prev.hours for prev in prevs_late])
                        rec.employee_left_hours = rec.late_request_id.hours_limit - rec.employee_current_hours 
                    if rec.period_type == 'days':
                        rec.employee_current_days = sum([prev.days for prev in prevs_late])
                        rec.employee_left_days = rec.late_request_id.days_limit - rec.employee_current_days
                else:
                    if rec.period_type == 'hours':
                        rec.employee_left_hours = rec.late_request_id.hours_limit
                    if rec.period_type == 'days':
                        rec.employee_left_days = rec.late_request_id.days_limit 

        return        


    @api.onchange('employee_id','date','late_request_id')
    def onchange_set_penality_domain(self):
        self.penalty_id = False
        if self.employee_id and self.date and self.late_request_id:
            domain = [('employee_id', '=', self.employee_id.id), 
                    # ('type','!=','ab'),
                    ('date','=',self.date),
                    ('late_request_id','=',False),
                    # ('state', '=', 'confirmed')
                    ]
            if self.late_request_id.penality_type != 'other':
                domain.append(('type','=',self.late_request_id.penality_type))
            return {
                'domain': {
                    'penalty_id': domain 
                }
            }
        else:
            return {
                'domain': {
                    'penalty_id': [('id','=',0)], 
                }
            }
        

    @api.onchange('late_request_id','penalty_id')
    def onchange_penalty_set_act_hours(self):
        for rec in self:
            if rec.late_request_id and rec.penalty_id:
                hours = rec.penalty_id.act_hours
                if rec.late_request_id.period_type == 'hours':
                    rec.hours = hours
                elif rec.late_request_id.period_type == 'days':
                    day_hours = 8
                    rec.days = hours/day_hours
                rec.amount = rec.penalty_id.amount
            else:
                rec.hours = rec.days = rec.amount = 0


                
    def action_submit(self):
        for rec in self:
            rec.state = 'confirm'

    def action_draft(self):
        for rec in self:
            if rec.penalty_id.late_request_id :
                rec.penalty_id.amount = rec.amount
                rec.penalty_id.late_request_id = False
                # rec.amount = 0
            rec.refuse_reason = False
            rec.state = 'draft'

    def action_refuse(self):
        for rec in self:
            if not rec.refuse_reason:
                raise UserError(_("Sorry!!,Please Fill Refuse Reason First."))
            rec.state = 'refuse'

    def action_approve(self):
        # self.penalty_id.action_cancel()
        for rec in self:
            rec.penalty_id.amount = 0
            rec.penalty_id.late_request_id = rec.id
            rec.state = 'approve'


    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(self._name) or '/'
        return super(LateRequest, self).create(vals)
        


class hrAttendancePenalty(models.Model):
    _inherit = 'hr.attendance.penalty'
    #@api.multi
    # @api.depends('employee_id')

    late_request_id = fields.Many2one('late.request')

    def name_get(self):
        res = []
        for rec in self:
            name = rec.name
            if rec.date:
                name += ' - '+str(rec.date)
            
            res += [(rec.id, name)]
        return res
