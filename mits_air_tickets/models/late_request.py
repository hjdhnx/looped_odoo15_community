# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _



from datetime import date, datetime, time, timedelta
from odoo.fields import Date, Datetime
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class lateRequestType(models.Model):
    _inherit = 'late.request.type'


    is_business_trip = fields.Boolean()
    air_ticket_type_id = fields.Many2one('air.ticket.type')
    duration_in_leave_request = fields.Selection([('no','No'),('yes','Yes')],string="Include Holiday Duration",default='no')

    @api.onchange('penality_type','period_type')
    def onchange_set_business_trip(self):
        for rec in self:
            if rec.penality_type != 'other' or rec.period_type != 'days':
                rec.is_business_trip = False
                rec.air_ticket_type_id = False


class lateRequest(models.Model):
    _inherit = 'late.request'

    is_business_trip = fields.Boolean(related="late_request_id.is_business_trip",store=True)
    date_from = fields.Datetime()
    date_to = fields.Datetime()
    number_of_days = fields.Integer()
    duration_in_leave_request = fields.Selection(related="late_request_id.duration_in_leave_request",store=True)

    @api.constrains('employee_id','penalty_id','late_request_id','date','date_from','date_to')
    def check_limit(self):
        for rec in self:
            # if rec.employee_current_hours or rec.employee_current_days :
            if rec.period_type == 'hours':
                total_current_balance  = rec.employee_current_hours + rec.hours
                if total_current_balance > rec.late_request_id.hours_limit:
                    raise UserError(_("Sorry!!,you Exceed  Hours Limit."))

            if rec.period_type == 'days':
                total_current_balance  = rec.employee_current_days + rec.days
                if total_current_balance > rec.late_request_id.days_limit:
                    raise UserError(_("Sorry!!,you Exceed Days Limit."))

    @api.onchange('late_request_id','penalty_id','date_from','date_to')
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
            elif rec.is_business_trip:
                # day_hours = 8
                rec.days = rec.number_of_days

            else:
                rec.hours = rec.days = rec.amount = 0


    @api.depends('employee_id','penalty_id','late_request_id','date','date_from','date_to')
    def get_employee_limit_data(self):
        for rec in self:
            rec.employee_current_hours = rec.employee_current_days = rec.employee_left_hours = rec.employee_left_days = 0
            if rec.employee_id and (rec.penalty_id or rec.is_business_trip) and rec.late_request_id and rec.date:
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
                
                print(".>>>>>>>>>>>>>>>>>>>>>>>prevs_late ",prevs_late)
                if prevs_late:
                    if rec.period_type == 'hours':
                        rec.employee_current_hours = sum([prev.hours for prev in prevs_late])
                        rec.employee_left_hours = rec.late_request_id.hours_limit - rec.employee_current_hours 
                    if rec.period_type == 'days':
                        if not rec.is_business_trip:
                            rec.employee_current_days = sum([prev.days for prev in prevs_late])
                            rec.employee_left_days = rec.late_request_id.days_limit - rec.employee_current_days
                        else:
                            rec.employee_current_days = sum([prev.days for prev in prevs_late]) #rec.number_of_days
                            rec.employee_left_days = rec.late_request_id.days_limit - rec.employee_current_days
                else:
                    if rec.period_type == 'hours':
                        rec.employee_left_hours = rec.late_request_id.hours_limit
                    if rec.period_type == 'days':
                        rec.employee_left_days = rec.late_request_id.days_limit - rec.number_of_days

        return    


    @api.onchange('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                #this section need check
                if rec.duration_in_leave_request == 'no':
                    data = self.env['hr.leave']._get_number_of_days(rec.date_from, rec.date_to, rec.employee_id.id)
                    rec.number_of_days = data['days']
                    if rec.number_of_days:
                        rec.number_of_days = rec.number_of_days + 1
                    
                else:
                    diff_days =  (rec.date_to - rec.date_from ).days
                    rec.number_of_days = diff_days + 1
            else:
                rec.number_of_days = 0