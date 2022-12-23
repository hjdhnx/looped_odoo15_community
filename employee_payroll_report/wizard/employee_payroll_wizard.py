# -*- coding: utf-8 -*-

from odoo import api, fields, models


class EmployeePayrollReportWizard(models.TransientModel):
    _name = "employee.payroll"
    _description = "Employee Payroll Report wizard"

    report_language = fields.Selection([
        ('en', 'English'),
        ('ar', 'Arabic'),
    ], string='Language', required=True)

    report_type = fields.Selection([('employees', 'Pick Employees'), ('departments', 'Departments'), ],
                                   string='Report Type', required=True)

    date_from = fields.Date(string="Date From", required=True, )
    date_to = fields.Date(string="Date To", required=True, )

    employee_ids = fields.Many2many('hr.employee', string='Employees')
    department_ids = fields.Many2many('hr.department', string='Departments')

    hide_basic_salary = fields.Boolean(string="Hide Basic Salary If Zero",  )

    def check_report(self):
        data = {}
        data['form'] = self.read(
            ['report_language', 'report_type', 'date_from', 'date_to', 'employee_ids', 'department_ids',
             'hide_basic_salary'])[0]
        return self.env.ref('employee_payroll_report.action_report_employee_payslip_pdf').report_action(self, data=data, config=False)



