odoo.define('branch.SwitchBranchMenu', function(require) {
"use strict";
/**
 * When Odoo is configured in multi-company mode, users should obviously be able
 * to switch their interface from one company to the other.  This is the purpose
 * of this widget, by displaying a dropdown menu in the systray.
 */

var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');
var Widget = require('web.Widget');
var ajax = require('web.ajax');
var rpc = require('web.rpc');
var utils = require('web.utils');
var request
var _t = core._t;

var SwitchBranchMenu = Widget.extend({
    template: 'SwitchBranchMenu',
    events: {
        'click .dropdown-item1[data-menu] div.log_into1': '_onSwitchBranchClick',
        'keydown .dropdown-item1[data-menu] div.log_into1': '_onSwitchBranchClick',
        'click .dropdown-item1[data-menu] div.toggle_branch': '_onToggleBranchClick',
        'keydown .dropdown-item1[data-menu] div.toggle_branch': '_onToggleBranchClick',
    },
    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.isMobile = config.device.isMobile;
        this._onSwitchBranchClick = _.debounce(this._onSwitchBranchClick, 1500, true);
    },

    /**
     * @override
     */
    willStart: function () {
        var self = this;
        this.allowed_branch_ids = session.user_context.allowed_branch_ids
        this.user_branches = session.user_branches.allowed_branch;
        this.current_branch = this.allowed_branch_ids[0];
        if (_.find(session.user_branches.allowed_branch, function (branch) {
            return branch[0] === self.current_branch;
        })){
            this.current_branch_name = _.find(session.user_branches.allowed_branch, function (branch) {
                return branch[0] === self.current_branch;
            })[1];
        }
        else{
            this.current_branch_name =session.user_branches.allowed_branch[0][1]
        }
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {MouseEvent|KeyEvent} ev
     */
    _onSwitchBranchClick: function (ev) {
        if (ev.type == 'keydown' && ev.which != $.ui.keyCode.ENTER && ev.which != $.ui.keyCode.SPACE) {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        var dropdownItem = $(ev.currentTarget).parent();
        var dropdownMenu = dropdownItem.parent();
        var branchID = dropdownItem.data('branch-id');
        var allowed_branch_ids = this.allowed_branch_ids;
        if (dropdownItem.find('.fa-square-o').length) {
            // 1 enabled company: Stay in single company mode
            if (this.allowed_branch_ids.length === 1) {
                if (this.isMobile) {
                    dropdownMenu = dropdownMenu.parent();
                }
                dropdownMenu.find('.fa-check-square').removeClass('fa-check-square').addClass('fa-square-o');
                dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
                allowed_branch_ids = [branchID];
            } else { // Multi company mode
                allowed_branch_ids.push(branchID);
                dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
            }
        }
        $(ev.currentTarget).attr('aria-pressed', 'true');
        session.setBranch(branchID, allowed_branch_ids);

        ajax.jsonRpc('/set_brnach', 'call', {
                    'BranchID':  branchID,
            })
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {MouseEvent|KeyEvent} ev
     */
    _onToggleBranchClick: function (ev) {
        if (ev.type == 'keydown' && ev.which != $.ui.keyCode.ENTER && ev.which != $.ui.keyCode.SPACE) {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        var dropdownItem = $(ev.currentTarget).parent();
        var branchID = dropdownItem.data('branch-id');
        var allowed_branch_ids = this.allowed_branch_ids;
        var current_branch_id = allowed_branch_ids[0];
        if (dropdownItem.find('.fa-square-o').length) {
            allowed_branch_ids.push(branchID);
            dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
            $(ev.currentTarget).attr('aria-checked', 'true');
        } else {
            allowed_branch_ids.splice(allowed_branch_ids.indexOf(branchID), 1);
            dropdownItem.find('.fa-check-square').addClass('fa-square-o').removeClass('fa-check-square');
            $(ev.currentTarget).attr('aria-checked', 'false');
        }
        session.setBranch(current_branch_id, allowed_branch_ids);
    },

});

if (session.display_switch_branch_menu) {
    SystrayMenu.Items.push(SwitchBranchMenu);
}

return SwitchBranchMenu;

});