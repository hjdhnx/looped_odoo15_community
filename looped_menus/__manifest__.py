# -*- coding: utf-8 -*-
{
    'name': "LOOPED Menus",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "IT-ARM E.Mudathir",
    'website': "http://www.yourcompany.com",


    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'pos_custom','pos_branch','mrp',
    'stock_request','stock_landed_costs',
    'im_livechat','website','hr_attendance',
    'hr_holidays','hr_expense','petty_cash_extention','event','account_accountant',
    'project','link_tracker','calendar','import_bridge_axis','ks_pos_dashboard_ninja','sh_backmate_theme_adv',
    'combo_client','account_budget','qrcode_table','pos_collection'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/pos_views.xml',
        'views/payment_views.xml',
        "views/menu_views.xml",
        'security/menu.xml',

    ],
    
}
