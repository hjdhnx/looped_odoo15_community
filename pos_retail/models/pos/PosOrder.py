# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, registry
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import base64
from odoo.tools import float_is_zero
import logging
from datetime import datetime, timedelta

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}

_logger = logging.getLogger(__name__)

class PosPayment(models.Model):
    _inherit = 'pos.payment'

    @api.constrains('payment_method_id')
    def _check_payment_method_id(self):
        for payment in self:
            if payment.payment_method_id.id not in payment.session_id.config_id.order_type_payment_method_ids.ids:
                raise ValidationError(_('The payment method selected is not allowed in the config of the POS session.'))

class POSOrder(models.Model):
    _inherit = 'pos.order'
    
    promotion_ids = fields.Many2many('pos.promotion', 'pos_order_promotion_rel', 'order_id', 'promotion_id', string='Promotions')
    coupon_id = fields.Many2one('pos.gift.coupon')

    def pos_create_invoice(self):
        #must change from xml to not be active unless paid
        return
        payment_method_create_invoice = self.order_type_id.payment_method_ids.filtered(lambda m: m.create_invoice != False)
        for i in payment_method_create_invoice[0]:
            if not float_is_zero(self.amount_total, precision_rounding=self.pricelist_id.currency_id.rounding):
                self.add_payment({
                                    'pos_order_id': self.id,
                                    'amount': self._get_rounded_amount(self.amount_total),
                                    'name': self.name,
                                    'payment_method_id': i.id,
                                })
            if self._is_pos_order_paid():
                self.action_pos_order_paid()
                self._create_order_picking()
                self._compute_total_cost_in_real_time()
            self.account_move.button_draft()

class POSOrderLine(models.Model):
    _inherit = "pos.order.line"

    reward_id = fields.Many2one('pos.loyalty.reward', 'Reward')

    coupon_program_id = fields.Many2one(
        'coupon.program',
        'Coupon Program',
        readonly=1
    )
    coupon_id = fields.Many2one(
        'coupon.coupon',
        'Coupon',
        readonly=1
    )
    coupon_ids = fields.Many2many(
        'coupon.coupon',
        'coupon_coupon_gift_card_rel',
        'pos_line_id',
        'coupon_id',
        string='Gift Cards',
        readonly=1
    )
    promotion = fields.Boolean('Applied Promotion', readonly=1)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion', readonly=1, ondelete="set null")
    promotion_reason = fields.Char(string='Promotion Reason', readonly=1)
    
