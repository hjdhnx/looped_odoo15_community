# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    max_deduction_percentage = fields.Float()



    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("ext_hr_payroll.max_deduction_percentage",
                                                         self.max_deduction_percentage)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['max_deduction_percentage'] = get_param('ext_hr_payroll.max_deduction_percentage')
        return res
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    max_deduction_percentage = fields.Float()



    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("ext_hr_payroll.max_deduction_percentage",
                                                         self.max_deduction_percentage)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['max_deduction_percentage'] = get_param('ext_hr_payroll.max_deduction_percentage')
        return res
