# -*- coding: utf-8 -*-
#################################################################################
# Author      : Omar Abdelaziz <omar_3ziz@hotmail.com>
# Copyright(c): Developer -Omar Abdelaziz-
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################

from odoo import models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res.update({
            'total_calories': ui_order.get('total_calories') or 0.00,
        })
        return res

    total_calories = fields.Integer()
