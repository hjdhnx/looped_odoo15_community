odoo.define('branch_accounting_report.account_report_generic', function (require) {
    'use strict';
    console.log(">>>>>>>>>>>>>>>>>>>>>>>.branch 0");
    var core = require('web.core');
    var Context = require('web.Context');
    var AbstractAction = require('web.AbstractAction');
    var Dialog = require('web.Dialog');
    var datepicker = require('web.datepicker');
    var session = require('web.session');
    var field_utils = require('web.field_utils');
    var RelationalFields = require('web.relational_fields');
    var StandaloneFieldManagerMixin = require('web.StandaloneFieldManagerMixin');
    // var WarningDialog = require('web.CrashManager').WarningDialog;
    var { WarningDialog } = require("@web/legacy/js/_deprecated/crash_manager_warning_dialog");
    var Widget = require('web.Widget');

    var accountReportsWidget = require('account_reports.account_report');


    var QWeb = core.qweb;
    var _t = core._t;
    
    var M2MBranchFilters = Widget.extend(StandaloneFieldManagerMixin, {
        /**
         * @constructor
         * @param {Object} fields
         */
        init: function (parent, fields) {
            
            this._super.apply(this, arguments);
            StandaloneFieldManagerMixin.init.call(this);
            this.fields = fields;
            this.widgets = {};
        },
        /**
         * @override
         */
        willStart: function () {
            
            var self = this;
            var defs = [this._super.apply(this, arguments)];
            _.each(this.fields, function (field, fieldName) {
                defs.push(self._makeM2MWidget(field, fieldName));
            });
            return Promise.all(defs);
        },
        /**
         * @override
         */
        start: function () {
            
            var self = this;
            var $content = $(QWeb.render("m2mWidgetTable", { fields: this.fields }));
            self.$el.append($content);
            _.each(this.fields, function (field, fieldName) {
                self.widgets[fieldName].appendTo($content.find('#' + fieldName + '_field'));
            });
            return this._super.apply(this, arguments);
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * This method will be called whenever a field value has changed and has
         * been confirmed by the model.
         *
         * @private
         * @override
         * @returns {Promise}
         */
        _confirmChange: function () {
            
            var self = this;
            var result = StandaloneFieldManagerMixin._confirmChange.apply(this, arguments);
            var data = {};
            _.each(this.fields, function (filter, fieldName) {
                data[fieldName] = self.widgets[fieldName].value.res_ids;
            });
            console.log(data);
            console.log(this.fields);
            console.log(">>>>>>>>>>>>>>>>>>>>>>>.branch 55");
            this.trigger_up('value_changed', data);
            return result;
        },
        /**
         * This method will create a record and initialize M2M widget.
         *
         * @private
         * @param {Object} fieldInfo
         * @param {string} fieldName
         * @returns {Promise}
         */
        _makeM2MWidget: function (fieldInfo, fieldName) {
            
            var self = this;
            var options = {};
            options[fieldName] = {
                options: {
                    no_create_edit: true,
                    no_create: true,
                }
            };
            return this.model.makeRecord(fieldInfo.modelName, [{
                fields: [{
                    name: 'id',
                    type: 'integer',
                }, {
                    name: 'display_name',
                    type: 'char',
                }],
                name: fieldName,
                relation: fieldInfo.modelName,
                type: 'many2many',
                value: fieldInfo.value,
            }], options).then(function (recordID) {
                self.widgets[fieldName] = new RelationalFields.FieldMany2ManyTags(self,
                    fieldName,
                    self.model.get(recordID),
                    { mode: 'edit', }
                );
                self._registerWidget(recordID, fieldName, self.widgets[fieldName]);
            });
        },
    });




    accountReportsWidget.include({

        custom_events: _.extend({}, accountReportsWidget.prototype.custom_events, {

            'value_changed': function (ev) {
                var self = this;

                
                // console.log(ev.data.branch);
                console.log(this.$searchview_buttons.find('td[name="analytic_accounts"]'));
                console.log(this.$searchview_buttons.find('td[name="analytic_accounts"]').children);

                //Analytic Account
                var analytic_ids = [];
                var children = document.getElementsByName("analytic_accounts")
                if (children.length) {
                    children = children[0].children;

                    for (var i = 0, len = children.length; i < len; i++) {
                        console.log(children[i]);
                        // children[i].className = 'new-class'; //change child class name.
                        if (children[i].dataset.id) {
                            analytic_ids.push(children[i].dataset.id); //get child id.
                        }
                    }
                    self.report_options.analytic_accounts = analytic_ids;
                }

                //Tags
                var tag_ids = [];
                var children = document.getElementsByName("analytic_tags") 
                if (children.length) {
                    children = children[0].children;
                for (var i = 0, len = children.length; i < len; i++) {
                    console.log(children[i]);
                    // children[i].className = 'new-class'; //change child class name.
                    if (children[i].dataset.id) {
                        tag_ids.push(children[i].dataset.id); //get child id.
                    }
                }
                self.report_options.analytic_tags = tag_ids;
                }



                //Partners
                var partner_ids = [];
                var children = document.getElementsByName("partner_ids") 
                if (children.length) {
                    children = children[0].children;
                for (var i = 0, len = children.length; i < len; i++) {
                    console.log(children[i]);
                    // children[i].className = 'new-class'; //change child class name.
                    if (children[i].dataset.id) {
                        partner_ids.push(children[i].dataset.id); //get child id.
                    }
                }
                self.report_options.partner_ids = partner_ids;
                }

                //Branch
                var branch = [];
                var children = document.getElementsByName("branch") 
                if (children.length) {
                    children = children[0].children;
                for (var i = 0, len = children.length; i < len; i++) {
                    console.log(children[i]);
                    // children[i].className = 'new-class'; //change child class name.
                    if (children[i].dataset.id) {
                        branch.push(parseInt(children[i].dataset.id)); //get child id.
                    }
                }
                self.report_options.branch_ids = branch;
                }
                

                
                


                // self.report_options.branch_ids = ev.data.branch;
                // self.report_options.partner_ids = ev.data.partner_ids;
                self.report_options.partner_categories = ev.data.partner_categories;
                // self.report_options.analytic_accounts = ev.data.analytic_accounts;

                // self.report_options.analytic_tags = ev.data.analytic_tags;
                return self.reload().then(function () {
                    self.$searchview_buttons.find('.account_branch_filter').click();
                    self.$searchview_buttons.find('.account_partner_filter').click();
                    self.$searchview_buttons.find('.account_analytic_filter').click();

                });
            },
        }),
        renderButtons: function () {


            var self = this;
            this.$buttons = $(QWeb.render("accountReports.buttons", { buttons: this.buttons }));
            
            
            // bind actions
            _.each(this.$buttons.siblings('button'), function (el) {
                $(el).click(function () {
                    self.$buttons.attr('disabled', true);
                    return self._rpc({
                        model: self.report_model,
                        method: $(el).attr('action'),
                        args: [self.financial_id, self.report_options],
                        context: self.odoo_context,
                    })
                        .then(function (result) {
                            var doActionProm = self.do_action(result);
                            self.$buttons.attr('disabled', false);
                            return doActionProm;
                        })
                        .guardedCatch(function () {
                            self.$buttons.attr('disabled', false);
                        });
                });
            });
            return this.$buttons;
        },

        render_searchview_buttons: function () {
            var self = this;
            
            self._super();
            console.log(this.M2MBranchFilters);
            if (this.report_options.branch) {
                
                if (!this.M2MBranchFilters) {
                    
                    var fields = {};
                    if ('branch_ids' in this.report_options) {
                        
                        fields['branch'] = {
                            label: _t('Branch'),
                            modelName: 'res.branch',
                            value: this.report_options.branch_ids.map(Number),
                        };
                        console.log(fields['branch']);
                    }

                    if (!_.isEmpty(fields)) {
                        
                        this.M2MBranchFilters = new M2MBranchFilters(this, fields);
                        this.M2MBranchFilters.appendTo(this.$searchview_buttons.find('.js_account_branch_m2m'));
                    }
                } else {
                    this.$searchview_buttons.find('.js_account_branch_m2m').append(this.M2MBranchFilters.$el);
                }
            }

        },

    });

});
