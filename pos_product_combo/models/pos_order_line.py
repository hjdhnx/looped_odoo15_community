""" Inherit Pos Order Line"""

from odoo import fields, models
from functools import partial


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    is_combo_line = fields.Boolean(string='Is a Combo line')

    # def _order_line_fields(self, line, session_id=None):
    #     """
    #      override to add save 'combo_ext_line_info' in line vals
    #     the parent method will remove this attribute from dict valus
    #     """
    #     combo = False
    #     if line[2:] and 'combo_ext_line_info' in line[2]:
    #         combo = line[2].get('combo_ext_line_info')
    #     res = super(PosOrderLine, self)._order_line_fields(line, session_id)
    #     if res[2:] and combo:
    #         res[2].update({
    #             'combo_ext_line_info': combo,
    #         })
    #     return res


class PosOrder(models.Model):
    _inherit = "pos.order"

    # def _order_fields(self, ui_order):
    #     """ override to handle combo line to order line """
    #     res = super(PosOrder, self)._order_fields(ui_order)
    #     new_order_line = []
    #     process_line = partial(self.env['pos.order.line']._order_line_fields)
    #     order_lines = [process_line(l) for l in res['lines']] if res['lines'] else False
    #     for order_line in order_lines:
    #         taxes = self.env['account.tax']
    #         if order_line[2]['tax_ids'] and order_line[2]['tax_ids'][0][2]:
    #             taxes = taxes.browse(order_line[2]['tax_ids'][0][2])
    #         pricelist = self.env['product.pricelist'].browse(res['pricelist_id'])
    #         currency = pricelist.currency_id
    #         if 'combo_ext_line_info' in order_line[2]:
    #             own_pro_list = [
    #                 process_line(l) for l in order_line[2]['combo_ext_line_info']
    #             ] if order_line[2]['combo_ext_line_info'] else []
    #             total_combo_price_unit = 0.0
    #             for own in own_pro_list:
    #                 # own[2]['qty'] *= order_line[2]['qty']
    #                 if taxes and own[2]['price_unit']:
    #                     tax_prices = taxes.compute_all(
    #                         own[2]['price_unit'], currency, own[2]['qty']
    #                     )
    #                     total_excluded = tax_prices['total_excluded']
    #                     total_included = tax_prices['total_included']
    #                 else:
    #                     total_excluded = total_included = own[2]['qty'] * own[2]['price_unit']
    #                 own[2]['price_subtotal'] = total_excluded
    #                 own[2]['price_subtotal_incl'] = total_included
    #                 own[2]['tax_ids'] = order_line[2]['tax_ids']
    #                 # own[2]['account_analytic_id'] = order_line[2].get('account_analytic_id',False)
    #                 own[2]['is_combo_line'] = True
    #                 new_order_line.append(own)
    #             order_line[2].pop('combo_ext_line_info')
    #         new_order_line.append(order_line)
    #     res.update({
    #         'lines': new_order_line,
    #     })
    #     return res
