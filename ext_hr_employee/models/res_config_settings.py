# -*- coding: utf-8 -*-

from odoo import fields, models


class resCompany(models.Model):
    _inherit = 'res.company'

    # hr_employee_seq_start_with = fields.Integer()

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # resource_calendar_id = fields.Many2one(
    #     'resource.calendar', 'Company Working Hours',
    #     related='company_id.resource_calendar_id', readonly=False)
    
    hr_employee_auto_seq = fields.Boolean(string="Active Employee Auto Sequance",
     config_parameter='ext_hr_employee.hr_employee_auto_seq')

    # hr_employee_seq_start_with = fields.Integer(related="company_id.hr_employee_seq_start_with",
    #   string="Employee Sequance Start at",readonly=False,)
    
    

    # def set_values(self):
    #     print(">>>>>>>>>>>>>>>>>>>>>>>>>>1 ",self.hr_employee_seq_start_with,self.hr_employee_auto_seq)
    #     res = super(ResConfigSettings, self).set_values()
    #     print(">>>>>>>>>>>>>>>>>>>>>>>>>>2 ",self.hr_employee_seq_start_with,self.hr_employee_auto_seq)
    #     self.env.ref('ext_hr_employee.seq_hr_employee_number').number_next_actual = self.hr_employee_seq_start_with
        # return res