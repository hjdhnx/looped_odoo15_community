# -*- coding: utf-8 -*-
from odoo import fields, api, models, api, _
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError


class pos_loyalty_category(models.Model):
    _name = "pos.loyalty.category"
    _description = "Customer loyalty type"

    name = fields.Char('Name', required=1)
    code = fields.Char('Code', required=1)
    active = fields.Boolean('Active', default=1)
    from_point = fields.Float('Point From', required=1)
    to_point = fields.Float('Point To', required=1)


class pos_loyalty(models.Model):
    _name = "pos.loyalty"
    _description = "Loyalties Program, on this object we define loyalty program, included rules of plus points and rules of redeem points"

    name = fields.Char('Loyalty Name', required=1)
    rule_ids = fields.One2many(
        'pos.loyalty.rule', 'loyalty_id', 'Rules', help='Rules for plus points to customer')
    reward_ids = fields.One2many(
        'pos.loyalty.reward', 'loyalty_id', 'Rewards',
        help='Rules for redeem points when customer use points on order')
    state = fields.Selection([
        ('running', 'Running'),
        ('stop', 'Stop')
    ], string='State', default='running')
    product_loyalty_id = fields.Many2one(
        'product.product',
        string='Product Reward Service',
        help='When you add Reward to cart, this product use for add to cart with price reward amount',
        domain=[('available_in_pos', '=', True)],
        required=1)
    rounding = fields.Float(
        string='Rounding Points', default=1,
        help="This is rounding ratio for rounding plus points \n"
             "when customer purchase products, compute like rounding of currency")
    rounding_down = fields.Boolean(
        string='Rounding Down Total', default=0,
        help="Rounding down total points plus, example when customer purchase order,\n"
             "Total points plus is 7,9 pos will rounding to 7 points, and if 7,1 points become to 7")
    config_ids = fields.One2many('pos.config', 'pos_loyalty_id', string='Pos Setting Applied')
    period_expired = fields.Integer(
        'Period Time Expired (day)',
        required=1,
        help='All points coming from this program will expired if out of date this period days. \n'
             'Example: You set is 30 days, any plus points will have life times is 30 days\n'
             'And out of 30 days, points auto expired and reduce points of customer',
        default=30)
    branch_ids = fields.Many2many('res.branch')

    @api.model
    def create(self, vals):
        if vals.get('period_expired', None) and vals.get('period_expired', None) <= 0:
            raise UserError(
                'You can not set period expired days of points smaller than or equal 0. Please set bigger than 0')
        return super(pos_loyalty, self).create(vals)

    def write(self, vals):
        if vals.get('period_expired', None) and vals.get('period_expired', None) <= 0:
            raise UserError(
                'You can not set period expired days of points smaller than or equal 0. Please set bigger than 0')
        return super(pos_loyalty, self).write(vals)

    @api.model
    def default_get(self, default_fields):
        res = super(pos_loyalty, self).default_get(default_fields)
        products = self.env['product.product'].search([('default_code', '=', 'Rs')])
        if products:
            res.update({'product_loyalty_id': products[0].id})
        return res

    def active_all_pos(self):
        configs = self.env['pos.config'].search([])
        for loyalty in self:
            if loyalty.state == 'running':
                configs.write({'pos_loyalty_id': loyalty.id})
            else:
                raise UserError('Loyalty program required state is running')
        return True

class pos_loyalty_rule_product(models.Model):
    _name = "pos.loyalty.rule.product"

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
    loyalty_rule_id = fields.Many2one('pos.loyalty.rule')

class pos_loyalty_rule_pos_category(models.Model):
    _name = "pos.loyalty.rule.pos_category"

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
    loyalty_rule_id = fields.Many2one('pos.loyalty.rule')


class pos_loyalty_rule_ecom_category(models.Model):
    _name = "pos.loyalty.rule.ecom_category"

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
    loyalty_rule_id = fields.Many2one('pos.loyalty.rule')


