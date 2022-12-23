# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

{
    'name': 'Employee Loan Management',
    'version': '13.0.1.0',
    'sequence':1,
    'category': 'Generic Modules/Human Resources',
    'description': """
        odod Apps will add Hr Employee Loan functioality for employee
        
Employee loan management
Odoo employee loan management
HR employee loan
Odoo HR employee loan
HR loan for employee
HR loan approval functionality 
Loan Installment link with employee payslip
Loan notification employee Inbox
Loan Deduction in employee payslip
Manage employee loan 
Manage employee loan odoo
Manage HR loan for employee
Manage HR loan for employee odoo
Loan management 
Odoo loan management
Odoo loan management system
Odoo loan management app
helps you to create customized loan
 module allow HR department to manage loan of employees
Loan Request and Approval
Odoo Loan Report
create different types of loan for employees
allow user to configure loan given to employee will be interest payable or not.
Open HRMS Loan Management
Loan accounting
Odoo loan accounting
Employee can create loan request.
Manage Employee Loan and Integrated with Payroll        
    """,
    'summary':'odoo app will add Hr Employee Loan functioality for employee',
    'depends': ['hr_payroll','hr_payroll_account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/salary_structure.xml',
        'data/ir_sequence_data.xml',
        'views/loan_emi_view.xml',
        'views/hr_employee_view.xml',
        'wizard/loan_reject_reason_view.xml',
        'views/hr_loan_view.xml',
        'views/employee_loan_type_views.xml',
        'report/employee_loan_template.xml',
        'report/report_menu.xml',
        'edi/mail_template.xml',
        'edi/skip_installment_mail_template.xml',
        'views/pay_slip_view.xml',
        'wizard/import_loan_views.xml',
        'wizard/import_logs_view.xml',
        'views/dev_skip_installment.xml',
        'views/hr_loan_dashbord.xml',
        'views/loan_document.xml',
        'views/loan_report_views.xml',
        
    ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # author and support Details =============#
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':59.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
