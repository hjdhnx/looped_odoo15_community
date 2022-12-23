# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape

import json


class ksDynamicFinancialReportController(http.Controller):

    @http.route('/ks_dynamic_financial_report', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report(self, model, ks_df_informations, output_format, financial_id=None, **kw):
        uid = request.session.uid
        ks_dynamic_report_model = request.env['ks.dynamic.financial.base']
        ks_df_informations = json.loads(ks_df_informations)
        cids = request.httprequest.cookies.get('cids', str(request.env.user.company_id.id))
        allowed_company_ids = [int(cid) for cid in cids.split(',')]
        ks_dynamic_report_instance = request.env[model].with_user(uid).with_context(allowed_company_ids=allowed_company_ids)
        if financial_id and financial_id != 'null':
            ks_dynamic_report_instance = ks_dynamic_report_instance.browse(int(financial_id))
        ks_dynamic_report_name = ks_dynamic_report_instance.display_name
        try:
            if output_format == 'xlsx':
                # self.ks_df_report_account_report_ids = self
                # if self.id == self.env.ref('ks_dynamic_financial_reports.ks_df_tb0').id:
                    response = request.make_response(
                        None,
                        headers=[
                            ('Content-Type', ks_dynamic_report_model.ks_get_export_plotting_type('xlsx')),
                            ('Content-Disposition', content_disposition(ks_dynamic_report_name + '.xlsx'))
                        ]
                    )
                    if ks_dynamic_report_name == 'Trial Balance':
                        response.stream.write(ks_dynamic_report_instance.ks_get_xlsx_trial_balance(ks_df_informations))
                    elif ks_dynamic_report_name == 'General Ledger':
                        response.stream.write(ks_dynamic_report_instance.ks_get_xlsx_general_ledger(ks_df_informations))
                    elif ks_dynamic_report_name == 'Partner Ledger':
                        response.stream.write(ks_dynamic_report_instance.ks_get_xlsx_partner_ledger(ks_df_informations))
                    elif ks_dynamic_report_name == 'Age Receivable':
                        response.stream.write(ks_dynamic_report_instance.ks_get_xlsx_Aging(ks_df_informations))
                    elif ks_dynamic_report_name == 'Age Payable':
                        response.stream.write(ks_dynamic_report_instance.ks_get_xlsx_Aging(ks_df_informations))
                    elif ks_dynamic_report_name == 'Tax Report':
                        response.stream.write(ks_dynamic_report_instance.ks_dynamic_tax_xlsx(ks_df_informations))
                    elif ks_dynamic_report_name == 'Consolidate Journal':
                        response.stream.write(ks_dynamic_report_instance.ks_dynamic_consolidate_xlsx(ks_df_informations))
                    else:
                        response.stream.write(ks_dynamic_report_instance.get_xlsx(ks_df_informations))

            return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
