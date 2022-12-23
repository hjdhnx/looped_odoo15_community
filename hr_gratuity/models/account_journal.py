# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    custom_is_gratuity_journal = fields.Boolean(
        string='Is Gratuity Journal?',
        copy=False,
    )

    gratuity_credit_account = fields.Many2one('account.account')
