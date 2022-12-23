# -*- coding: utf-8 -*-

# Part of SANERP Waves. See LICENSE file for full copyright and licensing details.

{
    'name': 'Employee Gratuity Accruals.',
    'version': '13.1.1',
    'price': 60.0,
    'category': 'HRMS and Payroll',
    'license': 'Other proprietary',
    'currency': 'EUR',
    'summary': """This app allow you to generate employee monthly gratuity provision accounting entry.""",
    'description': """
- This module generates gratuity accrual sheets for each employee when run the wizard.
- Gratuity rule as per UAE law.
- Add Journal from Accounting Configuration Journals.
Enter employee joining date.
Create employee running contract.
Create basic salary details on contract.
Run wizard to generate gratuity sheet.
    """,
    'author': 'SANERP Waves',
    'website': 'https://sanerp-waves.odoo.com/',
    'support': 'sanerpwaves@gmail.com',
    'images': [
        'static/description/img1.jpg'
    ],
    'depends': ['mits_hr_leaves'],
    # account_accountant
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_view.xml',
        'views/hr_contract_view.xml',
        'views/account_journal_view.xml',
        'views/mih_auh_gratuity_views.xml',
        'wizard/custom_auh_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
