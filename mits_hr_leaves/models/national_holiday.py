# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _, SUPERUSER_ID
from datetime import datetime


class national_holiday(models.Model):
    _name = "hr.national.holiday"
    _inherit = "mail.thread"

    name = fields.Char('Description')
    code = fields.Char('Code')
    year = fields.Integer(string="Year")
    start_date = fields.Date(string="Holiday Start Date")
    end_date = fields.Date(string="Holiday End Date")
    duration = fields.Integer(string="Holiday Duration",compute="compute_duration")
    duration_in_leave_request = fields.Selection([
        ('yes', 'yes'),
        ('no', 'No'),
    ], string='Include Holiday duration in leave request calculation',
     help="Example :You have a national holiday between 05/10/2017 to 09/10/2017 ( 5 days ), an employee requested for a leave between 01/10/2017 and 30/10/2017, if you select yes, leave request duration will be 30 days, if you select no, leave request duration will be 25 days.")
    notes = fields.Html(string="Notes")
    state = fields.Selection([
        ('New', 'New'),
        ('Confirmed', 'Confirmed'),
    ], string='Status', select=True, default='New', )

    @api.model
    def create(self, vals):
        res = super(national_holiday, self).create(vals)
        res.code = self.env['ir.sequence'].next_by_code('national.holiday')
        
        return res

    @api.depends('start_date','end_date')
    def compute_duration(self):
        for rec in self:
            rec.duration = 0
            if rec.start_date and rec.end_date:
                rec.duration = (rec.end_date - rec.start_date).days

    def action_draft(self):
        for rec in self:
            rec.state = 'New'

    def action_confirm(self):
        for rec in self:
            rec.state = 'Confirmed'