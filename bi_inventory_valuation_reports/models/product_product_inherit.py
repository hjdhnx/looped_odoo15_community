# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import models, api, fields
from datetime import date
from odoo.tools.float_utils import float_round


class ProductProductInherit(models.AbstractModel):
    _inherit = "product.product"

    get_all = fields.Boolean()


    def get_prd_name_with_atrr(self):
        self.ensure_one()
        name = "";
        name += self.name;
        attribute = "";
        if self.product_template_attribute_value_ids:
            for attr in self.product_template_attribute_value_ids:
                attribute += "," + attr.name;
            name += " (%s)"%attribute[1:len(attribute)];
        return name;


    def set_flag_to_get_all_records(self):
        for rec in self:
            rec.get_all = True
    