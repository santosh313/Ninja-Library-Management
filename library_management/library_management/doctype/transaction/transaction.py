# Copyright (c) 2024, santosh sutar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff

class Transaction(Document):
    def before_save(self):
        library_settings = frappe.get_single('Library Setting')
        max_books_allowed = library_settings.max_no_of_book_can_be_issued
        rent_fee_per_day = library_settings.rent_fee_per_book_per_day
        max_outstanding_debt = library_settings.max_outstanding_debt

        if not self.get("status") or self.status == 'Issued':
            self.validate_max_books_issued(max_books_allowed)
            self.validate_same_book_issue() 
            self.validate_outstanding_debt(max_outstanding_debt)  
            self.update_book_quantity(-1)  
            self.status = 'Issued'  
        if self.return_date:
            self.complete_transaction(rent_fee_per_day)  

    def validate_max_books_issued(self, max_books_allowed):
        issued_books_count = frappe.db.count('Transaction', {
            'member': self.member,
            'status': 'Issued'
        })

        if issued_books_count >= max_books_allowed:
            frappe.throw(f'Maximum number of books ({max_books_allowed}) already issued.')

    def validate_same_book_issue(self):
        existing_transaction = frappe.db.exists('Transaction', {
            'member': self.member,
            'book': self.book,
            'status': 'Issued'
        })

        if existing_transaction:
            frappe.throw('This book is already issued to the member and has not been returned yet.')

    def validate_outstanding_debt(self, max_outstanding_debt):
        member = frappe.get_doc('Member', self.member)
        if member.outstanding_debt >= max_outstanding_debt:
            frappe.throw(f'Outstanding debt ({member.outstanding_debt}) exceeds the limit of {max_outstanding_debt}.')

    def calculate_rent_fee(self, rent_fee_per_day):
        days = date_diff(self.return_date or frappe.utils.nowdate(), self.issue_date)
        self.rent_fee = days * rent_fee_per_day  
    def complete_transaction(self, rent_fee_per_day):
        self.calculate_rent_fee(rent_fee_per_day)  
        self.update_member_debt()  
        self.update_book_quantity(1)  
        self.status = 'Returned'  

    def update_member_debt(self):
        member = frappe.get_doc('Member', self.member)
        if not self.rent_paid:
            member.outstanding_debt = (member.outstanding_debt or 0) + self.rent_fee
        else:
            member.outstanding_debt = (member.outstanding_debt or 0) - self.rent_fee 
        member.save()

    def update_book_quantity(self, qty_change):
        book = frappe.get_doc('Book', self.book)
        book.quantity += qty_change
        if book.quantity <= 0:
            book.status = 'Not Available'  
        else:
            book.status = 'Available'  
        book.save()
