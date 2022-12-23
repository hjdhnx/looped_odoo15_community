# -*- coding: utf-8 -*-
from odoo import fields, api, models, api, _
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError


class pos_wallet_rule_product(models.Model):
    _name = "pos.wallet.rule.product"

    product_id = fields.Many2one('product.product',
                                   string='Product', domain=[('available_in_pos', '=', True)])
    

    order_amount_type = fields.Selection([
        ('fixed', 'By Fixed Amount'),
        ('perc', 'By Percentage'),
        ('quant', 'By Quantity'),
    ], string='Amount Type', default='fixed')
    
    order_amount_type_fixed = fields.Float(string="Every Fixed Amount")
    order_amount_type_quant = fields.Float(string="Every Quantity")
    order_amount_type_fixed_amount = fields.Float(string="Wallet Amount")
    order_amount_type_perc = fields.Float(string="Percentage %")
    wallet_rule_id = fields.Many2one('pos.wallet.rule')

class pos_wallet_rule_pos_category(models.Model):
    _name = "pos.wallet.rule.pos_category"

    pos_category_id = fields.Many2one('pos.category',
                                   string='POS Category')
    

    order_amount_type = fields.Selection([
        ('fixed', 'By Fixed Amount'),
        ('perc', 'By Percentage'),
        ('quant', 'By Quantity'),
    ], string='Amount Type', default='fixed')
    
    order_amount_type_fixed = fields.Float(string="Every Fixed Amount")
    order_amount_type_quant = fields.Float(string="Every Quantity")
    order_amount_type_fixed_amount = fields.Float(string="Wallet Amount")
    order_amount_type_perc = fields.Float(string="Percentage %")
    wallet_rule_id = fields.Many2one('pos.wallet.rule')


class pos_wallet_rule_ecom_category(models.Model):
    _name = "pos.wallet.rule.ecom_category"

    ecom_category_id = fields.Many2one('product.public.category',
                                   string='ECommerce Category')
    

    order_amount_type = fields.Selection([
        ('fixed', 'By Fixed Amount'),
        ('perc', 'By Percentage'),
        ('quant', 'By Quantity'),
    ], string='Amount Type', default='fixed')
    
    order_amount_type_fixed = fields.Float(string="Every Fixed Amount")
    order_amount_type_quant = fields.Float(string="Every Quantity")
    order_amount_type_fixed_amount = fields.Float(string="Wallet Amount")
    order_amount_type_perc = fields.Float(string="Percentage %")
    wallet_rule_id = fields.Many2one('pos.wallet.rule')

class posOrderwWalletLog(models.Model):
    _name = "pos.order.wallet.log"

    order_id = fields.Many2one('pos.order')
    partner_id  = fields.Many2one('res.partner','Customer') 
    amount = fields.Float()
    date = fields.Datetime()
    return_to_wallet = fields.Boolean()
    

