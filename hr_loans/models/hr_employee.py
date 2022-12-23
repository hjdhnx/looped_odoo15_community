# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.osv import expression


class hrEmployee(models.Model):
    _inherit = "hr.employee"

    employee_reward_count = fields.Integer(compute='_compute_hr_employee_rewards', string='Rewards Count')
    

    def _compute_hr_employee_rewards(self):
        employee_reward_obj = self.env['hr.employee.rewards']
        for rec in self:
            rec.employee_reward_count = 0
            count = employee_reward_obj.search_count([('employee_id', '=', rec.id) ])
            if count:
                rec.employee_reward_count = count
            