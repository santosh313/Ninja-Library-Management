// Copyright (c) 2024, santosh sutar and contributors
// For license information, please see license.txt

frappe.ui.form.on('Book', {
    refresh: function(frm) {
        frm.add_custom_button(__('Import Books'), function() {
            frappe.prompt([
                {'fieldname': 'json_data', 'fieldtype': 'Text', 'label': 'JSON Data', 'reqd': 1}
            ],
            function(values){
                frappe.call({
                    method: 'library_managemet.library_managemet.doctype.book.book.import_books',
                    args: {
                        data: JSON.parse(values.json_data),  // Ensure the data is parsed to JSON
                        start: 0,  // Modify as needed for pagination
                        page_length: 20
                    },
                    callback: function(r) {
                        if(r.message.status == "success") {
                            frappe.msgprint(r.message.message);
                        } else {
                            frappe.msgprint(__('Error: ') + r.message.message);
                        }
                    }
                });
            },
            __('Import Books'),
            __('Import')
            );
        });
    }
});
