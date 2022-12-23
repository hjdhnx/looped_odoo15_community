# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.osv import expression


class hrEmployee(models.Model):
    _inherit = "hr.employee"

    late_request_count = fields.Integer(compute='_compute_late_count', string='Requests Count')
    

    def _compute_late_count(self):
        late_request_obj = self.env['late.request']
        for rec in self:
            rec.late_request_count = 0
            count = late_request_obj.search_count([('employee_id', '=', rec.id) ])
            if count:
                rec.late_request_count = count
            