# Copyright 2018 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockLocation(models.Model):
    _inherit = "stock.location"

    @api.constrains("company_id")
    def _check_company_stock_request(self):
        if any(
            rec.company_id
            and self.env["stock.request"].search(
                [("company_id", "!=", rec.company_id.id), ("location_id", "=", rec.id)],
                limit=1,
            )
            for rec in self
        ):
            raise ValidationError(
                _(
                    "You cannot change the company of the location, as it is "
                    "already assigned to stock requests that belong to "
                    "another company."
                )
            )
        if any(
            rec.company_id
            and self.env["stock.request.order"].search(
                [
                    ("company_id", "!=", rec.company_id.id),
                    ("warehouse_id", "=", rec.id),
                ],
                limit=1,
            )
            for rec in self
        ):
            raise ValidationError(
                _(
                    "You cannot change the company of the location, as it is "
                    "already assigned to stock request orders that belong to "
                    "another company."
                )
            )


    @api.returns('stock.warehouse', lambda value: value.id)
    def get_warehouse(self):
        """ Returns warehouse id of warehouse that contains location """
        domain = [('view_location_id', 'parent_of', self.ids)]
        return self.env['stock.warehouse'].search(domain, limit=1)