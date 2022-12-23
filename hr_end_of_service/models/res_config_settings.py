# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    show_petty_cash = fields.Boolean()
    show_custody = fields.Boolean()

    amount_type = fields.Selection([
                                       ('basic_salary', 'Basic Salary'),
                                       ('total_salary','Total Salary'),
                                       ],default='basic_salary'
                                     )
    months_days = fields.Float(default=30)

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.sudo().env.ref('hr_end_of_service.default_show_petty_cash').value = self.show_petty_cash if  self.show_petty_cash else 0
        self.sudo().env.ref('hr_end_of_service.default_show_custody_eos').value = self.show_custody if  self.show_custody else 0
        self.sudo().env.ref('hr_end_of_service.default_end_of_service_amount_type').value = self.amount_type if  self.amount_type else 'basic_salary'
        self.sudo().env.ref('hr_end_of_service.default_end_of_service_months_days').value = self.months_days if  self.months_days else 30
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        if self.env.ref('hr_end_of_service.default_show_petty_cash').value == '0':
            res['show_petty_cash'] = False 
        else:
            res['show_petty_cash'] = self.env.ref('hr_end_of_service.default_show_petty_cash').value
        
        if self.env.ref('hr_end_of_service.default_show_custody_eos').value == '0':
            res['show_custody'] = False 
        else:
            res['show_custody'] = self.env.ref('hr_end_of_service.default_show_custody_eos').value
        
        res['amount_type'] = self.env.ref('hr_end_of_service.default_end_of_service_amount_type').value

        res['months_days'] = self.env.ref('hr_end_of_service.default_end_of_service_months_days').value
        return res
