# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response

import logging
import iclockhelper
from urllib.request import Request
import datetime

_logger = logging.getLogger(__name__)


class LoopedAttendance(http.Controller):
    @http.route('/iclock/cdata', csrf=False, auth='none', save_session=False)
    def cdataView(self, **kw):
        logging.info("cdata")

        # CdataRequest(sn='3836163100001', push_version=0.0,
        # method='POST', pin='', save=False, body='1\t2019-12-21 19:51:28\t0\t4\t0\t0\t0\n',
        # stamp='9999', operation_stamp='', table=<TableEnum.attlog: 'ATTLOG'>,

        # attendance_log=AttendanceLog(raw='1\t2019-12-21 19:51:28\t0\t4\t0\t0\t0\n',
        # transactions=[Transaction(server_datetime=datetime.datetime(2019, 12, 21, 19, 51, 28),
        # pin='1', raw='1\t2019-12-21 19:51:28\t0\t4\t0\t0\t0', check_type='0', verify_code='4',
        # work_code='0', reserved='0'), Transaction(server_datetime=None, pin='', raw='', check_type='',
        # verify_code='', work_code='', reserved='')]), operation_log=None, attendance_photo_log=None)

        zk_request = self._create_request(http.request.httprequest)
        cdata_req = iclockhelper.CdataRequest.from_req(zk_request)
        _logger.info("================")
        _logger.info(cdata_req)
        _logger.info("================")

        # tz = pytz.timezone(self._get_tz())

        sereal_number = cdata_req.sn
        pin = cdata_req.pin

        # check_type = cdata_req.check_type

        attendance_log = cdata_req.attendance_log

        # verify_code = cdata_req.verify_code

        if attendance_log:
            if attendance_log.transactions:
                for transactions in attendance_log.transactions:
                    if transactions.server_datetime:

                        device_id = request.env['attendance.device'].sudo().search(
                            [('device_id', '=', sereal_number)])

                        if (device_id):
                            tr = request.env['attendance.log'].un_upset_datetime(
                                transactions.server_datetime, str(device_id.location_id))

                            loging_date = datetime.datetime.strftime(
                                tr, '%Y-%m-%d %H:%M:%S')
                            _logger.info("===========tr======" +
                                         str(loging_date))
                            # loging_date = datetime.datetime(transactions.server_datetime, tzinfo=datetime.timezone('utc'))

                            finger_print_pin = transactions.pin
                            check_type = transactions.check_type
                            verify_code = transactions.verify_code

                            if loging_date and device_id.device_enable:
                                log = request.env['attendance.log'].sudo().create({
                                    'name': "Unregistared User",
                                    'device_id': device_id.id,
                                    'loging_date': str(loging_date),
                                    'finger_print_pin': finger_print_pin,
                                    'check_type': check_type,
                                    'verify_code': verify_code
                                })
                        else:
                            request.env['attendance.device'].sudo().create({
                                'device_id': str(sereal_number),
                                'device_enable': False,
                                'location_id': 'Asia/Riyadh',
                            })

        return Response('OK')

    def _create_request(self, req) -> iclockhelper.Request:
        logging.info("_create_request")

        return Request(
            headers=req.headers,
            method=req.method,
            url=req.url,
            data=req.data,
        )

    # def _get_tz(self):

    #     return (self.env.user.tz
    #             or self.employee_id.tz
    #             or self.resource_id.tz
    #             or self._context.get('tz')
    #             or self.company_id.resource_calendar_id.tz
    #             or 'UTC')

    # /iclock/fdata
    @http.route('/iclock/fdata', csrf=False, auth='none', save_session=False)
    def fdataView(self):
        logging.info("fdata")

        # not implemented
        logging.info("===========")
        return Response('OK')

    @http.route('/iclock/getreq', csrf=False, auth='none', save_session=False)
    def getreqView(self):
        # logging.info("getrequest")
        zk_request = self._create_request(http.request.httprequest)
        # get_req = iclockhelper.GetRequest.from_req(zk_request)
        # print(get_req)
        # logging.info(get_req)

        return
        # return Response('OK')

        # /iclock/devicecmd
    def devpostView(self):
        # not implemented
        return Response('OK')

    # @http.route('/looped_attendance/looped_attendance', auth='public')
    # def index(self, **kw):
    #     return "Hello, world"


#     @http.route('/looped_attendance/looped_attendance/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('looped_attendance.listing', {
#             'root': '/looped_attendance/looped_attendance',
#             'objects': http.request.env['looped_attendance.looped_attendance'].search([]),
#         })

#     @http.route('/looped_attendance/looped_attendance/objects/<model("looped_attendance.looped_attendance"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('looped_attendance.object', {
#             'object': obj
#         })
# -*- coding: utf-8 -*-
# from odoo import http
# from odoo.http import request, Response
# import json
# from odoo.exceptions import AccessError
# from odoo.addons.web.controllers.main import Database
# from odoo.addons.pos_custom.controllers.login import validate_token
# from odoo.addons.pos_custom.controllers.common import invalid_response, valid_response
# from odoo import fields
# from datetime import datetime, timedelta
# import hashlib
# import os
# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
# try:
#     from xmlrpc import client as xmlrpclib
# except ImportError:
#     import xmlrpclib

# def execute(connector, method, *args):
#     res = False
#     try:
#         res = getattr(connector, method)(*args)
#     except socket.error as error:
#         _logger.critical('Error while executing the method "execute". Error: ' + str(error))
#         raise error
#     return res

# class posCustomAPI(http.Controller):

#     @validate_token
#     @http.route('/pos_custom/get_updated_orders',type='json', methods=['POST'], auth="none", csrf=False)
#     def get_updated_orders(self, **kw):
#         """ get pos updated orders """
#         tracking_orders_obj = request.env['tracking.orders'].sudo()
#         tracking_orders_record = tracking_orders_obj.search([('user_id', '=', request.uid)])
#         data = []
#         for tracking_order in tracking_orders_record:
#             data += [{
#                         'id': tracking_order.id,
#                         'order_id': tracking_order.order_id.id,
#                         'session_id': tracking_order.session_id.id,
#                         'pos_id': tracking_order.pos_config_id.id,
#                         'updated_on': tracking_order.write_date,
#                         'updated_by': tracking_order.write_uid.id,
#                     }]
#         Response.status = "200"
#         result = {
#                     'message': "Get All Updated Orders Successfully",
#                     'body': data
#                 }
#         return result
