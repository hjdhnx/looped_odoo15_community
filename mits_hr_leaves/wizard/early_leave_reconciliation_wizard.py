# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api , exceptions



class early_leave_reconciliation_wizard(models.TransientModel):
    _name = "early.leave.reconciliation.wizard"

    choice = fields.Selection([
        ('reallocate', 'Re-allocate annual leave balance for this employee ( if you use leave reconciliation option, your system may create a deduction if the employee received more than his reconciliation, Also payslip may affected by this early return from leave.)'),
        ('no_reallocate', 'Do not re-allocate annual leave balance. include this employee in payslip starting from his return from leave date ( annual leave balance will not increase by early return from leave).'),
    ], string='what is the action you want to do', default='reallocate', )



    #@api.multi
    def apply(self):
        for rec in self:
            effective_notice = self.env['effective.notice'].browse(self._context.get('record_id', False))
            effective_notice.early_leave_reconciliation(rec.choice)


