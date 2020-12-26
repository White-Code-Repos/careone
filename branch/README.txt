-> 13.0.0.1 

fix method for create vendor bill.


--> 13.0.0.2
in pos receipt not show branches
orders payment not show branches

--> 13.0.0.3
-> Remove pos feature from branch module.


--> 13.0.0.4
-> Solve issue for inventory adjustment when valuation is set automatic.

--> 13.0.0.5
-> Add branch field in picking type related to stock.warehouse and updated the rule from global to user's current branch only for branch user.

--> 13.0.0.6
-> Remove account invoice ref from wizard, update code for sale advanced payment and
pass branch field.

--> 13.0.0.7
-> Call super in all possible methods.
-> Update context all for order lines like sale, purchase, invoice, move and bank statement lines.

Version: 13.0.0.8 | Date : 22/09/2020
-> Give option to select default branch in header and pass selected branch to the records.

Date 23rd sept 2020
version 13.0.0.9
issue solve:-
	- when user need to click two time otherwise need to reload manually , if want to change branch.

Version 13.0.1.0 : (23/10/20)
		- Update _assign_picking() method as per base.