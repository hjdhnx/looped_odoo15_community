# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, timedelta, datetime

class EmployeePayrollReport(models.AbstractModel):
    _name = 'report.employee_payroll_report.report_employee_payslip'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_language = data['form']['report_language']
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        employee_ids = data['form']['employee_ids']
        department_ids = data['form']['department_ids']
        print("employee_ids", employee_ids)
        print("department_ids", department_ids)
        print("report_language", report_language)
        all_payslips = []
        domain = []
        year = ''
        if employee_ids:
            print("1111")
            domain = [('id', 'in', employee_ids)]
        if department_ids:
            print("2222")
            domain = [('department_id', 'in', department_ids)]
        employee_object = self.env['hr.employee'].search(domain)
        print('employee_object', employee_object)
        if employee_object:
            print("YES employee_object")
            for employee in employee_object:
                payslip = self.env['hr.payslip'].search(
                    [('employee_id', '=', employee.id), ('date_from', '>=', date_from), ('date_to', '<=', date_to),
                     ('state', '=', 'done')])
                print("payslip_object", payslip)
                if payslip:
                    all_payslips.append({'employee_name': payslip.employee_id.name,
                                    'month': payslip.month,
                                    'year': payslip.year,
                                    'name': payslip.name,
                                    'number_of_days': payslip.number_of_days,
                                    'wage': payslip.contract_id.wage,
                                    'phone_allowance_amount': payslip.contract_id.phone_allowance_amount,
                                    'house_allowance_amount': payslip.contract_id.house_allowance_amount,
                                    'food_allowance_amount': payslip.contract_id.food_allowance_amount,
                                    'transportation_allowance_amount': payslip.contract_id.transportation_allowance_amount,
                                    'contract_id': payslip.contract_id})
                    year = payslip.year
                    # currency = payslip.currency_id.name

        now = fields.Date.today()
        nowtime = fields.Datetime.now()
        current_user = self.env.user
        # currency = currency
        year = year
        docargs = {
            'doc_model': 'employee.payroll',
            'date': date.today(),
            'report_language': report_language,
            'all_payslips': all_payslips,
            'year': year,
            'nowtime': nowtime,
            'now': now,
            'current_user': current_user.name,
            # 'currency': currency,
        }
        return docargs
