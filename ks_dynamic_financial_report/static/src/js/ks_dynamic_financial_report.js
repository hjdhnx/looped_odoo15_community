odoo.define('ks_dynamic_financial_report.dynamic_report', function (require) {
    'use strict';
    var core = require('web.core');
    var Context = require('web.Context');
    var AbstractAction = require('web.AbstractAction');
    var Dialog = require('web.Dialog');
    var datepicker = require('web.datepicker');
    var session = require('web.session');
    var field_utils = require('web.field_utils');
    var RelationalFields = require('web.relational_fields');
    var StandaloneFieldManagerMixin = require('web.StandaloneFieldManagerMixin');
//    var WarningDialog = require('web.CrashManager').WarningDialog;
    var Widget = require('web.Widget');



    var QWeb = core.qweb;
    var _t = core._t;


    var ksMany2ManyWidget = Widget.extend(StandaloneFieldManagerMixin, {
        /**
         * @override
         * @method to set fields
         */
        init: function (parent, fields) {
            this._super.apply(this, arguments);
            StandaloneFieldManagerMixin.init.call(this);
            this.fields = fields;
            this.widgets = {};
        },
        /**
         * @override
         * @method to initialise the many2many widget
         */
        willStart: function () {
            var self = this;
            var defs = [this._super.apply(this, arguments)];
            _.each(this.fields, function (field, fieldName) {
                defs.push(self._ksInitMany2ManyWidget(field, fieldName));
            });
            return Promise.all(defs);
        },

        /**
         * @override
         * @method to render many2many widget
         */
        start: function () {
            var self = this;
            var $content = $(QWeb.render("ksMany2ManyWidgetStructure", {
                fields: this.fields
            }));
            self.$el.append($content);
            _.each(this.fields, function (field, fieldName) {
                self.widgets[fieldName].appendTo($content.find('#' + fieldName + '_field'));
            });
            return this._super.apply(this, arguments);
        },

        _confirmChange: function () {
            var self = this;
            var result = StandaloneFieldManagerMixin._confirmChange.apply(this, arguments);
            var data = {};
            _.each(this.fields, function (filter, fieldName) {
                data[fieldName] = self.widgets[fieldName].value.res_ids;
            });
            this.trigger_up('ks_value_modified', data);
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
        _ksInitMany2ManyWidget: function (fieldInfo, fieldName) {
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
                    self.model.get(recordID), {
                        mode: 'edit',
                    }
                );
                self._registerWidget(recordID, fieldName, self.widgets[fieldName]);
            });
        },
    });


    var ksDynamicReportsWidget = AbstractAction.extend({
        hasControlPanel: true,
        events: {
            'click .ks_py-mline': 'ksGetMoveLines',
            'click .ks_pl-py-mline': 'ksGetPlMoveLines',
            'click .ks_pr-py-mline': 'ksGetAgedLinesInfo',
            'click .ks_cj-py-mline': 'ksGetConsolidateInfo',
            'click .ks_report_pdf': 'ksReportPrintPdf',
            'click .ks_report_xlsx': 'ksPrintReportXlsx',
            'click [action]': 'ksGetAction',
            'click .ks_send_email': "ksReportSendEmail",
            'hide.bs.dropdown': "ksHideDropDown",
            'click .o_control_panel': 'ksRemoveDisplayClass',
            'click .o_content': 'ksRemoveDisplayClass',
            'click .o_main_navbar': 'ksRemoveDisplayClass',
        },

        ksRemoveDisplayClass: function(evt){
            $('.o_filter_menu').removeClass('ks_d_block')
        },

        custom_events: {
            ks_value_modified :'ksPerformOnchange',
        },
        /**
         * @override
         */
        init: function (parent, action) {
            var self = this;
            self.ksSetInitObjects(parent, action);
            self.ksStorageKeyOpt(action);
            return self._super.apply(self, arguments);
        },

        /**
         * @override
         */
        willStart: async function () {
            const ksDynRepInfoProm = this._rpc({
                model: this.ks_dyn_fin_model,
                method: 'ks_get_dynamic_fin_info',
                args: [this.ks_report_id, this.ks_df_report_opt],
                context: this.ks_df_context,
            }).then(res => this.ksSetDfRepInfo(res));
            const ksParentProm = this._super(...arguments);
            return Promise.all([ksDynRepInfoProm, ksParentProm]);
        },

        /**
         * @override
         * @default method of widget to update control-panel and render view
         */
        start: async function () {
            this.controlPanelProps.cp_content = {
                $searchview_buttons: this.$ks_searchview_buttons,
                $pager: this.$pager,
                $searchview: this.$searchview,
            };
            await this._super(...arguments);
            this.ksRenderReport();
        },

        /**
         * @method to set init objects
         */
        ksSetInitObjects: function (parent, action) {
            this.actionManager = parent;
            this.ks_dyn_fin_model = action.context.model;
            if (this.ks_dyn_fin_model === undefined) {
                this.ks_dyn_fin_model = 'ks.dynamic.financial.base';
            }
            this.ks_report_id = false;
            if (action.context.id) {
                this.ks_report_id = action.context.id;
            }
            this.ks_df_context = action.context;
            this.ks_df_report_opt = action.ks_df_informations || false;
            this.ignore_session = action.ignore_session;
        },

        /**
         * @method to stop-propagation of inner dropdown
         */
        ksHideDropDown: function (event) {
            if (!event.clickEvent) {
                return true;
            }
            var target = $(event.clickEvent.target);
            return !(target.hasClass('ks_stop_propagation') || target.parents('.ks_stop_propagation').length);
        },

        /**
         * @method to perform onchange on values
         */
        ksPerformOnchange: function (ev) {
            var self = this;
            self.ks_df_report_opt.ks_partner_ids = ev.data.ks_partner_ids;
            self.ks_df_report_opt.analytic_accounts = ev.data.ks_analytic_ids;
            self.ks_df_report_opt.analytic_tags = ev.data.ks_analytic_tag_ids;
            return self.ksReloadReport().then(function () {
                self.$ks_searchview_buttons.find('.ks_df_partner_filter').click();
                self.$ks_searchview_buttons.find('.ks_df_analytic_filter').click();
            });
        },

        /**
         * @method to set/get Storage keys
        */
        ksStorageKeyOpt: function (action = false) {
            let action_this = action || this;
            let self = this;
            if ((action_this.ignore_session === 'read' || action_this.ignore_session === 'both') !== true) {
                var ks_df_report_key = 'report:' + self.ks_dyn_fin_model + ':' + self.ks_report_id + ':' + session.company_id;
                action ? self.ksGetStorageKey(ks_df_report_key) : self.ksSetStorageKey(ks_df_report_key);
            }
        },

        /**
         * @method to print the report pdf
        */
        ksReportPrintPdf: function (e) {
            var self = this;
            this._rpc({
                model: this.ks_dyn_fin_model,
                method: 'ks_get_dynamic_fin_info',
                args: [this.ks_report_id, this.ks_df_report_opt],
                context: this.ks_df_context,
            }).then(function (data) {
                var report_name = self.ksGetReportName();
                var action = self.ksGetReportAction(report_name,data);
                return self.do_action(action);
            });
        },

        /**
         * @method to get report name
        */
        ksGetReportName: function(){
            var self = this;
            if (self._title == _t('Trial Balance')) {
                return 'ks_dynamic_financial_report.ks_account_report_trial_balance';
            } else if (self._title == _t('General Ledger')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_general_ledger';
            } else if (self._title == _t('Partner Ledger')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_partner_ledger';
            } else if (self._title == _t('Age Receivable')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_age_receivable';
            } else if (self._title == _t('Age Payable')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_age_payable';
            } else if (self._title == _t('Consolidate Journal')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_consolidate_journal';
            } else if (self._title == _t('Tax Report')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_tax_report';
            } else if (self._title == _t('Executive Summary')) {
                return 'ks_dynamic_financial_report.ks_df_executive_summary';
            } else {
                return 'ks_dynamic_financial_report.ks_account_report_lines';
            }
        },

        /**
         * @method to get report action
        */
        ksGetReportAction: function(report_name,data)   {
            var self = this;
            return {
                'type': 'ir.actions.report',
                'report_type': 'qweb-pdf',
                'report_name': report_name,
                'report_file': report_name,
                'data': {
                    'js_data': data
                },
                'context': {
                    'active_model': self.ks_dyn_fin_model,
                    'landscape': 1,
                    'from_js': true
                },
                'display_name': self._title,
            };
        },

        /**
         * @method to send report email to user
        */
        ksReportSendEmail: function (e) {
            e.preventDefault();
            var self = this;
            this._rpc({
                model: this.ks_dyn_fin_model,
                method: 'ks_get_dynamic_fin_info',
                args: [this.ks_report_id, this.ks_df_report_opt],
                context: this.ks_df_context,
            }).then(function (data) {
                var ks_report_action = self.ksGetReportActionName();
                self._rpc({
                    model: self.ks_dyn_fin_model,
                    method: 'ks_action_send_email',
                    args: [self.ks_report_id, data, ks_report_action],
                    context: data['context'],
                });
            });
        },

        /**
         * @method to get report action name
        */
        ksGetReportActionName: function(){
            var self = this;

            if (self._title == _t('Trial Balance')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_trial_bal_action';
            } else if (self._title == _t('General Ledger')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_gel_bal_action';
            } else if (self._title == _t('Partner Ledger')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_partner_led_action';
            } else if (self._title == _t('Age Receivable')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_age_rec_action';
            } else if (self._title == _t('Age Payable')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_age_pay_action';
            } else if (self._title == _t('Consolidate Journal')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_cons_journal_action';
            } else if (self._title == _t('Tax Report')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_tax_action';
            } else if (self._title == _t('Executive Summary')) {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_executive_action';
            } else {
                return 'ks_dynamic_financial_report.ks_dynamic_financial_report_action';
            }
        },

        /**
         * @method to print report excel
        */
        ksPrintReportXlsx: function () {
            var self = this;
            self._rpc({
                model: this.ks_dyn_fin_model,
                method: 'ks_print_xlsx',
                args: [this.ks_report_id, this.ks_df_report_opt],
                context: this.ks_df_context
            }).then(function (action) {
                return self.do_action(action);
            });
        },

        /**
         * @method to set report Information
        */
        ksSetReportInfo: function (values) {
            this.ks_df_reports_ids= values.ks_df_reports_ids;
            this.ks_df_report_opt = values.ks_df_informations;
            this.ks_df_context = values.context;
            this.ks_report_manager_id = values.ks_report_manager_id;
            this.ks_remarks = values.ks_remarks;
            this.$ks_buttons = $(values.ks_buttons);
            this.$ks_searchview_buttons = $(values.ks_searchview_html);
            this.ks_currency = values.ks_currency;
            this.ks_report_lines = values.ks_report_lines;
            this.ks_initial_balance = values.ks_initial_balance;
            this.ks_current_balance = values.ks_current_balance;
            this.ks_ending_balance = values.ks_ending_balance;
            this.ks_diff_filter = values.ks_diff_filter;
            this.ks_retained = values.ks_retained;
            this.ks_subtotal = values.ks_subtotal;
            this.ks_partner_dict = values.ks_partner_dict
            this.ks_period_list = values.ks_period_list
            this.ks_period_dict = values.ks_period_dict
            this.ks_month_lines = values.ks_month_lines
            this.ksSaveReportInfo();
        },

        /**
         * @method to save the report Information in current session
        */
        ksSaveReportInfo: function () {
            if ((this.ignore_session === 'write' || this.ignore_session === 'both') !== true) {
                var ks_df_report_key = 'report:' + this.ks_dyn_fin_model + ':' + this.ks_report_id + ':' + session.company_id;
                sessionStorage.setItem(ks_df_report_key, JSON.stringify(this.ks_df_report_opt));
            }
        },

        /**
         * @override
         * @method to rerender the control panel when going back in the breadcrumb
        */
        do_show: function () {
            this._super.apply(this, arguments);
            this.ksUpdateControlPanel();
        },

        /**
         * @method to render the elements that have yet to be rendered
        */
        ksUpdateControlPanel: function () {
            var status = {
                cp_content: {
                    $buttons: this.$ks_buttons,
                    $searchview_buttons: this.$ks_searchview_buttons,
                    $pager: this.$pager,
                    $searchview: this.$searchview,
                },
            };
            return this.updateControlPanel(status);
        },

        /**
         * @method to reload the report content
        */
        ksReloadReport: function () {
            var self = this;
            return this._rpc({
                    model: this.ks_dyn_fin_model,
                    method: 'ks_get_dynamic_fin_info',
                    args: [self.ks_report_id, self.ks_df_report_opt],
                    context: self.ks_df_context,
                })
                .then(function (result) {
                    self.ksSetReportInfo(result);
                    self.ksRenderReport();
                    return self.ksUpdateControlPanel();
                });
        },

        /**
         * @method to render report body
         */
        ksRenderReport: function () {
            var self = this;
            this.ksRenderMainTemplate();
            this.ksRenderSearchViewButtons();
            this.ksUpdateControlPanel();
        },

        /**
         * @method to get general ledger line by page
        */
        ksGetGlLineByPage: function (offset, account_id) {
            var self = this;

            return self._rpc({
                model: self.ks_dyn_fin_model,
                method: 'ks_build_detailed_gen_move_lines',
                args: [self.ks_report_id, offset, account_id, self.ks_df_report_opt],
            });
        },

        /**
         * @method to get move line by page
        */
        ksGetMoveLines: function (event) {
            event.preventDefault();
            var self = this;
            var account_id = $(event.currentTarget).data('account-id');
            var offset = 0;
            var td = $(event.currentTarget).next('tr').find('td');

            if (td.length == 1) {
                self.ksGetGlLineByPage(offset, account_id).then(function (datas) {
                    _.each(datas[2], function (k, v) {
                        var ksFormatConfigurations = {
                            currency_id: k.company_currency_id,
                            noSymbol: true,
                        };
                        k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
                        k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
                        k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '');
                        k.ldate = field_utils.format.date(field_utils.parse.date(k.ldate, {}, {
                            isUTC: true
                        }));
                    });
                    $(event.currentTarget).next('tr').find('td .ks_py-mline-table-div').remove();
                    $(event.currentTarget).next('tr').find('td ul').after(
                        QWeb.render('ks_df_gl_subsection', {
                            count: datas[0],
                            offset: datas[1],
                            account_data: datas[2],
                        }))
                    $(event.currentTarget).next('tr').find('td ul li:first a').css({
                        'background-color': '#00ede8',
                        'font-weight': 'bold',
                    });
                })
            }
        },

        /**
         * @method to get profit and loss lines by page
        */
        ksGetPlLinesByPage: function (offset, account_id) {
            var self = this;
            return self._rpc({
                model: self.ks_dyn_fin_model,
                method: 'ks_build_detailed_move_lines',
                args: [self.ks_report_id, offset, account_id, self.ks_df_report_opt, self.$ks_searchview_buttons.find('.ks_search_account_filter').length],
            })

        },

        /**
         * @method to get profit and loss move lines
        */
        ksGetPlMoveLines: function (event) {
            event.preventDefault();
            var self = this;
            var account_id = $(event.currentTarget).data('account-id');
            var offset = 0;
            var td = $(event.currentTarget).next('tr').find('td');
            if (td.length == 1) {
                self.ksGetPlLinesByPage(offset, account_id).then(function (datas) {
                    _.each(datas[2], function (k, v) {
                        var ksFormatConfigurations = {
                            currency_id: k.company_currency_id,
                            noSymbol: true,
                        };
                        k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
                        k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
                        k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '');
                        k.ldate = field_utils.format.date(field_utils.parse.date(k.ldate, {}, {
                            isUTC: true
                        }));
                    });
                    $(event.currentTarget).next('tr').find('td .ks_py-mline-table-div').remove();
                    $(event.currentTarget).next('tr').find('td ul').after(
                        QWeb.render('ks_df_sub_pl0', {
                            count: datas[0],
                            offset: datas[1],
                            account_data: datas[2],
                        }))
                    $(event.currentTarget).next('tr').find('td ul li:first a').css({
                        'background-color': '#00ede8',
                        'font-weight': 'bold',
                    });
                })
            }
        },

        /**
         * @method to get Aged Report move lines detailed information
        */
        ksGetAgedReportDetailedInfo: function (offset, partner_id) {
            var self = this;
            return self._rpc({
                model: self.ks_dyn_fin_model,
                method: 'ks_process_aging_data',
                args: [self.ks_report_id, self.ks_df_report_opt, offset, partner_id],
            })
        },

        /**
         * @method to get Aged Report lines information
        */
        ksGetAgedLinesInfo: function (event) {
            event.preventDefault();
            var self = this;
            var partner_id = $(event.currentTarget).data('partner-id');
            var offset = 0;
            var td = $(event.currentTarget).next('tr').find('td');
            if (td.length == 1) {
                self.ksGetAgedReportDetailedInfo(offset, partner_id).then(function (datas) {
                    var count = datas[0];
                    var offset = datas[1];
                    var account_data = datas[2];
                    var period_list = datas[3];
                    _.each(account_data, function (k, v) {
                        var ksFormatConfigurations = {
                            currency_id: k.company_currency_id,
                            noSymbol: true,
                        };
                        k.range_0 = self.ksFormatCurrencySign(k.range_0, ksFormatConfigurations, k.range_0 < 0 ? '-' : '');
                        k.range_1 = self.ksFormatCurrencySign(k.range_1, ksFormatConfigurations, k.range_1 < 0 ? '-' : '');
                        k.range_2 = self.ksFormatCurrencySign(k.range_2, ksFormatConfigurations, k.range_2 < 0 ? '-' : '');
                        k.range_3 = self.ksFormatCurrencySign(k.range_3, ksFormatConfigurations, k.range_3 < 0 ? '-' : '');
                        k.range_4 = self.ksFormatCurrencySign(k.range_4, ksFormatConfigurations, k.range_4 < 0 ? '-' : '');
                        k.range_5 = self.ksFormatCurrencySign(k.range_5, ksFormatConfigurations, k.range_5 < 0 ? '-' : '');
                        k.range_6 = self.ksFormatCurrencySign(k.range_6, ksFormatConfigurations, k.range_6 < 0 ? '-' : '');
                        k.date_maturity = field_utils.format.date(field_utils.parse.date(k.date_maturity, {}, {
                            isUTC: true
                        }));
                    });
                    $(event.currentTarget).next('tr').find('td .ks_py-mline-table-div').remove();
                    $(event.currentTarget).next('tr').find('td ul').after(
                        QWeb.render('ks_df_sub_receivable0', {
                            count: count,
                            offset: offset,
                            account_data: account_data,
                            period_list: period_list
                        }))
                    $(event.currentTarget).next('tr').find('td ul li:first a').css({
                        'background-color': '#00ede8',
                        'font-weight': 'bold',
                    });
                })
            }
        },

        /**
         * @method to get Consolidate lines by page
        */
        ksGetConsolidateLinesByPage: function (offset, ks_journal_id) {
            var self = this;
            return self._rpc({
                model: self.ks_dyn_fin_model,
                method: 'ks_consolidate_journals_details',
                args: [self.ks_report_id, offset, ks_journal_id, self.ks_df_report_opt],
            })
        },

        /**
         * @method to get Consolidate move lines
        */
        ksGetConsolidateInfo: function (event) {
            event.preventDefault();
            var self = this;
            var ks_journal_id = $(event.currentTarget).data('journal-id');
            var offset = 0;
            var td = $(event.currentTarget).next('tr').find('td');
            if (td.length == 1) {
                self.ksGetConsolidateLinesByPage(offset, ks_journal_id).then(function (datas) {
                    var offset = datas[0];
                    var account_data = datas[1];
                    _.each(account_data, function (k, v) {
                        var ksFormatConfigurations = {
                            currency_id: k.company_currency_id,
                            noSymbol: true,
                        };
                        k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
                        k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
                        k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '');
                        k.ldate = field_utils.format.date(field_utils.parse.date(k.ldate, {}, {
                            isUTC: true
                        }));
                    });
                    $(event.currentTarget).next('tr').find('td .ks_py-mline-table-div').remove();
                    $(event.currentTarget).next('tr').find('td ul').after(
                        QWeb.render('ks_df_cj_subsection', {
                            offset: offset,
                            account_data: account_data,
                        }))
                    $(event.currentTarget).next('tr').find('td ul li:first a').css({
                        'background-color': '#00ede8',
                        'font-weight': 'bold',
                    });
                })
            }
        },

        /**
         * @method to render searchview buttons
        */
        ksRenderSearchViewButtons: function () {
            var self = this;
            // bind searchview buttons/filter to the correct actions

            var $datetimepickers = this.$ks_searchview_buttons.find('.js_account_reports_datetimepicker');
            var options = { // Set the options for the datetimepickers
                locale: moment.locale(),
                format: 'L',
                icons: {
                    date: "fa fa-calendar",
                },
            };
            // attach datepicker
            $datetimepickers.each(function () {
                var name = $(this).find('input').attr('name');
                var defaultValue = $(this).data('default-value');
                $(this).datetimepicker(options);
                var dt = new datepicker.DateWidget(options);
                dt.replace($(this)).then(function () {
                    dt.$el.find('input').attr('name', name);
                    if (defaultValue) { // Set its default value if there is one
                        dt.setValue(moment(defaultValue));
                    }
                });
            });
            // format date that needs to be show in user lang
            _.each(this.$ks_searchview_buttons.find('.js_format_date'), function (dt) {
                var date_value = $(dt).html();
                $(dt).html((new moment(date_value)).format('ll'));
            });
            //        // fold all menu
            this.$ks_searchview_buttons.find('.js_foldable_trigger').click(function (event) {
                $(this).toggleClass('o_closed_menu o_open_menu');
                self.$ks_searchview_buttons.find('.o_foldable_menu[data-filter="' + $(this).data('filter') + '"]').toggleClass('o_closed_menu');
            });
            //        // render filter (add selected class to the options that are selected)
            _.each(self.ks_df_report_opt, function (k) {
                if (k !== null && k.ks_filter !== undefined) {
                    self.$ks_searchview_buttons.find('[data-filter="' + k.ks_filter + '"]').addClass('selected');
                }
                else if(k !== null && k.ks_differentiate_filter !== undefined){
                self.$ks_searchview_buttons.find('[data-filter="' + k.ks_differentiate_filter + '"]').addClass('selected');
                }
            });
            _.each(this.$ks_searchview_buttons.find('.js_account_report_bool_filter'), function (k) {
                $(k).toggleClass('selected', self.ks_df_report_opt[$(k).data('filter')]);
            });
            _.each(this.$ks_searchview_buttons.find('.js_account_report_choice_filter'), function (k) {
                $(k).toggleClass('selected', (_.filter(self.ks_df_report_opt[$(k).data('filter')], function (el) {
                    return '' + el.id == '' + $(k).data('id') && el.selected === true;
                })).length > 0);
            });
            $('.js_account_report_group_choice_filter', this.$ks_searchview_buttons).each(function (i, el) {
                var $el = $(el);
                var ids = $el.data('member-ids');
                $el.toggleClass('selected', _.every(self.ks_df_report_opt[$el.data('filter')], function (member) {
                    // only look for actual ids, discard separators and section titles
                    if (typeof member.id == 'number') {
                        // true if selected and member or non member and non selected
                        return member.selected === (ids.indexOf(member.id) > -1);
                    } else {
                        return true;
                    }
                }));
            });
            _.each(this.$ks_searchview_buttons.find('.js_account_reports_one_choice_filter'), function (k) {
                $(k).toggleClass('selected', '' + self.ks_df_report_opt[$(k).data('filter')] === '' + $(k).data('id'));
            });
            // click events
            this.$ks_searchview_buttons.find('.js_account_report_date_filter').click(function (event) {
                self.ks_df_context.ks_option_enable = false;
                self.ks_df_context.ks_journal_enable = false
                self.ks_df_context.ks_account_enable = false
                self.ks_df_context.ks_account_both_enable = false
                self.ks_df_report_opt.date.ks_filter = $(this).data('filter');
                var error = false;
                if ($(this).data('filter') === 'custom') {
                    var ks_start_date = self.$ks_searchview_buttons.find('.o_datepicker_input[name="ks_start_date"]');
                    var ks_end_date = self.$ks_searchview_buttons.find('.o_datepicker_input[name="ks_end_date"]');
                    if (ks_start_date.length > 0) {
                        error = ks_start_date.val() === "" || ks_end_date.val() === "";
                        self.ks_df_report_opt.date.ks_start_date = field_utils.parse.date(ks_start_date.val());
                        self.ks_df_report_opt.date.ks_end_date = field_utils.parse.date(ks_end_date.val());
                    } else {
                        error = ks_end_date.val() === "";
                        self.ks_df_report_opt.date.ks_end_date = field_utils.parse.date(ks_end_date.val());
                    }
                }
//                if (error) {
                if (false) {
//                    new WarningDialog(self, {
//                        title: _t("Odoo Warning"),
//                    }, {
//                        message: _t("Date cannot be empty")
//                    }).open();
                } else {
                    self.ksReloadReport();
                }
            });
            this.$ks_searchview_buttons.find('.js_account_report_bool_filter').click(function (event) {
                var option_value = $(this).data('filter');
                self.ks_df_context.ks_option_enable = false;
                self.ks_df_context.ks_journal_enable = false
                self.ks_df_context.ks_account_enable = false
                self.ks_df_context.ks_account_both_enable = false
                var ks_options_enable = false
                if (!$(event.currentTarget).hasClass('selected')){
                    var ks_options_enable = true
                }
                var ks_temp_arr = []
                var ks_options = $(event.currentTarget).parent().find('a')
                for (var i=0; i < ks_options.length; i++){
                    if (ks_options[i].dataset.filter !== option_value){
                        ks_temp_arr.push($(ks_options[i]).hasClass('selected'))
                    }
                }
                if (ks_temp_arr.indexOf(true) !== -1 || ks_options_enable){
                    self.ks_df_context.ks_option_enable = true;
                }else{
                    self.ks_df_context.ks_option_enable = false;
                }

                if(option_value=='ks_comparison_range'){
                    var ks_date_range_change = {}
                    ks_date_range_change['ks_comparison_range'] =!self.ks_df_report_opt[option_value]
                    return self._rpc({
                    model: self.ks_dyn_fin_model,
                    method: 'write',
                    args: [self.ks_report_id, ks_date_range_change],
                    }).then(function (res) {
                        self._rpc({
                        model: self.ks_dyn_fin_model,
                        method: 'ks_reload_page',
                        }).then(function (action){
                            self.do_action(action)
                        });
                    });
                }
                else if(option_value!='ks_comparison_range'){
                    self.ks_df_report_opt[option_value]= !self.ks_df_report_opt[option_value]
                }
                if (option_value === 'unfold_all') {
                    self.unfold_all(self.ks_df_report_opt[option_value]);
                }
                self.ksReloadReport();
            });
            $('.js_account_report_group_choice_filter', this.$ks_searchview_buttons).click(function () {
                var option_value = $(this).data('filter');
                var option_member_ids = $(this).data('member-ids') || [];
                var is_selected = $(this).hasClass('selected');
                _.each(self.ks_df_report_opt[option_value], function (el) {
                    // if group was selected, we want to uncheck all
                    el.selected = !is_selected && (option_member_ids.indexOf(Number(el.id)) > -1);
                });
                self.ksReloadReport();
            });
            this.$ks_searchview_buttons.find('.js_account_report_choice_filter').click(function (event) {
                self.ks_df_context.ks_journal_enable = false
                self.ks_df_context.ks_account_enable = false
                self.ks_df_context.ks_account_both_enable = false

                self.ks_df_context.ks_option_enable = false;

                var option_value = $(this).data('filter');
                var option_id = $(this).data('id');

                if (!$(event.currentTarget).hasClass('selected')){
                    var ks_options_enable = true
                }
                var ks_temp_arr = []
                var ks_options = $(event.currentTarget).parent().find('a')
                for (var i=0; i < ks_options.length; i++){
                    if (parseInt(ks_options[i].dataset.id) !== option_id){
                        ks_temp_arr.push($(ks_options[i]).hasClass('selected'))
                    }
                }
                if (option_value === 'account'){
                    if (ks_temp_arr.indexOf(true) !== -1 || ks_options_enable){
                        self.ks_df_context.ks_account_enable = true;
                    }
                }
                if (option_value === 'journals'){
                    if (ks_temp_arr.indexOf(true) !== -1 || ks_options_enable){
                        self.ks_df_context.ks_journal_enable = true;
                    }
                }
                if (option_value === 'account_type'){
                    if (ks_temp_arr.indexOf(true) !== -1 || ks_options_enable){
                        self.ks_df_context.ks_account_both_enable = true;
                    }
                }

//
                _.filter(self.ks_df_report_opt[option_value], function (el) {
                    if ('' + el.id == '' + option_id) {
                        if (el.selected === undefined || el.selected === null) {
                            el.selected = false;
                        }
                        el.selected = !el.selected;
                    } else if (option_value === 'ir_filters') {
                        el.selected = false;
                    }
                    return el;
                });
                self.ksReloadReport();
            });
            var rate_handler = function (event) {
                var option_value = $(this).data('filter');
                if (option_value == 'current_currency') {
                    delete self.report_options.currency_rates;
                } else if (option_value == 'custom_currency') {
                    _.each($('input.js_account_report_custom_currency_input'), function (input) {
                        self.report_options.currency_rates[input.name].rate = input.value;
                    });
                }
                self.ksReloadReport();
            }
            $(document).on('click', '.js_account_report_custom_currency', rate_handler);
            this.$ks_searchview_buttons.find('.js_account_report_custom_currency').click(rate_handler);
            this.$ks_searchview_buttons.find('.js_account_reports_one_choice_filter').click(function (event) {
                self.ks_df_report_opt[$(this).data('filter')] = $(this).data('id');
                self.ksReloadReport();
            });
            this.$ks_searchview_buttons.find('.js_account_report_date_cmp_filter').click(function (event) {
                self.ks_df_context.ks_option_enable = false;
                self.ks_df_context.ks_journal_enable = false
                self.ks_df_context.ks_account_enable = false
                self.ks_df_context.ks_account_both_enable = false
                self.ks_df_report_opt.ks_differ.ks_differentiate_filter = $(this).data('filter');
                if (self.ks_df_report_opt.ks_differ.ks_differentiate_filter == "no_differentiation") {
                    self.ks_df_report_opt.ks_diff_filter.ks_diff_filter_enablity = false
                    self.ks_df_report_opt.ks_diff_filter.ks_debit_credit_visibility = true
                }
                if (self.ks_df_report_opt.ks_differ.ks_differentiate_filter != "no_differentiation") {
                    self.ks_df_report_opt.ks_diff_filter.ks_diff_filter_enablity = true
                    self.ks_df_report_opt.ks_diff_filter.ks_debit_credit_visibility = false
                }
                var error = false;
                var number_period = $(this).parent().find('input[name="periods_number"]');
                self.ks_df_report_opt.ks_differ.ks_no_of_interval = (number_period.length > 0) ? parseInt(number_period.val()) : 1;
                if ($(this).data('filter') === 'custom') {
                    var ks_start_date = self.$ks_searchview_buttons.find('.o_datepicker_input[name="date_from_cmp"]');
                    var ks_end_date = self.$ks_searchview_buttons.find('.o_datepicker_input[name="date_to_cmp"]');
                    if (ks_start_date.length > 0) {
                        error = ks_start_date.val() === "" || ks_end_date.val() === "";
                        self.ks_df_report_opt.ks_differ.ks_start_date = field_utils.parse.date(ks_start_date.val());
                        self.ks_df_report_opt.ks_differ.ks_end_date = field_utils.parse.date(ks_end_date.val());
                    } else {
                        error = ks_end_date.val() === "";
                        self.ks_df_report_opt.ks_differ.ks_end_date = field_utils.parse.date(ks_end_date.val());
                    }
                }
//                if (error) {
                if (false) {
//                    new WarningDialog(self, {
//                        title: _t("Odoo Warning"),
//                    }, {
//                        message: _t("Date cannot be empty")
//                    }).open();
                } else {
                    self.ksReloadReport();
                }
            });

            // partner filter
            if (this.ks_df_report_opt.ks_partner) {
                if (!this.ksMany2Many) {
                    var fields = {};
                    if ('ks_partner_ids' in this.ks_df_report_opt) {
                        fields['ks_partner_ids'] = {
                            label: _t('Partners'),
                            modelName: 'res.partner',
                            value: this.ks_df_report_opt.ks_partner_ids.map(Number),
                        };
                    }
                    if (!_.isEmpty(fields)) {
                        this.ksMany2Many = new ksMany2ManyWidget(this, fields);
                        this.ksMany2Many.appendTo(this.$ks_searchview_buttons.find('.js_account_partner_m2m'));
                    }
                } else {
                    this.$ks_searchview_buttons.find('.js_account_partner_m2m').append(this.ksMany2Many.$el);
                }
            }
            if (this.ks_df_report_opt.analytic) {
                if (!this.ksMany2Many) {
                    var fields = {};
                    if (this.ks_df_report_opt.analytic_accounts) {
                        fields['ks_analytic_ids'] = {
                            label: _t('Accounts'),
                            modelName: 'account.analytic.account',
                            value: this.ks_df_report_opt.analytic_accounts.map(Number),
                        };
                    }
                    if (this.ks_df_report_opt.analytic_tags) {
                        fields['ks_analytic_tag_ids'] = {
                            label: _t('Tags'),
                            modelName: 'account.analytic.tag',
                            value: this.ks_df_report_opt.analytic_tags.map(Number),
                        };
                    }
                    if (!_.isEmpty(fields)) {
                        this.ksMany2Many = new ksMany2ManyWidget(this, fields);
                        this.ksMany2Many.appendTo(this.$ks_searchview_buttons.find('.js_account_analytic_m2m'));
                    }
                } else {
                    this.$ks_searchview_buttons.find('.js_account_analytic_m2m').append(this.ksMany2Many.$el);
                }
            }

        },

        /**
         * @method to render main template
        */
        ksRenderMainTemplate: function () {
            this.ksRenderBody();
        },

        /**
         * @method to render report body and currency conversion
        */
        ksRenderBody: function () {
            var self = this;

            var ksFormatConfigurations = {
                currency_id: self.ks_currency,
                noSymbol: true,
            };
            self.initial_balance = self.ksFormatCurrencySign(self.ks_initial_balance, ksFormatConfigurations, self.ks_initial_balance < 0 ? '-' : '');
            self.current_balance = self.ksFormatCurrencySign(self.ks_current_balance, ksFormatConfigurations, self.ks_current_balance < 0 ? '-' : '');
            self.ending_balance = self.ksFormatCurrencySign(self.ks_ending_balance, ksFormatConfigurations, self.ks_ending_balance < 0 ? '-' : '');

            if (self._title != _t("Tax Report") && self._title != _t("Executive Summary")) {
                self.ksSetReportCurrencyConfig();
            } else if (self._title == _t("Tax Report")) {
                self.ksSetTaxReportCurrencyConfig();
            } else if (self._title == _t("Executive Summary")) {
                self.ksSetExecutiveReportCurrencyConfig();
            }

            if (self._title == _t("General Ledger")) {
                self.ksRenderGeneralLedger();
            } else if (self._title == _t("Trial Balance")) {
                self.ksRenderTrialBalance();
            } else if (self._title == _t("Partner Ledger")) {
                self.ksRenderPartnerLedger();
            } else if (self._title == _t("Consolidate Journal")) {
                self.ksRenderConsolidateJournal();
            } else if (self._title == _t("Age Receivable")) {
                self.ksRenderAgeReceivable();
            } else if (self._title == _t("Age Payable")) {
                self.ksRenderAgePayable();
            } else if (self._title == _t("Tax Report")) {
                self.ksRenderTaxReport();
            } else if (self._title == _t("Executive Summary")) {
                self.ksRenderExecutiveSummary();
            } else {
                self.ksRenderGenericReport();
            }
        },

        /**
         * @method to render general ledger report
        */
        ksRenderGeneralLedger: function(){
            var self = this;

            self.$('.o_content').html(QWeb.render('ks_df_gl', {
                    ks_report_lines: self.ks_report_lines
                }));
        },

        /**
         * @method to render trial balance report
        */
        ksRenderTrialBalance: function(){
            var self = this;

            _.each(self.ks_report_lines, function (k, v) {
                    var ksFormatConfigurations = {
                        currency_id: k.company_currency_id,
                        noSymbol: true,
                    };
                    k.initial_debit = self.ksFormatCurrencySign(k.initial_debit, ksFormatConfigurations, k.initial_debit < 0 ? '-' : '');
                    k.initial_credit = self.ksFormatCurrencySign(k.initial_credit, ksFormatConfigurations, k.initial_credit < 0 ? '-' : '');
                    k.initial_balance = self.ksFormatCurrencySign(k.initial_balance, ksFormatConfigurations, k.initial_balance < 0 ? '-' : '');
                    k.ending_debit = self.ksFormatCurrencySign(k.ending_debit, ksFormatConfigurations, k.ending_debit < 0 ? '-' : '');
                    k.ending_credit = self.ksFormatCurrencySign(k.ending_credit, ksFormatConfigurations, k.ending_credit < 0 ? '-' : '');
                    k.ending_balance = self.ksFormatCurrencySign(k.ending_balance, ksFormatConfigurations, k.ending_balance < 0 ? '-' : '');
                });
            _.each(self.ks_retained, function (k, v) {
                var ksFormatConfigurations = {
                    currency_id: k.company_currency_id,
                    noSymbol: true,
                };
                k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
                k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
                k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '');
                k.initial_debit = self.ksFormatCurrencySign(k.initial_debit, ksFormatConfigurations, k.initial_debit < 0 ? '-' : '');
                k.initial_credit = self.ksFormatCurrencySign(k.initial_credit, ksFormatConfigurations, k.initial_credit < 0 ? '-' : '');
                k.initial_balance = self.ksFormatCurrencySign(k.initial_balance, ksFormatConfigurations, k.initial_balance < 0 ? '-' : '');
                k.ending_debit = self.ksFormatCurrencySign(k.ending_debit, ksFormatConfigurations, k.ending_debit < 0 ? '-' : '');
                k.ending_credit = self.ksFormatCurrencySign(k.ending_credit, ksFormatConfigurations, k.ending_credit < 0 ? '-' : '');
                k.ending_balance = self.ksFormatCurrencySign(k.ending_balance, ksFormatConfigurations, k.ending_balance < 0 ? '-' : '');
            });
            _.each(self.ks_subtotal, function (k, v) {
                    var ksFormatConfigurations = {
                        currency_id: k.company_currency_id,
                        noSymbol: true,
                    };
                    k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
                    k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
                    k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '');
                    k.initial_debit = self.ksFormatCurrencySign(k.initial_debit, ksFormatConfigurations, k.initial_debit < 0 ? '-' : '');
                    k.initial_credit = self.ksFormatCurrencySign(k.initial_credit, ksFormatConfigurations, k.initial_credit < 0 ? '-' : '');
                    k.initial_balance = self.ksFormatCurrencySign(k.initial_balance, ksFormatConfigurations, k.initial_balance < 0 ? '-' : '');
                    k.ending_debit = self.ksFormatCurrencySign(k.ending_debit, ksFormatConfigurations, k.ending_debit < 0 ? '-' : '');
                    k.ending_credit = self.ksFormatCurrencySign(k.ending_credit, ksFormatConfigurations, k.ending_credit < 0 ? '-' : '');
                    k.ending_balance = self.ksFormatCurrencySign(k.ending_balance, ksFormatConfigurations, k.ending_balance < 0 ? '-' : '');
                });

            self.$('.o_content').html(QWeb.render('ks_df_trial_balance', {
                    account_data: self.ks_report_lines,
                    retained: self.ks_retained,
                    ks_df_report_opt: self.ks_df_report_opt,
                    subtotal: self.ks_subtotal,
                }));
        },

        /**
         * @method to render partner ledger report
        */
        ksRenderPartnerLedger: function(){
            var self = this;

            self.$('.o_content').html(QWeb.render('ks_df_pl0', {
                    ks_report_lines: self.ks_report_lines
                }));
        },

        /**
         * @method to render consolidate journal report
        */
        ksRenderConsolidateJournal: function(){
            var self = this;

            _.each(self.ks_month_lines, function (k, v) {
                    var ksFormatConfigurations = {
                        currency_id: k.company_currency_id,
                        noSymbol: true,
                    };
                    k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
                    k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
                    k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '')

                });
            self.$('.o_content').html(QWeb.render('ks_df_cj0', {
                    ks_report_lines: self.ks_report_lines,
                    ks_month_lines: self.ks_month_lines
                }));
        },

        /**
         * @method to render Age Receivable report
        */
        ksRenderAgeReceivable: function(){
            var self = this;

            _.each(self.ks_partner_dict, function (k, v) {
                    var ksFormatConfigurations = {
                        currency_id: k.company_currency_id,
                        noSymbol: true,
                    };
                    for (var z = 0; z < self.ks_period_list.length; z++) {
                        k[self.ks_period_list[z]] = self.ksFormatCurrencySign(k[self.ks_period_list[z]], ksFormatConfigurations, k[self.ks_period_list[z]] < 0 ? '-' : '');
                    }
                    k.total = self.ksFormatCurrencySign(k.total, ksFormatConfigurations, k.total < 0 ? '-' : '');
                });
            self.$('.o_content').html(QWeb.render('ks_df_rec0', {
                    ks_period_list: self.ks_period_list,
                    ks_period_dict: self.ks_period_dict,
                    ks_partner_dict: self.ks_partner_dict,
                }));
        },

        /**
         * @method to render Age Payable report
        */
        ksRenderAgePayable: function(){
            var self = this;

            _.each(self.ks_partner_dict, function (k, v) {
                var ksFormatConfigurations = {
                    currency_id: k.company_currency_id,
                    noSymbol: true,
                };
                for (var z = 0; z < self.ks_period_list.length; z++) {
                    k[self.ks_period_list[z]] = self.ksFormatCurrencySign(k[self.ks_period_list[z]], ksFormatConfigurations, k[self.ks_period_list[z]] < 0 ? '-' : '');
                }
                k.total = self.ksFormatCurrencySign(k.total, ksFormatConfigurations, k.total < 0 ? '-' : '');
            });
            self.$('.o_content').html(QWeb.render('ks_df_rec0', {
                    ks_period_list: self.ks_period_list,
                    ks_period_dict: self.ks_period_dict,
                    ks_partner_dict: self.ks_partner_dict,
                }));
        },

        /**
         * @method to render Tax report
        */
        ksRenderTaxReport: function(){
            var self = this;

            self.$('.o_content').html(QWeb.render('ks_tax_report_lines', {
                    ks_report_lines: self.ks_report_lines,
                    ks_df_report_opt: self.ks_df_report_opt
                }));
        },

        /**
         * @method to render Executive summary report
        */
        ksRenderExecutiveSummary: function(){
            var self = this;

            self.$('.o_content').html(QWeb.render('ks_executive_summary_lines', {
                    ks_report_lines: self.ks_report_lines,
                    ks_df_report_opt: self.ks_df_report_opt

                }));

            if (parseFloat(self.ks_initial_balance) > 0 || parseFloat(self.ks_current_balance) > 0 || parseFloat(self.ks_ending_balance) > 0) {
                    self.$(".o_content").append(QWeb.render('ks_account_report_summary_section', {
                        ks_initial_balance: self.ks_initial_balance,
                        ks_current_balance: self.ks_current_balance,
                        ks_ending_balance: self.ks_ending_balance
                    }));
                }
        },

        /**
         * @method to render Generic summary report
        */
        ksRenderGenericReport: function(){
            var self = this;

            self.$('.o_content').html(QWeb.render('ks_account_report_lines', {
                    ks_report_lines: self.ks_report_lines,
                    ks_df_report_opt: self.ks_df_report_opt

                }));

            if (parseFloat(self.ks_initial_balance) > 0 || parseFloat(self.ks_current_balance) > 0 || parseFloat(self.ks_ending_balance) > 0) {
                    self.$(".o_content").append(QWeb.render('ks_account_report_summary_section', {
                        ks_initial_balance: self.ks_initial_balance,
                        ks_current_balance: self.ks_current_balance,
                        ks_ending_balance: self.ks_ending_balance
                    }));
                }
        },

        /**
         * @method to set report currency configuration
        */
        ksSetReportCurrencyConfig: function() {
            var self = this;

            _.each(self.ks_report_lines, function (k, v) {
                    var ksFormatConfigurations = {
                        currency_id: k.company_currency_id,
                        noSymbol: true,
                    };
                    k.debit = self.ksFormatCurrencySign(k.debit, ksFormatConfigurations, k.debit < 0 ? '-' : '');
                    k.credit = self.ksFormatCurrencySign(k.credit, ksFormatConfigurations, k.credit < 0 ? '-' : '');
                    //  changed the values of balance
                    if (!k['percentage']) {
                        k.balance = self.ksFormatCurrencySign(k.balance, ksFormatConfigurations, k.balance < 0 ? '-' : '');
                    } else {
                        k.balance = String(Math.round(k.balance)) + "%";
                    }

                    for (const prop in k.balance_cmp) {
                        k.balance_cmp[prop] = self.ksFormatCurrencySign(k.balance_cmp[prop], ksFormatConfigurations, k.balance[prop] < 0 ? '-' : '');
                    }
                });
        },

        /**
         * @method to set tax report currency configuration
        */
        ksSetTaxReportCurrencyConfig: function() {
            var self = this;

            _.each(self.ks_report_lines, function (k, v) {
                    var ksFormatConfigurations = {
                        currency_id: k.company_currency_id,
                        noSymbol: true,
                    };
                    k.ks_net_amount = self.ksFormatCurrencySign(k.ks_net_amount, ksFormatConfigurations, k.ks_net_amount < 0 ? '-' : '');
                    k.tax = self.ksFormatCurrencySign(k.tax, ksFormatConfigurations, k.tax < 0 ? '-' : '');

                    for (const prop in k.balance_cmp) {
                        k.balance_cmp[prop][0]['ks_com_net'] = self.ksFormatCurrencySign(k.balance_cmp[prop][0]['ks_com_net'], ksFormatConfigurations, k.balance_cmp[prop][0]['ks_com_net'] < 0 ? '-' : '');
                        k.balance_cmp[prop][1]['ks_com_tax'] = self.ksFormatCurrencySign(k.balance_cmp[prop][1]['ks_com_tax'], ksFormatConfigurations, k.balance_cmp[prop][1]['ks_com_tax'] < 0 ? '-' : '');
                    }
                });
        },

        /**
         * @method to set tax report currency configuration
        */
        ksSetExecutiveReportCurrencyConfig: function() {
            var self = this;

             _.each(self.ks_report_lines, function (k, v) {
                    var ksFormatConfigurations = {
                        currency_id: k.company_currency_id,
                        noSymbol: true,
                    };

                    for (const prop in k.debit) {
                        k.debit[prop] = self.ksFormatCurrencySign(k.debit[prop], ksFormatConfigurations, k.debit[prop] < 0 ? '-' : '');
                    }
                    for (const prop in k.credit) {
                        k.credit[prop] = self.ksFormatCurrencySign(k.credit[prop], ksFormatConfigurations, k.credit[prop] < 0 ? '-' : '');
                    }

                    //  changed the values of balance
                    if (!k['percentage']) {
                        for (const prop in k.balance) {
                            k.balance[prop] = self.ksFormatCurrencySign(k.balance[prop], ksFormatConfigurations, k.balance[prop] < 0 ? '-' : '');
                        }
                    } else {
                        for (const prop in k.balance) {
                            k.balance[prop] = String(Math.round(k.balance[prop])) + "%";
                        }
                    }

                    for (const prop in k.balance_cmp) {
                        k.balance_cmp[prop] = self.ksFormatCurrencySign(k.balance_cmp[prop], ksFormatConfigurations, k.balance[prop] < 0 ? '-' : '');
                    }
                });
        },

        /**
         * @method to render report body and currency conversion
        */
        ksGetAction: function (e) {
            e.stopPropagation();
            var self = this;
            var action = $(e.target).attr('action');
            var id = $(e.target).parents('td').data('accountId') || $(e.target).parents('td').data('moveId');
            var params = $(e.target).data();
            var context = new Context(this.ks_df_context, params.actionContext || {}, {
                active_id: id
            });

            params = _.omit(params, 'actionContext');
            if (action) {
                return this._rpc({
                        model: this.ks_dyn_fin_model,
                        method: action,
                        args: [this.ks_report_id, this.ks_df_report_opt, params],
                        context: context.eval(),
                    })
                    .then(function (result) {
                        return self.do_action(result);
                    });
            }
        },

        /**
         * @method to format currnecy with amount
         */
        ksFormatCurrencySign: function (amount, ksFormatConfigurations, sign) {
            var currency_id = ksFormatConfigurations.currency_id;
            currency_id = session.get_currency(currency_id);
            var without_sign = field_utils.format.monetary(Math.abs(amount), {}, ksFormatConfigurations);
            if (!amount) {
                return '-'
            };
            if (currency_id.position === "after") {
                return sign + '&nbsp;' + without_sign + '&nbsp;' + currency_id.symbol;
            } else {
                return currency_id.symbol + '&nbsp;' + sign + '&nbsp;' + without_sign;
            }
            return without_sign;
        },

        /**
         * @method to get the storage session keys
         */
        ksGetStorageKey: function (ks_df_report_key) {
            self.ks_df_report_opt = JSON.parse(sessionStorage.getItem(ks_df_report_key)) || this.ks_df_report_opt;
        },

        /**
         * @method to set the storage session keys
         */
        ksSetStorageKey: function (ks_df_report_key) {
            // set session key
            sessionStorage.setItem(ks_df_report_key, JSON.stringify(this.ks_df_report_opt));
        },

        /**
         * @method to set the information required by Dynamic financial reports
         */
        ksSetDfRepInfo: function (values) {
            this.ks_df_reports_ids= values.ks_df_reports_ids;
            this.ks_df_report_opt = values.ks_df_informations;
            this.ks_df_context = values.context;
            this.ks_report_manager_id = values.ks_report_manager_id;
            this.ks_remarks = values.ks_remarks;
            this.$ks_buttons = $(values.ks_buttons);
            this.$ks_searchview_buttons = $(values.ks_searchview_html);
            this.ks_currency = values.ks_currency;
            this.ks_report_lines = values.ks_report_lines;
            this.ks_initial_balance = values.ks_initial_balance;
            this.ks_current_balance = values.ks_current_balance;
            this.ks_ending_balance = values.ks_ending_balance;
            this.ks_diff_filter = values.ks_diff_filter;
            this.ks_retained = values.ks_retained;
            this.ks_subtotal = values.ks_subtotal;
            this.ks_partner_dict = values.ks_partner_dict;
            this.ks_period_list = values.ks_period_list;
            this.ks_period_dict = values.ks_period_dict;
            this.ks_month_lines = values.ks_month_lines;
            this.ks_sub_lines = values.ks_sub_lines
            this.ksStorageKeyOpt();
        },
    });

    core.action_registry.add('ks_dynamic_report', ksDynamicReportsWidget);
    return ksDynamicReportsWidget;

});


 $(document).ready(function() {
        $(document).on('click', 'header .o_main_navbar', function(evt){
                $('.o_filter_menu').removeClass('ks_d_block')
            });
    });














