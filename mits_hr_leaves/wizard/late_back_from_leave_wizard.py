# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api , exceptions



class late_back_from_leave_wizard(models.TransientModel):
    _name = "late.back.from.leave.wizard"

    message = fields.Text(string="Message")
    choice = fields.Selection([
        ('deduct', 'Deduct late days from employee annual leave balance? this may cause a negative  annual leave balance.'),
        ('extend', 'Extend this leave with another leave?'),
        ('absent', 'Consider that the employee is absent and create a deduction?'),
    ], string='what is the action you want to do', default='deduct', )



    #@api.multi
    def confirm(self):
        for rec in self:
            effective_notice = self.env['effective.notice'].browse(self._context.get('record_id', False))
            return effective_notice.late_back_from_leave(rec.choice)


