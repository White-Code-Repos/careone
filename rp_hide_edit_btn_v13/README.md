RP Show edit button condition based 
----------------------------------------

Overview
--------
This module manages to show edit button based on selection field condition. You just need to provide expression attribute in form tag in form view.

Configuration
-------------
By default create and edit button is visible to user.

To show edit or create button on condition then you need to add condition in which state only you want to show button. To add expression use "rp_edit" or "rp_create" attribute in form view.

```xml
1. Here to show edit button in draft state only:
<field name="arch" type="xml">
    <form string="view name" rp_edit="state == 'draft'">
        <field name="name"/>
    </form>
</field>

2. To show edit button in daft and sent state only:
<field name="arch" type="xml">
    <form string="view name" rp_edit="state in ['draft','sent']">
        <field name="name"/>
    </form>
</field>

3. Here to show create button in draft state only:
```xml
<field name="arch" type="xml">
    <form string="view name" rp_create="state == 'draft'">
        <field name="name"/>
    </form>
</field>``` 

4. To show create button in daft and sent state only:
<field name="arch" type="xml">
    <form string="view name" rp_create="state in ['draft','sent']">
        <field name="name"/>
    </form>
</field>

``` 

Usage
-----
Add attribute in form tag in form view

Sometimes we need to make fields non-editable on some state or for logged in users or users groups.

For state - you can directly give 'rp_edit' or 'rp_create' attribute in form view.

For Logged in users or check on users specific group, in that case generally we give 'Boolean' field and make it computable as non-storable field.
So, Instead of giving 'Boolean' field just give 'Selection' field as computable (non-storable field) and then you can apply 'rp_edit'.

For Example:-

In Sale Order:
```py
can_edit = fields.Selection([('yes','Yes'),('no','No')], string='Can Edit', compute='_compute_can_edit')

@api.depends('name','state')
def _compute_can_edit(self):
    if self.env.user.id == self.user_id.id or self.env.user.user_has_groups('base.group_system'): # you can check weather user has particular group or not.
        self.can_edit = 'yes'
    else:
        self.can_edit = 'no'

``` 
```xml
<xpath expr="//form" position="attributes">
    <attribute name="rp_edit">can_edit == 'yes'</attribute>
</xpath>
<xpath expr="payment_term_id" position="after">
    <field name="can_edit"/>
</xpath>
``` 
In above example: edit button is visible to sales person or Admin rights. 

Connect with experts
--------------------

If you have any question/queries on this module, You can drop an email directly to Us.

Contacts
--------
info - rpodoodeveloper@gmail.com
