# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class Ks_Res_Company(models.Model):
    _inherit = "res.company"

    def ks_get_choosed_default_tax_report(self):
        """ Returns the tax report object to be selected by default the first
        time the tax report is open for current company; or None if there isn't any.

        This method just selects the first available one, but is intended to be
        a hook for localization modules wanting to select a specific report
        depending on some particular factors (type of business, installed CoA, ...)
        """
        self.ensure_one()
        available_reports = self.ks_get_existing_tax_report()
        return available_reports and available_reports[0] or None

    def ks_get_existing_tax_report(self):
        """ Returns all the tax reports available for the country of the current
        company.
        """
        self.ensure_one()
        # return self.env['account.tax.report'].search([('country_id', '=', self.account_tax_fiscal_country_id.id)])
        return self.env['account.tax.report'].search([('country_id', '=', self.account_fiscal_country_id.id)])
