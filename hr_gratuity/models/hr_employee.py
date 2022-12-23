# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    custom_gratuity_generate = fields.Boolean(
        string='Grauity Generate?',
        default=True
    )
    date_of_join = fields.Date(string="Date of Join", size=14, required=False,readonly=1,related="contract_id.first_effective_notice.start_work")