class pos_loyalty_rule(models.Model):
    _name = "pos.loyalty.rule"
    _rec_name = 'loyalty_id'
    _description = "Loyalties rule plus points"

    name = fields.Char('Name', required=1)
    active = fields.Boolean('Active', default=1)
    loyalty_id = fields.Many2one('pos.loyalty', 'Loyalty', required=1)
    coefficient = fields.Float('Coefficient ratio', required=1,
                               help=' 10    USD covert to 1 point input value is 0.1,\n'
                                    ' 100   USD covert to 1 point input value is 0.01\n'
                                    ' 1000  USD covert to 1 point input value is 0.001.',
                               default=1, digits=(16, 6))
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

    # product_ids = fields.Many2many('product.product', 'loyalty_rule_product_rel', 'rule_id', 'product_id',
    #                                string='Products', domain=[('available_in_pos', '=', True)])
    product_ids = fields.One2many('pos.loyalty.rule.product',
    'loyalty_rule_id',string='Products', )
    
    
    # category_ids = fields.Many2many('pos.category', 'loyalty_rule_pos_categ_rel', 'rule_id', 'categ_id',
    #                                 string='Categories')
    category_ids = fields.One2many('pos.loyalty.rule.pos_category',
    'loyalty_rule_id',string='POS Categories', )
    # ecom_category_ids = fields.Many2many('product.public.category', 'loyalty_rule_ecom_categ_rel', 'rule_id', 'categ_id',
    #                                 string='Ecommerce Categories')
    ecom_category_ids = fields.One2many('pos.loyalty.rule.ecom_category',
     'loyalty_rule_id',
                                    string='Ecommerce Categories')
    
    min_amount = fields.Float('Min amount', required=0, help='This condition min amount of order can apply rule')
    coefficient_note = fields.Text(compute='_get_coefficient_note', string='Coefficient note')
    state = fields.Selection([
        ('running', 'Running'),
        ('stop', 'Stop')
    ], string='State', default='running')

    def get_rule_order_wallet_amount(self,pos_order=1):
        for rec in self:
            
            order = self.env['pos.order'].browse(pos_order) #pos_order
            if rec.type == 'products':
                wallet_amount_total = 0
                for rule_line in rec.product_ids:
                    if rule_line.order_amount_type == 'quant':
                        qty_total = sum([ line.qty for line in order.lines.filtered(lambda r: r.product_id.id == rule_line.product_id.id)])
                        amount_type_quant = rule_line.order_amount_type_quant

                        get_every_accurance = qty_total/amount_type_quant
                        get_every_accurance = int(get_every_accurance)
                        wallet_amount = get_every_accurance * rule_line.order_amount_type_fixed_amount
                        wallet_amount_total = wallet_amount_total + wallet_amount
                    
                    elif rule_line.order_amount_type == 'fixed':
                        amount_total = sum([ line.price_subtotal_incl for line in order.lines.filtered(lambda r: r.product_id.id == rule_line.product_id.id)])
                        amount_type_fixed = rule_line.order_amount_type_fixed

                        get_every_accurance = amount_total/amount_type_fixed
                        get_every_accurance = int(get_every_accurance)
                        wallet_amount = get_every_accurance * rule_line.order_amount_type_fixed_amount
                        wallet_amount_total = wallet_amount_total + wallet_amount
                    elif rule_line.order_amount_type == 'perc':
                        amount_total = sum([ line.price_subtotal_incl for line in order.lines.filtered(lambda r: r.product_id.id == rule_line.product_id.id)])
                        amount_type_perc = rule_line.order_amount_type_perc

                        wallet_amount = amount_total * (amount_type_perc/100)
                        wallet_amount_total = wallet_amount_total + wallet_amount


                    
                    # return wallet_amount
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>wallet_amount_total ",wallet_amount_total)

                return wallet_amount_total

            elif rec.type == 'categories':
                wallet_amount_total = 0
                for rule_line in rec.category_ids:
                    if rule_line.order_amount_type == 'quant':
                        qty_total = sum([ line.qty for line in order.lines.filtered(lambda r: r.product_id.pos_categ_id.id == rule_line.pos_category_id.id)])
                        amount_type_quant = rule_line.order_amount_type_quant

                        get_every_accurance = qty_total/amount_type_quant
                        get_every_accurance = int(get_every_accurance)
                        wallet_amount = get_every_accurance * rule_line.order_amount_type_fixed_amount
                        wallet_amount_total = wallet_amount_total + wallet_amount
                    
                    elif rule_line.order_amount_type == 'fixed':
                        amount_total = sum([ line.price_subtotal_incl for line in order.lines.filtered(lambda r: r.product_id.pos_categ_id.id == rule_line.pos_category_id.id)])
                        amount_type_fixed = rule_line.order_amount_type_fixed

                        get_every_accurance = amount_total/amount_type_fixed
                        get_every_accurance = int(get_every_accurance)
                        wallet_amount = get_every_accurance * rule_line.order_amount_type_fixed_amount
                        wallet_amount_total = wallet_amount_total + wallet_amount
                    elif rule_line.order_amount_type == 'perc':
                        amount_total = sum([ line.price_subtotal_incl for line in order.lines.filtered(lambda r: r.product_id.pos_categ_id.id == rule_line.pos_category_id.id)])
                        amount_type_perc = rule_line.order_amount_type_perc

                        wallet_amount = amount_total * (amount_type_perc/100)
                        wallet_amount_total = wallet_amount_total + wallet_amount
                

                    
                    # return wallet_amount
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>wallet_amount_total ",wallet_amount_total)

                return wallet_amount_total
                #continue with categories and ecommecrece
            elif rec.type == 'ecom_categories':
                wallet_amount_total = 0
                for rule_line in rec.ecom_category_ids:
                    if rule_line.order_amount_type == 'quant':
                        qty_total = sum([ line.qty for line in order.lines.filtered(lambda r: rule_line.ecom_category_id.id in r.product_id.public_categ_ids.ids )])
                        amount_type_quant = rule_line.order_amount_type_quant

                        get_every_accurance = qty_total/amount_type_quant
                        get_every_accurance = int(get_every_accurance)
                        wallet_amount = get_every_accurance * rule_line.order_amount_type_fixed_amount
                        wallet_amount_total = wallet_amount_total + wallet_amount
                    
                    elif rule_line.order_amount_type == 'fixed':
                        amount_total = sum([ line.price_subtotal_incl for line in order.lines.filtered(lambda r: rule_line.ecom_category_id.id in r.product_id.public_categ_ids.ids)])
                        amount_type_fixed = rule_line.order_amount_type_fixed

                        get_every_accurance = amount_total/amount_type_fixed
                        get_every_accurance = int(get_every_accurance)
                        wallet_amount = get_every_accurance * rule_line.order_amount_type_fixed_amount
                        wallet_amount_total = wallet_amount_total + wallet_amount
                    elif rule_line.order_amount_type == 'perc':
                        amount_total = sum([ line.price_subtotal_incl for line in order.lines.filtered(lambda r: rule_line.ecom_category_id.id in r.product_id.public_categ_ids.ids)])
                        amount_type_perc = rule_line.order_amount_type_perc

                        wallet_amount = amount_total * (amount_type_perc/100)
                        wallet_amount_total = wallet_amount_total + wallet_amount
                

                    
                    # return wallet_amount
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>wallet_amount_total ",wallet_amount_total)

                return wallet_amount_total
            elif rec.type == 'order_amount':
                if rec.order_amount_type == 'quant':
                    qty_total = sum([ line.qty for line in order.lines])
                    amount_type_quant = rec.order_amount_type_quant

                    get_every_accurance = qty_total/amount_type_quant
                    get_every_accurance = int(get_every_accurance)
                    wallet_amount = get_every_accurance * rec.order_amount_type_fixed_amount
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>wallet_amount ",wallet_amount)
                    return wallet_amount
                elif rec.order_amount_type == 'fixed':
                    amount_total = sum([ line.price_subtotal_incl for line in order.lines])
                    amount_type_fixed = rec.order_amount_type_fixed

                    get_every_accurance = amount_total/amount_type_fixed
                    get_every_accurance = int(get_every_accurance)
                    wallet_amount = get_every_accurance * rec.order_amount_type_fixed_amount


                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>wallet_amount ",wallet_amount)

                    return wallet_amount
                elif rec.order_amount_type == 'perc':
                    amount_total = sum([ line.price_subtotal_incl for line in order.lines])
                    amount_type_perc = rec.order_amount_type_perc

                    wallet_amount = amount_total * (amount_type_perc/100)


                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>wallet_amount ",wallet_amount)

                    return wallet_amount



    @api.model
    def create(self, vals):
        if vals.get('coefficient', None) and vals.get('coefficient', None) <= 0:
            raise UserError(
                'You can not set Coefficient smaller than or equal 0. Please set bigger than 0')
        return super(pos_loyalty_rule, self).create(vals)

    def write(self, vals):
        if vals.get('coefficient', None) and vals.get('coefficient', None) <= 0:
            raise UserError(
                'You can not set Coefficient smaller than or equal 0. Please set bigger than 0')
        return super(pos_loyalty_rule, self).write(vals)

    def _get_coefficient_note(self):
        for rule in self:
            rule.coefficient_note = '1 %s will cover to %s point and with condition total amount order bigger than [Min Amount] %s' % (
                self.env.user.company_id.currency_id.name, rule.coefficient, rule.min_amount)


