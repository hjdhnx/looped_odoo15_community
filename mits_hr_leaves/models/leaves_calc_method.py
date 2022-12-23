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


class hrContract(models.Model):
    _inherit = 'hr.contract'

    leave_policy_applied_ids = fields.Many2many('leaves.calc.method.line')

    last_auto_allocation_date = fields.Date()
    calc_allocation_to_this_date = fields.Date()
    # allocation_ids = fields.Many2many('hr.leave.allocation')
    allocation_ids = fields.One2many('hr.leave.allocation','contract_id')

    @api.model
    def cron_allocation(self):
        contracts = self.env['hr.contract'].search([('state','=','open'),('annual_leave_policy','!=',False)])
        contracts.action_set_auto_allocation()

    def action_set_emp_auto_allocation(self):
        for rec in self:
            if not rec.annual_leave_policy:
                raise exceptions.ValidationError("Please set Leave Policy First")
            for line in rec.annual_leave_policy.lines:
                line.get_employee_allocation(rec)
        return 

    def contract_create_allocation(self,balance,date):
        for rec in self:
            balance = balance
            year = date.year
            leave_type_date ={
                    'name':_('Auto Allocation Employee ')+str(rec.employee_id.name),
                    'employee_id':rec.employee_id.id,
                    'holiday_type':'employee',
                    'holiday_status_id':rec.annual_leave_policy.id,
                    'number_of_days_display':balance,
                    'number_of_days':balance,
                    'year':str(year),
                    'date':date,
                    'allocation_type':'regular',
                    'contract_id':rec.employee_id.contract_id.id,
                    'is_created_auto':True
                }
            allocation = leave_type_allocation = self.env['hr.leave.allocation'].create(leave_type_date)
            allocation.action_validate()
            rec.allocation_ids = [(4, allocation.id)]

    def action_set_auto_allocation(self):
        for rec in self:
            months , policy = rec.annual_leave_policy.get_allocation(rec)
            
            # if policy.id not in rec.leave_policy_applied_ids.ids:

            if months:
                request_reason = False
                if rec.annual_leave_policy.type == 'Annual Leave':
                    request_reason = 'annual'
                leave_type_date ={
                    'name':_('Auto Allocation Employee')+str(rec.employee_id.name),
                    'employee_id':rec.employee_id.id,
                    'holiday_type':'employee',
                    'holiday_status_id':rec.annual_leave_policy.id,
                    'number_of_days_display':months,
                    'number_of_days':months,
                    'allocation_type':'regular',
                    'request_reason':request_reason,
                }
                allocation = leave_type_allocation = self.env['hr.leave.allocation'].create(leave_type_date)
                allocation.action_validate()
                rec.allocation_ids = [(4, allocation.id)]

                allocation_date = datetime.now() #.strftime('%Y-%m-%d')
                allocation_date = datetime.date(allocation_date)
                rec.last_auto_allocation_date = allocation_date
                # rec.write({'leave_policy_applied_ids': [(4, [policy.id])] })                  
                rec.leave_policy_applied_ids = [(4, policy.id)]
                

class hrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    _order = 'date'
    

    months = fields.Integer()
    year = fields.Char()
    date = fields.Date()
    request_reason = fields.Selection([
        ('annual', 'annual leave'),
        ('non-annual', 'Non-annual leave'),
    ], string='Leave request reason')
    contract_id = fields.Many2one('hr.contract')
    used_duration = fields.Integer()
    is_created_auto = fields.Boolean(default=False)
    manual_allocation = fields.Boolean(default=False)

    @api.onchange('employee_id','holiday_status_id','manual_allocation')
    def onchange_set_request_reason(self):
        for rec in self:
            rec.request_reason = False
            if rec.manual_allocation and rec.holiday_status_id and rec.employee_id:
                if rec.holiday_status_id.type == 'Annual Leave':
                    rec.request_reason = 'annual'
                else:
                    rec.request_reason = 'non-annual'
    @api.constrains('manual_allocation','contract_id')
    def check_prev_manual(self):
        for rec in self:
            if rec.manual_allocation:
                prevs = rec.search([('id','!=',rec.id),('contract_id','=',rec.contract_id.id),('manual_allocation','=',True)])
                if prevs:
                    raise exceptions.ValidationError(_("Sorry!!, you can use Manual Allocation once per Contract"))

    @api.onchange('manual_allocation','employee_id')
    def onchange_Set_contract(self):
        for rec in self:
            if rec.manual_allocation and rec.employee_id:
                rec.contract_id = rec.employee_id.contract_id
            else:
                rec.contract_id = False
    def action_validate(self):
        res = super(hrLeaveAllocation,self).action_validate()
        for rec in self:
            if rec.manual_allocation:
                rec.contract_id.last_auto_allocation_date = rec.date
        
        return res

