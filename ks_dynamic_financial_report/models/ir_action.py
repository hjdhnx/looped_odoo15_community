# -*- coding: utf-8 -*-

from odoo import models, fields

class IrActionsAccountReportDownload(models.Model):
    _inherit = 'ir.actions.actions'
    _table = 'ir_actions'

    type = fields.Char(default='ir_actions_account_report_download')

    def _get_readable_fields(self):
        # data is not a stored field, but is used to give the parameters to generate the report
        # We keep it this way to ensure compatibility with the way former version called this action.
        return super()._get_readable_fields() | {'data'}