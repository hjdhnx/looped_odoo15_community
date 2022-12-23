# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Branch Custom',
    'category': 'Hidden',
    'version': '1.0',
    'description': """

""",
    'depends': ['base', 'sale_management', 'purchase', 'stock', 'account', 'purchase_stock','web'],
    # 'auto_install': True,
    'data': [
        'security/branch_security.xml',
        'security/ir.model.access.csv',
        'security/multi_branch.xml',
        'views/inherited_res_users.xml',
        'views/res_branch_view.xml',

        'views/inherited_sale_order.xml',
        'views/inherited_stock_picking.xml',
        'views/inherited_stock_move.xml',
        'views/inherited_account_invoice.xml',
        'views/inherited_purchase_order.xml',
        'views/inherited_stock_warehouse.xml',
        'views/inherited_stock_location.xml',
        'views/inherited_account_bank_statement.xml',
        'wizard/inherited_account_payment.xml',
        # 'views/inherited_stock_inventory.xml',
        'views/inherited_product.xml',
        'views/inherited_partner.xml',
    ],
    'assets': {

        'web.assets_qweb': [
            'branch/static/src/webclient/switch_branch_menu/switch_branch_menu.xml',
        ],
        
        'web.assets_backend': [

            'branch/static/src/legacy/js/views/basic/basic_model.js',
            'branch/static/src/webclient/branch_service.js',
            'branch/static/src/webclient/switch_branch_menu/switch_branch_menu.js',
            


        ],
        
        
  

        
    },
    'license': 'LGPL-3',
}