class hrLeaveType(models.Model):
    _inherit = 'hr.leave.type'


    is_required_attachment = fields.Boolean()
    
    def get_allocation(self,contract_id):
        for rec in self:
            contract = contract_id #rec.env['hr.contract'].browse(3) #anita contract #rec.contract_id
            leave_type_id = rec
            if not contract.last_auto_allocation_date:
                if leave_type_id.start_calc_from == "First Effective Notice":
                    start_date_from = contract.start_work
                if leave_type_id.start_calc_from == "Contract Start Date":
                    start_date_from = contract.date_start
                if leave_type_id.start_calc_from == "Trial Period Start Date":
                    start_date_from = contract.trial_date_start
            else:
                start_date_from = contract.last_auto_allocation_date

            end_date_from = datetime.now() #.strftime('%Y-%m-%d')
            end_date_from = datetime.date(end_date_from)
            
            diff = relativedelta(end_date_from, start_date_from)
            diff_in_months = diff.months + diff.years * 12
            

            months = diff_in_months
            # print(">>>>>>>>>>>>>>>>>>>>>.month",months , end_date_from , ' - ',start_date_from ,)
            # raise exceptions.ValidationError(diff_in_months)
            # 1/0

            policy = leave_type_id.lines.filtered(lambda policy:months >= policy.greater_than and months < policy.less_than)
            # print(">>>>>>>>>>>>>>>>>>>>>.Policy Balance",policy.balance , policy.monthly_balance,policy)

            
            return policy.monthly_balance * months ,policy



