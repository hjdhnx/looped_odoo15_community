""" Inherit Product Template """

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_combo = fields.Boolean("Has Addons", ) #compute="_compute_combo", store =True)
    product_combo_ids = fields.One2many(
        'product.combo',
        'product_tmpl_id',
        copy=True
    )
    product_price_ids = fields.One2many(
        'product.combo.price',
        'product_tmpl_id',
        copy=True
    )

    valid_product_attribute_ids = fields.Many2many('product.attribute',
                                                   compute="_compute_valid_product_template_attribute_line_ids",
                                                   string='Valid Product Attributes',
                                                   help="Technical compute")
    valid_product_attribute_value_ids = fields.Many2many('product.attribute.value',
                                                         compute="_compute_valid_product_template_attribute_line_ids",
                                                         string='Valid Product Attribute Values',
                                                         help="Technical compute")

    @api.depends('attribute_line_ids.value_ids', 'attribute_line_ids.attribute_id')
    def _compute_valid_product_template_attribute_line_ids(self):
        """A product template attribute line is considered valid if it has at
        least one possible value.

        Those with only one value are considered valid, even though they should
        not appear on the configurator itself (unless they have an is_custom
        value to input), indeed single value attributes can be used to filter
        products among others based on that attribute/value.
        """
        for record in self:
            valid_product_template_attribute_line_ids = record.attribute_line_ids.filtered(
                lambda ptal: ptal.value_ids)
            record.valid_product_template_attribute_line_ids = valid_product_template_attribute_line_ids
            record.valid_product_attribute_ids = valid_product_template_attribute_line_ids.mapped(
                'attribute_id')
            record.valid_product_attribute_value_ids = valid_product_template_attribute_line_ids.mapped(
                'value_ids')

    # @api.depends('product_combo_ids')
    # def _compute_combo(self):
    #     for rec in self:
    #         if rec.product_combo_ids:
    #             rec.is_combo = True
    #         else:
    #             rec.is_combo = False

    @api.constrains('product_combo_ids', 'product_price_ids')
    def _check_categ_counts(self):
        for rec in self:
            combo_vals = {}
            extra_vals = {}
            for combo in rec.product_combo_ids:
                if combo.pos_category_id:
                    combo_vals.setdefault(combo.pos_category_id.id, 0)
                    combo_vals[combo.pos_category_id.id] += combo.no_of_items
            for extra in rec.product_price_ids:
                categ = extra.product_id.pos_categ_id
                if categ:
                    extra_vals.setdefault(categ.id, 0)
                    extra_vals[categ.id] += extra.auto_select_num
                    if combo_vals.get(categ.id) and extra_vals[categ.id] > combo_vals[categ.id]:
                        raise ValidationError(
                            _("Total Auto Selected Number [%s] of categ [%s] is greater than the "
                              "number [%s] of items of the same category in combo table" % (
                                extra_vals[categ.id], categ.name, combo_vals[categ.id]
                            ))
                        )

    @api.onchange("product_combo_ids")
    def _onchange_product_combo_ids(self):
        toremove_prices = self.env['product.combo.price']
        keeped_prices = {}
        keeped_qty = {}
        keeped_seq = {}
        toadd_prices = []
        for price in self.product_price_ids:
            found = self.product_combo_ids.filtered(lambda pc: price.product_id.id in pc.product_ids.ids)
            if price.attribute_value_id:
                found = found.filtered(lambda pc: price.attribute_value_id.id in pc.attribute_value_ids.ids)
            if not found:
                toremove_prices |= price
                keeped_prices[price.product_id.id] = price.extra_price
                keeped_qty[price.product_id.id] = price.auto_select_num
                keeped_seq[price.product_id.id] = price.sequence
            else:
                found = found.filtered(lambda pc: not price.attribute_value_id and pc.attribute_value_ids)
                if found:
                    toremove_prices |= price
        for combo in self.product_combo_ids:
            for pcombo in combo.product_ids:
                if not combo.attribute_value_ids:
                    found = self.product_price_ids.filtered(
                        lambda pp: pp.product_id.id == pcombo.id.origin and not pp.attribute_value_id.id)
                    if not found:
                        toadd_prices.append((pcombo, False))
                else:
                    for value_pcombo in combo.attribute_value_ids:
                        found = self.product_price_ids.filtered(
                            lambda pp: pp.product_id.id == pcombo.id.origin and pp.attribute_value_id.id == value_pcombo.id.origin)
                        if not found:
                            toadd_prices.append((pcombo, value_pcombo))

        remove_list = [(2, rpprice.id) for rpprice in toremove_prices]
        add_list = [(0, 0, {'product_id': apprice[0].id.origin if apprice[0] else apprice[0],
                            'attribute_value_id': apprice[1].id.origin if apprice[1] else apprice[1],
                            'extra_price': keeped_prices.get(
                                apprice[0].id.origin if apprice[0] else apprice[0], 0),
                            'auto_select_num': keeped_qty.get(
                                apprice[0].id.origin if apprice[0] else apprice[0], 0),
                            'sequence': keeped_seq.get(
                                apprice[0].id.origin if apprice[0] else apprice[0], 0),
                            }
                     ) for apprice in
                    toadd_prices]
        self.product_price_ids = remove_list + add_list

    @api.onchange('sale_ok')
    def unset_is_combo(self):
        if not self.sale_ok:
            self.is_combo = False
