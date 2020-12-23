odoo.define('branch.AbstractWebClient', function (require) {
"use strict";
var AbstractWebClient = require('web.AbstractWebClient');
var ActionManager = require('web.ActionManager');
var concurrency = require('web.concurrency');
var core = require('web.core');
var config = require('web.config');
var WarningDialog = require('web.CrashManager').WarningDialog;
var data_manager = require('web.data_manager');
var dom = require('web.dom');
var KeyboardNavigationMixin = require('web.KeyboardNavigationMixin');
var Loading = require('web.Loading');
var local_storage = require('web.local_storage');
var RainbowMan = require('web.RainbowMan');
var ServiceProviderMixin = require('web.ServiceProviderMixin');
var session = require('web.session');
var utils = require('web.utils');
var Widget = require('web.Widget');

var _t = core._t;
AbstractWebClient.include({

    start: function () {
        var self = this;

        // we add the o_touch_device css class to allow CSS to target touch
        // devices.  This is only for styling purpose, if you need javascript
        // specific behaviour for touch device, just use the config object
        // exported by web.config
        this.$el.toggleClass('o_touch_device', config.device.touch);
        this.on("change:title_part", this, this._title_changed);
        this._title_changed();

        var state = $.bbq.getState();
        // If not set on the url, retrieve cids from the local storage
        // of from the default company on the user
        var current_company_id = session.user_companies.current_company[0]
        var current_branch_id = session.user_branches.current_branch[0]
        if (!state.cids) {
            state.cids = utils.get_cookie('cids') !== null ? utils.get_cookie('cids') : String(current_company_id);
        }
        if (!state.bids) {
            state.bids = utils.get_cookie('bids') !== null ? utils.get_cookie('bids') : String(current_branch_id);
        }
        var stateCompanyIDS = _.map(state.cids.split(','), function (cid) { return parseInt(cid) });
        var userCompanyIDS = _.map(session.user_companies.allowed_companies, function(company) {return company[0]});
        
        var stateBranchIDS = _.map(state.bids.split(','), function (bid) { return parseInt(bid) });
        var userBranchIDS = _.map(session.user_branches.allowed_branch, function(branch) {return branch[0]});
        
        // Check that the user has access to all the companies
        if (!_.isEmpty(_.difference(stateCompanyIDS, userCompanyIDS))) {
            state.cids = String(current_company_id);
            state.bids = String(current_branch_id);
            stateCompanyIDS = [current_company_id];
            stateBranchIDS = [current_branch_id];
        }
        // Update the user context with this configuration
        session.user_context.allowed_company_ids = stateCompanyIDS;
        session.user_context.allowed_branch_ids = stateBranchIDS;
        $.bbq.pushState(state);
        // Update favicon
        $("link[type='image/x-icon']").attr('href', '/web/image/res.company/' + String(stateCompanyIDS[0]) + '/favicon/')

        return session.is_bound
            .then(function () {
                self.$el.toggleClass('o_rtl', _t.database.parameters.direction === "rtl");
                self.bind_events();
                return Promise.all([
                    self.set_action_manager(),
                    self.set_loading()
                ]);
            }).then(function () {
                if (session.session_is_valid()) {
                    return self.show_application();
                } else {
                    // database manager needs the webclient to keep going even
                    // though it has no valid session
                    return Promise.resolve();
                }
            }).then(function () {
                // Listen to 'scroll' event and propagate it on main bus
                self.action_manager.$el.on('scroll', core.bus.trigger.bind(core.bus, 'scroll'));
                core.bus.trigger('web_client_ready');
                odoo.isReady = true;
                if (session.uid === 1) {
                    self.$el.addClass('o_is_superuser');
                }
            });
    },

    _onPushState: function (e) {
        this.do_push_state(_.extend(e.data.state, {'cids': $.bbq.getState().cids,
            'bids': $.bbq.getState().bids}));
    },

    });
});