class pos_loyalty_reward(models.Model):
    _name = "pos.loyalty.reward"
    _description = "Loyalties rule redeem points"

    name = fields.Char('Name', required=1)
    active = fields.Boolean('Active', default=1)
    loyalty_id = fields.Many2one('pos.loyalty', 'Loyalty', required=1)
    redeem_point = fields.Float('Redeem Point', help='This is total point get from customer when cashier Reward')
    type = fields.Selection([
        ('discount_products', 'Discount Products'),
        ('discount_categories', "Discount Categories"),
        ('gift', 'Free Gift'),
        ('resale', "Sale off get a points"),
        ('use_point_payment', "Use points payment one part of order amount total"),
    ], string='Type of Reward', required=1, help="""
        Discount Products: Will discount list products filter by products\n
        Discount categories: Will discount products filter by categories \n
        Gift: Will free gift products to customers \n
        Sale off got point : sale off list products and get points from customers \n
        Use point payment : covert point to discount price \n
    """)
    coefficient = fields.Float('Coefficient Ratio', required=1,
                               help=' 1     point  covert to 1 USD input value is 1,\n'
                                    ' 10    points covert to 1 USD input value is 0.1\n'
                                    ' 1000  points cover to 1 USD input value is 0.001.',
                               default=1, digits=(16, 6))
    discount = fields.Float('Discount %', required=1, help='Discount %')
    discount_product_ids = fields.Many2many('product.product', 'reward_product_rel', 'reward_id', 'product_id',
                                            string='Products', domain=[('available_in_pos', '=', True)])
    discount_category_ids = fields.Many2many('pos.category', 'reward_pos_categ_rel', 'reward_id', 'categ_id',
                                             string='POS Categories')
    min_amount = fields.Float('Min Amount', required=1,
                              help='Required Amount Total of Order bigger than or equal for apply this Reward')
    gift_product_ids = fields.Many2many('product.product', 'reward_gift_product_product_rel', 'reward_id',
                                        'gift_product_id',
                                        string='Gift Products', domain=[('available_in_pos', '=', True)])
    resale_product_ids = fields.Many2many('product.product', 'reward_resale_product_product_rel', 'reward_id',
                                          'resale_product_id',
                                          string='Resale Products', domain=[('available_in_pos', '=', True)])
    gift_quantity = fields.Float('Gift Quantity', default=1)
    price_resale = fields.Float('Price of resale')
    coefficient_note = fields.Text(compute='_get_coefficient_note', string='Coefficient note')
    state = fields.Selection([
        ('running', 'Running'),
        ('stop', 'Stop')
    ], string='State', default='running')
    line_ids = fields.One2many('pos.order.line', 'reward_id', 'POS order lines')

    @api.model
    def create(self, vals):
        if vals.get('coefficient', None) and vals.get('coefficient', None) <= 0:
            raise UserError(
                'You can not set Coefficient smaller than or equal 0. Please set bigger than 0')
        return super(pos_loyalty_reward, self).create(vals)

    def write(self, vals):
        if vals.get('coefficient', None) and vals.get('coefficient', None) <= 0:
            raise UserError(
                'You can not set Coefficient smaller than or equal 0. Please set bigger than 0')
        return super(pos_loyalty_reward, self).write(vals)

    def _get_coefficient_note(self):
        for rule in self:
            if rule.type != 'gift':
                rule.coefficient_note = '1 point will cover to %s %s with condition min amount total order bigger than: %s' % (
                    rule.coefficient, self.env.user.company_id.currency_id.name, rule.min_amount)
            else:
                rule.coefficient_note = '%s (points) will give 1 quantity of each product bellow' % (rule.coefficient)


