# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2020-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################


from odoo import models, fields, tools, api, exceptions, _

from datetime import datetime, date, timedelta, time

class HrPublicHoliday(models.Model):
    _name = "hr.public.holiday"
    _inherit = ['mail.thread']
    _description = "hr.public.holiday"
    HOLIDAY_TYPE = [
        ('emp', 'name'),
        ('dep', 'Department'),
        ('tag', 'Tags')

    ]
    type_select = fields.Selection(HOLIDAY_TYPE, "By", default='emp')
    emp_ids = fields.Many2many(comodel_name="hr.employee",
                               relation="employee_ph_rel",
                               column1="employee_ph_col2",
                               column2="attendance_ph_col2",
                               string="Employees", )

    dep_ids = fields.Many2many(comodel_name="hr.department",
                               relation="department_att_ph_rel1",
                               column1="ph_department_col2",
                               column2="att_ph_col3", string="Departments", )
    cat_ids = fields.Many2many(comodel_name="hr.employee.category",
                               relation="category__phrel",
                               column1="cat_col2", column2="ph_col2",
                               string="Tags", )

    name = fields.Char(string="Description",required=True)
    date_from = fields.Date(string="From",required=True)
    date_to = fields.Date(string="To",required=True)
    state = fields.Selection([
        
        ('inactive', 'Draft'),('active', 'Confirmed')], default='inactive',
        track_visibility='onchange',
        string='Status', required=True, index=True, )
    note = fields.Text("Notes")
    duration_in_leave_request = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Include Holiday duration in leave request calculation',
     default='yes',required=1,
     )
    number_of_days = fields.Integer(compute="_compute_number_of_days",store=True)
    # help="Example :You have a national holiday between 05/10/2017 to 09/10/2017 ( 5 days ), an employee requested for a leave between 01/10/2017 and 30/10/2017, if you select yes, leave request duration will be 30 days, if you select no, leave request duration will be 25 days."
    
    @api.depends('date_from', 'date_to','duration_in_leave_request')
    def _compute_number_of_days(self):
        for rec in self:
            rec.number_of_days = 0
            if rec.date_from and rec.date_to:
                #this section need check
                if rec.duration_in_leave_request == 'no':
                    
                    #convert date to datetime
                    date_from = datetime(rec.date_from.year, rec.date_from.month,rec.date_from.day)
                    date_to = datetime(rec.date_to.year, rec.date_to.month,rec.date_to.day)
                    
                    data = rec.env['hr.leave']._get_number_of_days(date_from, date_to, 
                    False
                    # rec.employee_id.id
                    )
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>data ",data)
                    rec.number_of_days = data['days']
                    if rec.number_of_days:
                        rec.number_of_days = rec.number_of_days + 1
                    
                else:
                    diff_days =  (rec.date_to - rec.date_from ).days
                    rec.number_of_days = diff_days + 1
            else:
                rec.number_of_days = 0



    def action_inactive(self):
        for rec in self:
            rec.state = 'inactive'

    def action_active(self):
        for rec in self:
            rec.state = 'active'


    @api.onchange("dep_ids", "cat_ids")
    def get_employee_ids(self):
        emp_ids = []
        if self.type_select == 'dep':
            self.emp_ids = self.env['hr.employee'].search(
                [('department_id.id', 'in', self.dep_ids.ids)])
        elif self.type_select == 'tag':
            for employee in self.env['hr.employee'].search([]):
                list1 = self.cat_ids.ids
                list2 = employee.category_ids.ids
                match = any(map(lambda v: v in list1, list2))
                if match:
                    emp_ids.append(employee.id)
            self.emp_ids = self.env['hr.employee'].search(
                [('id', 'in', emp_ids)])
