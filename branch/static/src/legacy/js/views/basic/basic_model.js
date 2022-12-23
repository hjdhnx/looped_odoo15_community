odoo.define('branch.BasicModel', function (require) {
"use strict";

var core = require('web.core');
const pyUtils = require('web.py_utils');
var session = require('web.session');
var localStorage = require('web.local_storage');

var _t = core._t;

var basicModel = require('web.BasicModel');
var BasicModel = basicModel.include({
    
   
    _getEvalContext: function (element, forDomain) {
        var evalContext = element.type === 'record' ? this._getRecordEvalContext(element, forDomain) : {};

        if (element.parentID) {
            var parent = this.localData[element.parentID];
            if (parent.type === 'list' && parent.parentID) {
                parent = this.localData[parent.parentID];
            }
            if (parent.type === 'record') {
                evalContext.parent = this._getRecordEvalContext(parent, forDomain);
            }
        }
        
        let current_company_id;
        if (session.user_context.allowed_company_ids) {
            current_company_id = session.user_context.allowed_company_ids[0];
        } else {
            current_company_id = session.user_companies ?
                session.user_companies.current_company :
                false;
        }

        let current_branch_id;
        if (session.user_context.allowed_branch_ids) {
            current_branch_id = session.user_context.allowed_branch_ids[0];
        } else {
            current_branch_id = session.user_companies ?
                session.user_companies.current_branch :
                false;
        }
        return Object.assign(
            {
                active_id: evalContext.id || false,
                active_ids: evalContext.id ? [evalContext.id] : [],
                active_model: element.model,
                current_company_id,
                current_branch_id,
                id: evalContext.id || false,
            },
            pyUtils.context(),
            session.user_context,
            element.context,
            evalContext,
        );
    },
    
    
    _invalidateCache: function (dataPoint) {
        while (dataPoint.parentID) {
            dataPoint = this.localData[dataPoint.parentID];
        }
        if (dataPoint.model === 'res.currency') {
            session.reloadCurrencies();
        }
        if (dataPoint.model === 'res.company' && !localStorage.getItem('running_tour')) {
            this.do_action('reload_context');
        }
        if (dataPoint.model === 'res.branch' && !localStorage.getItem('running_tour')) {
            this.do_action('reload_context');
        }
        if (_.contains(this.noCacheModels, dataPoint.model)) {
            core.bus.trigger('clear_cache');
        }
    },
});

return BasicModel;
});