class calc_method_line(models.Model):
    _name = 'leaves.calc.method.line'

    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type')
    greater_than = fields.Integer(string="Greater Than", default=lambda self: self._default_greater_than(),)
    less_than = fields.Integer(string="Less Than")
    number_of_months = fields.Integer(string="Number Of Months", compute="_compute_number_of_months", store=True)
    calc_method = fields.Selection([('None', 'None'),
                                    ('Fixed Number', 'Fixed Number')], _('Calculation Method'), required=True,
                                     default="Fixed Number")
    balance = fields.Float(string="Balance")
    monthly_balance = fields.Float(string="Monthly Balance", compute="_compute_monthly_balance", store=True)
    notes = fields.Text(string="Notes")
    max_line_less = fields.Integer(related="leave_type_id.max_line_less")



    def _default_greater_than(self):
        leave_type = self.env['hr.leave.type'].search([('id', '=', self.env.context.get('leave_type_id', False))])
        return leave_type.max_line_less

    @api.onchange('less_than')
    def onchange_less_than(self):
        for rec in self:
            leave_type = self.env['hr.leave.type'].search([('id', '=', self.env.context.get('leave_type_id', False))])
            current_rec = self.env['leaves.calc.method.line'].search([('leave_type_id', '=', leave_type.id), ('greater_than', '=', rec.greater_than)])
            if rec.less_than > 0:
                if current_rec:
                    current_rec.write({'less_than': rec.less_than})
                    leave_type.write({'max_line_less': rec.less_than})
                else:
                    rec = rec.create({'leave_type_id': leave_type.id, 'greater_than': rec.greater_than, 'less_than': rec.less_than})
                    leave_type.write({'max_line_less': rec.less_than})

    #@api.multi
    def unlink(self):
        for rec in self:
            next_calc_line = self.env['leaves.calc.method.line'].search([('greater_than', '=', rec.less_than), ('leave_type_id', '=', rec.leave_type_id.id)])
            if next_calc_line and not self.env.context.get('on_create', False):
                raise exceptions.ValidationError(_("Please Delete The Last Line First"))
            record_id = rec.leave_type_id.id
            leave_type = rec.leave_type_id
            res = super(calc_method_line, self).unlink()
            last_line = self.env['leaves.calc.method.line'].search([('leave_type_id', '=', record_id)], order="less_than desc", limit=1)
            if last_line:
                leave_type.max_line_less = last_line.less_than
            else:
                leave_type.max_line_less = 0
        return res

    @api.model
    def create(self, vals):
        same_record = self.env['leaves.calc.method.line'].search([('leave_type_id', '=', vals['leave_type_id']), ('greater_than', '=', vals['greater_than'])])
        if same_record:
            same_record.with_context({'on_create': True}).unlink()
        res = super(calc_method_line, self).create(vals)
        last_line = self.env['leaves.calc.method.line'].search([('leave_type_id', '=', vals['leave_type_id'])], order="less_than desc", limit=1)
        if last_line:
            last_line.leave_type_id.max_line_less = last_line.less_than
        return res

    @api.depends('greater_than', 'less_than')
    def _compute_number_of_months(self):
        for rec in self:
            rec.number_of_months = rec.less_than - rec.greater_than

    @api.onchange('calc_method')
    def onchange_balance(self):
        for rec in self:
            if rec.calc_method == "None":
                rec.balance = 0

    @api.constrains('balance')
    def _check_balance(self):
        if self.balance <= 0 and self.calc_method == "Fixed Number":
            raise exceptions.ValidationError("Balance Must be Positive number")

    @api.depends('balance')
    def _compute_monthly_balance(self):
        for rec in self:
            if rec.number_of_months == 0 or not rec.leave_type_id.months_in_year:
                rec.monthly_balance = 0
            else:
                mb = rec.balance / rec.leave_type_id.months_in_year
                rec.monthly_balance = round(mb, 2)

    @api.constrains('greater_than', 'less_than')
    def _check_greater_than(self):
        if self.greater_than >= self.less_than:
            raise exceptions.ValidationError("Configuration error!! The value in (less than) should be greater than the value in (greater than)")




    def get_employee_allocation(self,contract_id):
        for rec in self:
            contract = contract_id #rec.env['hr.contract'].browse(3) #anita contract #rec.contract_id
            leave_type_line_id = rec
            leave_type_id = rec.leave_type_id

            all_period_start_date = False
            all_period_end_date = False

            # if not contract.last_auto_allocation_date:
            if leave_type_id.start_calc_from == "First Effective Notice":
                start_date_from = contract.start_work
                all_period_start_date = contract.start_work
            if leave_type_id.start_calc_from == "Contract Start Date":
                start_date_from = contract.date_start
                all_period_start_date = contract.date_start
            if leave_type_id.start_calc_from == "Trial Period Start Date":
                start_date_from = contract.trial_date_start
                all_period_start_date = contract.trial_date_start
            # else:
            # start_date_from = contract.last_auto_allocation_date
            # contract.calc_allocation_to_this_date 
            #get first date of the current month
            date_time_now_end  = datetime.date(datetime.now()) 
            date_time_now_end = date_time_now_end - relativedelta(days=date_time_now_end.day-1)
            # print(">>>>>>>>>>>>>>>>>>>>>>>date_time_now_end ",date_time_now_end)
            # raise exceptions.ValidationError(str(date_time_now_end ))
            # end_date_from = #datetime.now() 
            end_date_from = date_time_now_end #datetime.date(end_date_from)

            # all_period_end_date = datetime.date(datetime.now())
            all_period_end_date = date_time_now_end #datetime.date(datetime.now())

            #all_peride diff in month
            all_period_diff = relativedelta(all_period_end_date, all_period_start_date)
            all_period_diff_in_months = all_period_diff.months + all_period_diff.years * 12

            all_period_months = all_period_diff_in_months

            # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>",rec.id , " - ",all_period_months)


            
            if all_period_months >= leave_type_line_id.greater_than and all_period_months < leave_type_line_id.less_than:
                    
                if contract.last_auto_allocation_date:
                    all_period_start_date = contract.last_auto_allocation_date
                    all_period_diff = relativedelta(all_period_end_date, all_period_start_date)
                    all_period_diff_in_months = all_period_diff.months + all_period_diff.years * 12

                    all_period_months = all_period_diff_in_months
                

                # if rec.id == 29:
                #     raise exceptions.ValidationError(str(all_period_months )+" | "+str(all_period_months)+" | "+str(contract.last_auto_allocation_date))
                
                
                
                
                balance = leave_type_line_id.monthly_balance * all_period_months 
                if balance:
                    # return
                    #set allocation in contract
                    # contract.contract_create_allocation(balance,datetime.now().year)
                    # contract.last_auto_allocation_date = datetime.now()

                    contract.contract_create_allocation(balance,date_time_now_end)
                    contract.last_auto_allocation_date = date_time_now_end


                    # raise exceptions.ValidationError(str(balance)+" | "+str(all_period_months))
                    # print(">>>>>>>>>>>>>>>>>balance ",balance,all_period_months,)
            #if calculated monthes more then less than then check 
            if all_period_months > leave_type_line_id.less_than:
            
                start_date_from = start_date_from 
                #get full peride excatly
                end_date_from = start_date_from + relativedelta(months=leave_type_line_id.less_than)
                #after get full periode in case previus allocation set it as start date
                if contract.last_auto_allocation_date:
                    start_date_from = contract.last_auto_allocation_date
                # end_date_from = 
                #calculate diffrence in month
                all_period_start_date = start_date_from
                all_period_end_date = end_date_from
                all_period_diff = relativedelta(all_period_end_date, all_period_start_date)
                all_period_diff_in_months = all_period_diff.months + all_period_diff.years * 12

                all_period_months = all_period_diff_in_months
                #in case calculated months in mines then no balance and return
                if all_period_months >= 0:
                    # return
                    balance = leave_type_line_id.monthly_balance * all_period_months 
                    contract.contract_create_allocation(balance,all_period_end_date)
                    contract.last_auto_allocation_date = all_period_end_date
                # raise exceptions.ValidationError("2 |"+str(all_period_months))

            
            # 1/0
            
            # return
