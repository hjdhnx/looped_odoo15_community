# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api, _


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    loan_request = fields.Integer(string='Loan Request Per Year', default=1, required=True,help="Loan Request", store=True)


# class HrEmployeeBases(models.AbstractModel):
#     _inherit = "hr.employee.base"
#
#     loan_request = fields.Integer(string='Loan Request Per Year')

class hr_employeess(models.Model):
    _inherit = 'hr.employee.public'

#
    loan_request = fields.Integer(string='Loan Request Per Year')
