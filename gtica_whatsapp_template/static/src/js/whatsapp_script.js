odoo.define('gtica_whatsapp_template.ScriptWhatsappOpen', function (require) {
'use strict';

var ActionManager = require('web.ActionManager');

ActionManager.include({
  _executeURLAction: function (action, options) {

        if (action.param === 'whatsapp_action') {
            window.open(action.url , 'MyTabWhatsapp');
            return true
           }
        this._super.apply(this, arguments);

    },
});

return ActionManager;

});