# -*- coding: utf-8 -*-

# from openerp.osv import expression
# from openerp.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    @api.model
    def _get_default_rule_ids(self):
        return [
            # (0, 0, {
            #     'name': _('Basic Salary'),
            #     'sequence': 1,
            #     'code': 'BASIC',
            #     'category_id': self.env.ref('hr_payroll.BASIC').id,
            #     'condition_select': 'none',
            #     'amount_select': 'code',
            #     'amount_python_compute': 'result = payslip.paid_amount',
            # }),
            # (0, 0, {
            #     'name': _('Gross'),
            #     'sequence': 100,
            #     'code': 'GROSS',
            #     'category_id': self.env.ref('hr_payroll.GROSS').id,
            #     'condition_select': 'none',
            #     'amount_select': 'code',
            #     'amount_python_compute': 'result = categories.BASIC + categories.ALW',
            # }),
            (0, 0, {
                'name': _('Net Salary'),
                'sequence': 200,
                'code': 'NET',
                'category_id': self.env.ref('hr_payroll.NET').id,
                'condition_select': 'none',
                'amount_select': 'code',
                'amount_python_compute': 'result = categories.BASIC + categories.ALW + categories.DED',
            }),
        ]
        
    rule_ids = fields.One2many(
        'hr.salary.rule', 'struct_id',
        string='Salary Rules', default=_get_default_rule_ids)