class pos_wallet_rule(models.Model):
    _name = "pos.wallet.rule"
    
    _description = "Loyalties rule plus points"

    name = fields.Char('Name', required=1)
    active = fields.Boolean('Active', default=1)
    
    
    type = fields.Selection([
        ('products', 'Products'),
        ('categories', 'POS Categories'),
        ('ecom_categories', 'Ecommerce Categories'),
        ('order_amount', 'Order Totals')
    ], string='Type', required=1, default='products')

    order_amount_type = fields.Selection([
        ('fixed', 'By Fixed Amount'),
        ('perc', 'By Percentage'),
        ('quant', 'By Quantity'),
    ], string='Amount Type', default='fixed')
    
    order_amount_type_fixed = fields.Float(string="Every Fixed Amount")
    order_amount_type_quant = fields.Float(string="Every Total Quantity")
    order_amount_type_fixed_amount = fields.Float(string="Wallet Amount")
    order_amount_type_perc = fields.Float(string="Percentage %")

    # product_ids = fields.Many2many('product.product', 'wallet_rule_product_rel', 'rule_id', 'product_id',
    #                                string='Products', domain=[('available_in_pos', '=', True)])
    product_ids = fields.One2many('pos.wallet.rule.product',
    'wallet_rule_id',string='Products', )
    
    
    # category_ids = fields.Many2many('pos.category', 'wallet_rule_pos_categ_rel', 'rule_id', 'categ_id',
    #                                 string='Categories')
    category_ids = fields.One2many('pos.wallet.rule.pos_category',
    'wallet_rule_id',string='POS Categories', )
    # ecom_category_ids = fields.Many2many('product.public.category', 'wallet_rule_ecom_categ_rel', 'rule_id', 'categ_id',
    #                                 string='Ecommerce Categories')
    ecom_category_ids = fields.One2many('pos.wallet.rule.ecom_category',
     'wallet_rule_id',
                                    string='Ecommerce Categories')
    
    state = fields.Selection([
        ('running', 'Running'),
        ('stop', 'Stop')
    ], string='State', default='running')
    applied_app = fields.Selection([('pos', 'POS'),('delivery', 'Delivery'), ('both', 'Both')], default='pos')
    pos_order_id = fields.Many2one('pos.order')
    amount = fields.Float()

    def get_rule_order_wallet_amount(self,pos_order_id=False):
        for rec in self:
            pos_order = pos_order_id.id if pos_order_id else False #rec.pos_order_id.id
            
            rec.amount = 0
            if not pos_order:
                continue
            order = self.env['pos.order'].browse(pos_order) #pos_order
            if rec.type == 'products':
                wallet_amount_total = 0
                for rule_line in rec.product_ids:
                    order_amount_type = rule_line.wallet_rule_id.order_amount_type
            
                    if order_amount_type == 'quant':
                        qty_total = sum([ line.qty for line in order.lines.filtered(lambda r: r.product_id.id == rule_line.product_id.id)])
                        amount_type_quant = rule_line.order_amount_type_quant

                        get_every_accurance = qty_total/amount_type_quant
                        get_every_accurance = int(get_every_accurance)
                        wallet_amount = get_every_accurance * rule_line.order_amount_type_fixed_amount
                        wallet_amount_total = wallet_amount_total + wallet_amount
                    
                    elif order_amount_type == 'fixed':
                        amount_total = sum([ line.price_subtotal_incl for line in order.lines.filtered(lambda r: r.product_id.id == rule_line.product_id.id)])
                        
                        amount_type_fixed = rule_line.order_amount_type_fixed

                        get_every_accurance = amount_total/amount_type_fixed
                        get_every_accurance = int(get_every_accurance)
                        wallet_amount = get_every_accurance * rule_line.order_amount_type_fixed_amount
                        wallet_amount_total = wallet_amount_total + wallet_amount
                    elif order_amount_type == 'perc':
                        amount_total = sum([ line.price_subtotal_incl for line in order.lines.filtered(lambda r: r.product_id.id == rule_line.product_id.id)])
                        amount_type_perc = rule_line.order_amount_type_perc

                        wallet_amount = amount_total * (amount_type_perc/100)
                        wallet_amount_total = wallet_amount_total + wallet_amount


                    
                    # return wallet_amount
                # print(">>>>>>>>>>>>>>>>>>>>>>>>>>wallet_amount_total ",wallet_amount_total)
                # raise UserError("Wallet Amount is "+str(wallet_amount_total))
                # rec.amount = wallet_amount_total
                return wallet_amount_total

            elif rec.type == 'categories':
                wallet_amount_total = 0
                for rule_line in rec.category_ids:
                    order_amount_type = rule_line.wallet_rule_id.order_amount_type
                    if order_amount_type == 'quant':
                        qty_total = sum([ line.qty for line in order.lines.filtered(lambda r: r.product_id.pos_categ_id.id == rule_line.pos_category_id.id)])
                        amount_type_quant = rule_line.order_amount_type_quant

                        get_every_accurance = qty_total/amount_type_quant
                        get_every_accurance = int(get_every_accurance)
                        wallet_amount = get_every_accurance * rule_line.order_amount_type_fixed_amount
                        wallet_amount_total = wallet_amount_total + wallet_amount
                    
                    elif order_amount_type == 'fixed':
                        amount_total = sum([ line.price_subtotal_incl for line in order.lines.filtered(lambda r: r.product_id.pos_categ_id.id == rule_line.pos_category_id.id)])
                        amount_type_fixed = rule_line.order_amount_type_fixed

                        get_every_accurance = amount_total/amount_type_fixed
                        get_every_accurance = int(get_every_accurance)
                        wallet_amount = get_every_accurance * rule_line.order_amount_type_fixed_amount
                        wallet_amount_total = wallet_amount_total + wallet_amount
                    elif order_amount_type == 'perc':
                        amount_total = sum([ line.price_subtotal_incl for line in order.lines.filtered(lambda r: r.product_id.pos_categ_id.id == rule_line.pos_category_id.id)])
                        amount_type_perc = rule_line.order_amount_type_perc

                        wallet_amount = amount_total * (amount_type_perc/100)
                        wallet_amount_total = wallet_amount_total + wallet_amount
                

                    
                    # return wallet_amount
                # print(">>>>>>>>>>>>>>>>>>>>>>>>>>wallet_amount_total ",wallet_amount_total)
                # raise UserError("Wallet Amount is "+str(wallet_amount_total))
                # rec.amount = wallet_amount_total
                return wallet_amount_total
                #continue with categories and ecommecrece
            elif rec.type == 'ecom_categories':
                wallet_amount_total = 0
                for rule_line in rec.ecom_category_ids:
                    order_amount_type = rule_line.wallet_rule_id.order_amount_type
                    if order_amount_type == 'quant':
                        qty_total = sum([ line.qty for line in order.lines.filtered(lambda r: rule_line.ecom_category_id.id in r.product_id.public_categ_ids.ids )])
                        amount_type_quant = rule_line.order_amount_type_quant

                        get_every_accurance = qty_total/amount_type_quant
                        get_every_accurance = int(get_every_accurance)
                        wallet_amount = get_every_accurance * rule_line.order_amount_type_fixed_amount
                        wallet_amount_total = wallet_amount_total + wallet_amount
                    
                    elif order_amount_type == 'fixed':
                        amount_total = sum([ line.price_subtotal_incl for line in order.lines.filtered(lambda r: rule_line.ecom_category_id.id in r.product_id.public_categ_ids.ids)])
                        amount_type_fixed = rule_line.order_amount_type_fixed

                        get_every_accurance = amount_total/amount_type_fixed
                        get_every_accurance = int(get_every_accurance)
                        wallet_amount = get_every_accurance * rule_line.order_amount_type_fixed_amount
                        wallet_amount_total = wallet_amount_total + wallet_amount
                    elif order_amount_type == 'perc':
                        amount_total = sum([ line.price_subtotal_incl for line in order.lines.filtered(lambda r: rule_line.ecom_category_id.id in r.product_id.public_categ_ids.ids)])
                        amount_type_perc = rule_line.order_amount_type_perc

                        wallet_amount = amount_total * (amount_type_perc/100)
                        wallet_amount_total = wallet_amount_total + wallet_amount
                

                    
                    # return wallet_amount
                # print(">>>>>>>>>>>>>>>>>>>>>>>>>>wallet_amount_total ",wallet_amount_total)
                # raise UserError("Wallet Amount is "+str(wallet_amount_total))
                # rec.amount = wallet_amount_total
                return wallet_amount_total
            elif rec.type == 'order_amount':
                if rec.order_amount_type == 'quant':
                    qty_total = sum([ line.qty for line in order.lines])
                    amount_type_quant = rec.order_amount_type_quant

                    get_every_accurance = qty_total/amount_type_quant
                    get_every_accurance = int(get_every_accurance)
                    wallet_amount = get_every_accurance * rec.order_amount_type_fixed_amount
                    
                    # rec.amount = wallet_amount_total
                    return wallet_amount
                elif rec.order_amount_type == 'fixed':
                    amount_total = sum([ line.price_subtotal_incl for line in order.lines])
                    amount_type_fixed = rec.order_amount_type_fixed

                    get_every_accurance = amount_total/amount_type_fixed
                    get_every_accurance = int(get_every_accurance)
                    wallet_amount = get_every_accurance * rec.order_amount_type_fixed_amount


                    
                    # rec.amount = wallet_amount_total
                    return wallet_amount
                elif rec.order_amount_type == 'perc':
                    amount_total = sum([ line.price_subtotal_incl for line in order.lines])
                    amount_type_perc = rec.order_amount_type_perc

                    wallet_amount = amount_total * (amount_type_perc/100)


                    
                    # raise UserError("Wallet Amount is "+str(wallet_amount))
                    # rec.amount = wallet_amount_total
                    return wallet_amount


