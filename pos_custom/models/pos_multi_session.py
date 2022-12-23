# Copyright 2015-2016 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
# Copyright 2016 Ilyas Rakhimkulov
# Copyright 2017,2019 Kolushov Alexandr <https://it-projects.info/team/KolushovAlexandr>
# Copyright 2016-2018 Dinar Gabbasov <https://it-projects.info/team/GabbasovDinar>
# License MIT (https://opensource.org/licenses/MIT).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)



class PosMultiSession(models.Model):
    _name = "pos.multi_session"
    _description = "POS Multi Session"

    name = fields.Char("Name",required=1)
    multi_session_active = fields.Boolean(
        string="Active",
        help="Select the checkbox to enable synchronization for POSes",
        default=True,
    )
    pos_ids = fields.One2many(
        "pos.config", "multi_session_id", string="POSes in Multi-session"
    )
    order_ID = fields.Integer(
        string="Order number",
        default=0,
        help="Current Order Number shared across all POS in Multi Session",
    )
    sync_server = fields.Char("Sync Server", default="")
    run_ID = fields.Integer(
        string="Running count",
        default=1,
        help="Number of Multi-session starts. "
        "It's incremented each time the last session in Multi-session is closed. "
        "It's used to prevent synchronization of old orders",
    )
    fiscal_position_ids = fields.Many2many(
        "account.fiscal.position", string="Fiscal Positions", ondelete="restrict"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )


    floor_ids = fields.Many2many(
        "restaurant.floor",
        "pos_multi_session_floor_rel",
        "pos_multi_session_id",
        "floor_id",
        string="Restaurant Floors",
        help="The restaurant floors served by this point of sale",
        ondelete="restrict",
    )
    table_blocking = fields.Boolean("One Waiter per Table")


    # @api.multi
    def action_set_default_multi_session(self):
        """
            during installation of the module set default multi-session
            for all POSes for which multi_session_id is not specified
        """
        self.ensure_one()
        configs = self.env["pos.config"].search([("multi_session_id", "=", False)])
        configs.write({"multi_session_id": self.id})

    # @api.multi
    def name_get(self):
        """ Override name_get method to return generated name."""
        res = super(PosMultiSession, self).name_get()
        res = [
            (
                record[0],
                record[1] + " - Syncronization is disabled"
                if self.browse(record[0]).multi_session_active is False
                else record[1],
            )
            for record in res
        ]
        return res


