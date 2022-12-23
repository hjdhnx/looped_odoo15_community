from odoo import models, fields, api

class posOrderType(models.Model):
    _name = 'pos.order_type'

    name = fields.Char(required=1)
    is_show_customer_info = fields.Boolean('Show Customer info')
    is_require_information = fields.Boolean('Require Information')
    is_require_driver = fields.Boolean('Require Driver')
    is_auto_open_table_screen = fields.Boolean('Auto Open Table Screen')
    pricelist_id = fields.Many2one('product.pricelist',required=1)
    account_journal_ids = fields.Many2many('account.journal')
    payment_method_ids = fields.Many2many('pos.payment.method')
    type = fields.Selection([('dine_in','Dine In'),('delivary','Delivary'),('take_away','Take Away'),('extra','Extra')])
    delivary_product_id = fields.Many2one('product.product')
    extra_product_id = fields.Many2one('product.product')
    extra_percentage = fields.Float()
    company_id = fields.Many2one('res.company',default=lambda self:self.env.user.company_id.id)
    customer_id = fields.Many2one('res.partner',)
    tax_ids = fields.Many2many('account.tax', string='Taxes',)
    arbic_name = fields.Char('')
    category_order_type_id = fields.Many2one(comodel_name="category.order.type", string="Category Order Type", required=False, )
