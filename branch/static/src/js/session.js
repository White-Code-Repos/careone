odoo.define('branch.Session', function (require) {
"use strict";
var Session = require('web.Session');
var utils = require('web.utils');
Session.include({

    setBranch: function (main_branch_id, branch_ids) {
        var hash = $.bbq.getState()
        hash.bids = branch_ids.sort(function(a, b) {
            if (a === main_branch_id) {
                return -1;
            } else if (b === main_branch_id) {
                return 1;
            } else {
                return a - b;
            }
        }).join(',');
        utils.set_cookie('bids', hash.bids || String(main_branch_id));
        $.bbq.pushState({'bids': hash.bids}, 0);
        location.reload();
    },

    });

});