class PosLoyaltyPoint(models.Model):
    _name = "pos.loyalty.point"
    _rec_name = 'partner_id'
    _description = "Model Management all points pluus or redeem of customer"

    create_uid = fields.Many2one('res.users', string='Create by', readonly=1)
    is_return = fields.Boolean('Is Return', readonly=1)
    create_date = fields.Datetime('Create Date', readonly=1)
    loyalty_id = fields.Many2one('pos.loyalty', 'Loyalty Program')
    order_id = fields.Many2one('pos.order', 'Order', index=1, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', 'Customer', required=1, index=1)
    end_date = fields.Datetime('Expired Date')
    point = fields.Float('Point')
    type = fields.Selection([
        ('import', 'Manual import'),
        ('plus', 'Plus'),
        ('redeem', 'Redeem')
    ], string='Type', default='import', required=1)
    state = fields.Selection([
        ('ready', 'Ready to use'),
        ('expired', 'Expired Period Times')
    ], string='State', default='ready')

    @api.model
    def create(self, vals):
        loyalty_program = self.env['pos.loyalty'].browse(vals.get('loyalty_id'))
        if loyalty_program.period_expired >= 0:
            end_date = fields.Datetime.now() + timedelta(days=loyalty_program.period_expired)
            vals.update({'end_date': end_date})
        loyalty_point = super(PosLoyaltyPoint, self).create(vals)
        return loyalty_point

    def cron_expired_points(self):
        loyalty_points = self.search([('end_date', '<=', fields.Datetime.now()), ('type', 'in', ['plus', 'import'])])
        if loyalty_points:
            loyalty_points.write({'state': 'expired'})
        return True

    def set_expired(self):
        return self.write({'state': 'expired'})

    def set_ready(self):
        return self.write({'state': 'ready'})