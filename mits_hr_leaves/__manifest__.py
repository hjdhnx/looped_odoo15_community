# -*- coding: utf-8 -*-
{
    'name': "MITS HR Leaves",
    'summary': 'MITS HR Leaves',
    'description': 'MITS HR Leaves',
    'author': "OserGroup",
    'website': "http://www.osergroup.com",
    'category': 'HR',
    'version': '0.1',
    'depends': [
        'base',
        'hr',
        'hr_holidays',
        'ext_hr_employee',
        'ext_hr_contract',
        'basic_hr',
        # 'file_save',
        # 'hr_auth',
    ],

    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/sequence.xml',
        'views/templates.xml',
        'views/exit_rentry.xml',
        'views/leave_request.xml',
        'views/menus.xml',
        'views/views.xml',
        'views/leave_reconciliation.xml',
        'views/national_holiday.xml',
        'views/leave_allocation.xml',
        'wizard/views/early_leave_reconciliation_wizard.xml',
        'wizard/views/late_back_from_leave_wizard.xml',
        'wizard/views/air_ticket_payment_view.xml',
        'data/cron.xml',
        'reports/effective_notice_report.xml',
        'reports/hr_leave_reports.xml',
    ],
    'qweb': [
       
        'static/src/xml/*.xml',
    ],
}
