# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import float_compare, float_round, float_is_zero, OrderedSet


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_stock_move_vals(self, first_line, order_lines):
        res = super(StockPicking, self)._prepare_stock_move_vals(first_line, order_lines)
        res['pos_order_line_id'] = first_line.id
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    pos_order_line_id = fields.Many2one(comodel_name="pos.order.line", string="", required=False, )

    def action_explode(self):
        """ Explodes pickings """
        # in order to explode a move, we must have a picking_type_id on that move because otherwise the move
        # won't be assigned to a picking and it would be weird to explode a move into several if they aren't
        # all grouped in the same picking.
        moves_ids_to_return = OrderedSet()
        moves_ids_to_unlink = OrderedSet()
        phantom_moves_vals_list = []
        for move in self:
            if not move.picking_type_id or (move.production_id and move.production_id.product_id == move.product_id):
                moves_ids_to_return.add(move.id)
                continue
            bom = self.env['mrp.bom'].sudo()._bom_find(move.product_id, company_id=move.company_id.id,
                                                       bom_type='phantom')[move.product_id]
            if not bom:
                moves_ids_to_return.add(move.id)
                continue
            if move.picking_id.immediate_transfer:
                factor = move.product_uom._compute_quantity(move.quantity_done, bom.product_uom_id) / bom.product_qty
            else:
                factor = move.product_uom._compute_quantity(move.product_uom_qty, bom.product_uom_id) / bom.product_qty
            boms, lines = bom.sudo().explode(move.product_id, factor, picking_type=bom.picking_type_id)
            for bom_line, line_data in lines:
                if move.pos_order_line_id.order_id.order_type_id.category_order_type_id.id in bom_line.category_order_type_ids.ids:
                    if move.picking_id.immediate_transfer:
                        phantom_moves_vals_list += move._generate_move_phantom(bom_line, 0, line_data['qty'])
                    else:
                        phantom_moves_vals_list += move._generate_move_phantom(bom_line, line_data['qty'], 0)

            # delete the move with original product which is not relevant anymore
            moves_ids_to_unlink.add(move.id)

        self.env['stock.move'].browse(moves_ids_to_unlink).sudo().unlink()
        if phantom_moves_vals_list:
            phantom_moves = self.env['stock.move'].create(phantom_moves_vals_list)
            phantom_moves._adjust_procure_method()
            moves_ids_to_return |= phantom_moves.action_explode().ids
        return self.env['stock.move'].browse(moves_ids_to_return)
