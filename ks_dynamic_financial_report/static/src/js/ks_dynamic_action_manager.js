odoo.define("ks_dynamic_financial_report.report", function (require) {
    "use strict";

    var core = require('web.core');
    var ks_framework = require('web.framework');
    var ks_session = require('web.session');

     function ks_executexlsxReportDownloadAction(parent, action) {
        var self = this;
        ks_framework.blockUI();
        var def = $.Deferred();
        return new Promise(function (resolve, reject) {
            ks_session.get_file({
                url: '/ks_dynamic_financial_report',
                data: action.data,
                success: def.resolve.bind(def),
                complete: ks_framework.unblockUI,
            });
            return def;
        });
    };
    core.action_registry.add("ks_executexlsxReportDownloadAction", ks_executexlsxReportDownloadAction);
 });