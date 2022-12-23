# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime, time, timedelta
from odoo.fields import Date, Datetime
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class hrOtherRequest(models.Model):
    _name = 'hr.other.request'
    _inherit = 'mail.thread'
    _description = 'HR Other Request'

    name = fields.Char(default='/',copy=False)
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False,default=lambda self:self.env.user.employee_id.id , track_visibility='onchange')
    
    
    date = fields.Date(string="Date", required=False, default=date.today(), track_visibility='onchange')

    state = fields.Selection(string="state",
                             selection=[('draft', 'Draft'), ('confirm', 'Confirmed'), ('approve', 'Approved'),('refuse','Refuse') ],
                             required=False, default='draft', track_visibility='onchange')
    department_id = fields.Many2one('hr.department',related="employee_id.department_id",readonly=1)
    job_id = fields.Many2one('hr.job',related="employee_id.job_id",readonly=1)
    manager_id = fields.Many2one('hr.employee',related="employee_id.department_id.manager_id",readonly=1)
    employee_number = fields.Char('Number',related='employee_id.employee_number',readonly=1)
    request_details = fields.Text( required=False, track_visibility='onchange')
    
    hr_manager_notes = fields.Char( track_visibility='onchange')

        

                
    def action_submit(self):
        for rec in self:
            rec.state = 'confirm'

    def action_draft(self):
        for rec in self:
            rec.hr_manager_notes = False
            rec.state = 'draft'

    def action_refuse(self):
        for rec in self:
            if not rec.hr_manager_notes:
                raise UserError(_("Sorry!!,Please Fill HR Manager Notes First."))
            rec.state = 'refuse'

    def action_approve(self):
        # self.penalty_id.action_cancel()
        for rec in self:
            
            rec.state = 'approve'


    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(self._name) or '/'
        return super(hrOtherRequest, self).create(vals)
        
