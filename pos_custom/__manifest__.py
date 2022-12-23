# -*- coding: utf-8 -*-
{
    'name': "POS Custom",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "E.MUDATHIR",
    'website': "http://www.yourcompany.com ",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'POS',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale','pos_restaurant','pos_retail','pos_hr','branch'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/pos_scrap_reason_views.xml',
        'views/pos_discount_program_views.xml',
        'views/pos_config_views.xml',
        'views/pos_return_reason_views.xml',
        'views/pos_product_notes_views.xml',
        'views/pos_security_views.xml',
        'views/pos_order_type_views.xml',
        'views/pos_driver_views.xml',
        'views/pos_multi_session_view.xml',
        'views/pos_resturant_printer_view.xml',
        # 'views/pos_longpolling_view.xml',
        'views/product_template.xml',
        'views/templates.xml',
        'views/pos_category_view.xml',
        'views/website_sale_category_view.xml',
        'views/pos_order.xml',
        'views/mrp_bom.xml',
        'views/stock_scrap.xml',
        'views/pos_device_views.xml',
        'views/account.xml',
        'data/res_users.xml',
        'data/pos_type_id.xml',
        'data/key_type.xml',

    ],
}
