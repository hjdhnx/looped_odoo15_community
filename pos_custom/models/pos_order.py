# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosCloseSessionWizard(models.TransientModel):
    _inherit = "pos.close.session.wizard"
    _description = "Close Session Wizard"

    

    session_id = fields.Many2one('pos.session')

    def close_session_pos(self):
        session = self.session_id
        return session.action_pos_session_closing_control(
            self.account_id, self.amount_to_balance
        )

class posPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    image_1920 = fields.Binary()

    
class posPayment(models.Model):
    _inherit = 'pos.payment'

    payment_time = fields.Datetime()

class TrackingOrders(models.Model):
    _name = 'tracking.orders'

    order_id = fields.Many2one('pos.order')
    session_id = fields.Many2one('pos.session')
    pos_config_id = fields.Many2one('pos.config')
    user_id = fields.Many2one('res.users')

class StreamingOrder(models.Model):
    _name = 'streaming.order'

    name = fields.Char()

class posOrderLineDelete(models.Model):
    _name = 'pos.order.line_delete'
    product_id = fields.Many2one('product.product')
    price = fields.Float()
    quantity = fields.Integer()
    order_id = fields.Many2one('pos.order')

class posOrder(models.Model):
    _inherit = 'pos.order'

    order_type_id = fields.Many2one('pos.order_type','Order Type')
    return_reason_id = fields.Many2one('pos.return_reason','Return Reason')
    return_order_id = fields.Many2one('pos.order')

    discount_type_id = fields.Many2one('pos.discount_program','Discount Type')
    driver_id = fields.Many2one('pos.driver','Driver')
    mobile_ref = fields.Char('POS Order Ref')
    commission = fields.Float('', compute='_compute_commission',)
    commission_after_tax = fields.Float('', compute='_compute_commission',)
    state = fields.Selection(
        [('draft', 'New'), ('send_to_kitchen', 'Send to Kitchen'), ('ready', 'Ready'), ('cancel', 'Cancelled'), ('paid', 'Paid'), ('done', 'Posted'), ('invoiced', 'Invoiced'),('scrap','Scrapped')],
        'Status', readonly=True, copy=False, default='draft')    
    d_o_number = fields.Float('D.O Number')
    qr_code = fields.Char()
    discount_type_total = fields.Float(compute="_get_discount_program_total",store=1)
    discount_type_qty = fields.Float(compute="_get_discount_program_total",store=1)
    total_qty = fields.Float()
    total_return = fields.Float()
    line_delete_ids = fields.One2many('pos.order.line_delete','order_id')
    product_line_ids = fields.One2many('pos.order.product.line','pos_order_id')
    pos_reference_custom = fields.Char('Receipt Number')
    name_custom = fields.Char('Order Ref')
    coupon_id = fields.Many2one('pos.gift.coupon')
    amount_subtotal =  fields.Float()
    amount_coupon =  fields.Float()
    amount_discount =  fields.Float()
    amount_wallet =  fields.Float()
    amount_discount_total =  fields.Float()
    amount_promotion  =  fields.Float()
    amount_subtotal_discounted  =  fields.Float()
    notes = fields.Text()             
    return_to_wallet = fields.Boolean()
    is_order_updated = fields.Boolean()
    amount_tax = fields.Float(string='Taxes', digits=False, readonly=True, required=True)
    order_kitchen_state = fields.Char()

    @api.onchange('payment_ids', 'lines')
    def _onchange_amount_all(self):
        res = super(posOrder,self)._onchange_amount_all()
        for order in self:
            order.total_qty = sum(line.qty for line in order.lines)
            order.total_return = sum(line.price_subtotal_incl for line in order.lines.filtered(lambda x: x.qty < 0))
        return res
    @api.depends('state','lines')
    def _get_discount_program_total(self):
        for rec in self:
            rec.discount_type_total = rec.discount_type_qty = 0
            if rec.discount_type_id:
                rec.discount_type_total  = sum([ line.price_subtotal_incl if line.product_id.id == rec.discount_type_id.discount_program_product_id.id else 0 for line in rec.lines])
                rec.discount_type_qty  = sum([ line.qty if line.product_id.id == rec.discount_type_id.discount_program_product_id.id else 0 for line in rec.lines])
            

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        if not self._context.get('force_delete',False):
            for pos_order in self.filtered(lambda pos_order: pos_order.state not in ['draft', 'cancel']):
                raise UserError(_('In order to delete a sale, it must be new or cancelled.'))
        


    @api.depends('amount_total','order_type_id')
    def _compute_commission(self):
        for rec in self:
            if rec.order_type_id.type == 'extra':
                rec.commission = rec.amount_total * rec.order_type_id.extra_percentage / 100
                tax_amount = sum(rec.amount_total * rec.order_type_id.extra_percentage / 100 * (tax.amount / 100) for tax in rec.order_type_id.tax_ids)
                rec.commission_after_tax = (rec.amount_total * rec.order_type_id.extra_percentage / 100) + tax_amount
            else:
                rec.commission = 0.00
                rec.commission_after_tax = 0.00

    @api.model
    def create(self, vals):
        if 'order_type_id' in vals:
            order_type = self.env['pos.order_type'].search([('id', '=', vals.get('order_type_id'))])
            vals.update({'partner_id': order_type.customer_id.id})  
        res_rec = super(posOrder, self).create(vals)
        for res in res_rec:
            if res.session_id:
                res.pos_reference_custom = str(len(res.session_id.order_ids))
                res.name_custom = res.config_id.name + '/' + res.session_id.name + '/' + res.pos_reference_custom
        
        return res_rec

    def write(self, vals):
        res = super(posOrder, self).write(vals)
        for rec in self:
            for user in rec.session_id.config_id.user_ids:
                rec.env['tracking.orders'].create({ 
                                                    'order_id': rec.id, 
                                                    'session_id': rec.session_id.id, 
                                                    'pos_config_id': rec.session_id.config_id.id, 
                                                    'user_id': user.id, 
                                                    })     
        for rec in self:
            rec.order_wallet()
                           
        return res      

    def order_wallet(self):
        #   "amount_return": 0.0,       // الباقي.
        # "return_to_wallet": true,   // اضافة الباقي للمحفظة.
        for rec in self:
            if rec.state == 'paid' and rec.partner_id:
                if rec.amount_wallet:
                    rec.env['pos.order.wallet.log'].create({
                            "order_id": rec.id,
                            "partner_id": rec.partner_id.id,
                            "amount": rec.amount_wallet * -1,
                        }) 
                    rec.partner_id.wallet_balance = rec.partner_id.wallet_balance - rec.amount_wallet


                if rec.return_to_wallet:
                    rec.env['pos.order.wallet.log'].create({
                            "order_id": rec.id,
                            "partner_id": rec.partner_id.id,
                            "amount": rec.amount_return,
                            "return_to_wallet":True,
                        }) 
                    rec.partner_id.wallet_balance = rec.partner_id.wallet_balance + rec.amount_return

                if rec.session_id.config_id.wallet_id: 
                    wallet_amount = rec.session_id.config_id.wallet_id.get_rule_order_wallet_amount(rec) 
                    if  wallet_amount:
                        rec.env['pos.order.wallet.log'].create({
                            "order_id": rec.id,
                            "partner_id": rec.partner_id.id,
                            "amount": wallet_amount,
                        })      
                        rec.partner_id.wallet_balance = rec.partner_id.wallet_balance + wallet_amount  

    
