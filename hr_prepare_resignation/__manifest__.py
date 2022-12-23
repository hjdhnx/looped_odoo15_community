# -*- coding: utf-8 -*-
{
    'name': "HR Prepare Resignation",
    'summary': """
        Prepare Resignation""",
    'description': """
        HR Prepare Resignation
    """,
    'author': "Beshoy Wageh",
    'website': "https://www.linkedin.com/in/beshoy-wageh-701ba7116/",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['ext_hr_employee',
    # 'hr_employee_updation',
                'general_manager_group',
                # 'heights_custom_report',
                'hr_custody'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/prepare_resignation_view.xml',
        'views/prepare_clearance_view.xml',
        'views/hr_employee_view.xml',
        'reports/report_resignation_form.xml',
        'reports/report_clearance_form.xml',
        'data/direct_manager_mail.xml',
        'data/hr_manager_mail.xml',
        'data/general_manager_mail.xml',
        'data/employee_mail.xml',
        'data/reject_resignation_mail.xml',
        'data/reject_clearance_mail.xml',
        'data/clearance_direct_manager_mail.xml',
        'data/clearance_it_manager_mail.xml',
        'data/clearance_stock_manager_mail.xml',
        'data/clearance_account_manager_mail.xml',
        'data/clearance_hr_manager_mail.xml',
        'data/clearance_approve_employee_mail.xml',
    ]
}
