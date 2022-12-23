# -- coding: utf-8 --

from odoo.http import request
import requests
import json
import logging
from odoo import models, fields, api
_logger = logging.getLogger(__name__)


class odoo_firebase(models.Model):
    _inherit = 'pos.order'

    def create(self, vals):

        record = super(odoo_firebase, self).create(vals)

        try:

            key = f'{self.env.cr.dbname}{self.env.company.name}{record.config_id.branch_id.id}_{record.multi_session_id.id}'
            url = "https://us-central1-looped-5088f.cloudfunctions.net/LastOrders"
            payload = json.dumps({
                "key": key,
                "LastOrderID": str(record.id),
            })
            headers = {'Content-Type': 'application/json'}

            requests.request("POST", url, headers=headers, data=payload)

        except Exception as ex:

            _logger.info("update on firebase : " + str(ex))

        return record

    def write(self, vals):

        record = super(odoo_firebase, self).write(vals)

        try:

            key = f'{self.env.cr.dbname}{self.env.company.name}{self.config_id.branch_id.id}_{self.multi_session_id.id}'
            url = "https://us-central1-looped-5088f.cloudfunctions.net/LastOrders"
            payload = json.dumps({
                "key": key,
                "LastOrderID": str(self.id),
            })
            headers = {'Content-Type': 'application/json'}
            requests.request("POST", url, headers=headers, data=payload)

        except Exception as ex:

            _logger.info("update on firebase : " + str(ex))

        return record