class posOrderLine(models.Model):
    _inherit = 'pos.order.line'

    pos_categ_id = fields.Many2one('pos.category',related="product_id.pos_categ_id",store=1)
    list_price = fields.Float('pos.category',related="product_id.list_price",store=1)
    tax_ids_after_fiscal_position = fields.Many2many('account.tax','account_tax_rel_pos_order',
     store=1, string='Taxes to Apply',compute=False)
    product_line_ids = fields.One2many('pos.order.product.line','pos_order_line_id')
    product_note_ids = fields.Many2many('pos.product_note')
    product_extra_ids = fields.One2many('pos.order.line.extra','pos_order_line_id')
    product_addons_ids = fields.One2many('pos.order.line.addons','pos_order_line_id')
    name_ar = fields.Char()
    name_en = fields.Char()
    custom_note = fields.Char()
    is_show = fields.Boolean()
    main_product_id = fields.Many2one('product.template')
    status = fields.Selection([('normal','Normal'),('scrapped','Scrapped'),('added','Added'),('deleted','Deleted')])
    is_send_to_kitchen = fields.Boolean()

    price_subtotal = fields.Float(string='Subtotal w/o Tax', 
        readonly=True, required=True,digits=False)
    item_kitchen_state = fields.Char()
    prepare_time = fields.Float()

    @api.depends('order_id', 'order_id.fiscal_position_id')
    def _get_tax_ids_after_fiscal_position(self):
        for line in self:
            return
            # line.tax_ids_after_fiscal_position = line.order_id.fiscal_position_id.map_tax(line.tax_ids)

class posOrderLineProductLine(models.Model):
    _name = 'pos.order.product.line'
    _rec_name = 'product_id'

    main_product_id = fields.Many2one('product.product')
    product_id = fields.Many2one('product.product')
    quantity = fields.Float()
    pos_order_line_id = fields.Many2one('pos.order.line')
    pos_order_id = fields.Many2one('pos.order',related="pos_order_line_id.order_id",store=1)

class posOrderLineExtra(models.Model):
    _name = 'pos.order.line.extra'
    _rec_name = 'product_id'

    main_product_id = fields.Many2one('product.product')
    product_id = fields.Many2one('product.product')
    quantity = fields.Float()
    pos_order_line_id = fields.Many2one('pos.order.line')
    pos_order_id = fields.Many2one('pos.order',related="pos_order_line_id.order_id",store=1)
    price = fields.Float()
    tax_ids = fields.Many2many('account.tax')
    subtotal = fields.Float()
    total_price = fields.Float()
    # is_selected = fields.Boolean()
    discount = fields.Float()
    name_ar = fields.Char()
    name_en = fields.Char()
class ComboTitle(models.Model):
    _name = 'combo.title'

    name = fields.Char('')
    arabic_name = fields.Char('')
    
class posOrderLineAddons(models.Model):
    _name = 'pos.order.line.addons'
    _rec_name = 'title_id'

    
    main_product_id = fields.Many2one('product.product')
    title_id = fields.Many2one('combo.title')
    pos_order_line_id = fields.Many2one('pos.order.line')
    pos_order_id = fields.Many2one('pos.order',related="pos_order_line_id.order_id",store=1)
    line_addons_ids = fields.One2many('pos.order.line.addons.product','line_addons_id')
    product_id = fields.Many2one('product.product')
    qty =  fields.Float()
    
class posOrderLineAddons(models.Model):
    _name = 'pos.order.line.addons.product'
    _rec_name = 'product_id' 


    product_id = fields.Many2one('product.product')
    extra_price =  fields.Float()
    qty =  fields.Float()
    line_addons_id = fields.Many2one('pos.order.line.addons')
    
    
