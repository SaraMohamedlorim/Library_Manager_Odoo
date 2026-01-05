from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class QuickBorrowWizard(models.TransientModel):
    _name = 'library.quick.borrow.wizard'
    _description = 'Quick Borrow Wizard'

    member_id = fields.Many2one('library.member', string='Member', required=True)
    book_id = fields.Many2one('library.book', string='Book', required=True,
                              domain="[('status', '=', 'available')]")
    due_date = fields.Date(string='Due Date', required=True, default=fields.Date.context_today)

    @api.model
    def default_get(self, fields_list):
        """Handle default values from context"""
        res = super().default_get(fields_list)
        context = self.env.context

        # Set default member from context
        if 'default_member_id' in context:
            res['member_id'] = context['default_member_id']

        # Set default book from context
        if 'default_book_id' in context:
            res['book_id'] = context['default_book_id']

        return res

    @api.onchange('member_id', 'book_id')
    def _onchange_member_book(self):
        """Check if member can borrow and book is available"""
        if self.member_id and self.book_id:
            # Check if book is still available
            if self.book_id.status != 'available':
                return {
                    'warning': {
                        'title': _('Book Not Available'),
                        'message': _('This book is currently not available for borrowing.')
                    }
                }

            # Check if member already has this book
            existing_borrowing = self.env['library.borrowing'].search([
                ('member_id', '=', self.member_id.id),
                ('book_id', '=', self.book_id.id),
                ('returned', '=', False)
            ])
            if existing_borrowing:
                return {
                    'warning': {
                        'title': _('Already Borrowed'),
                        'message': _('This member has already borrowed this book and not returned it yet.')
                    }
                }

    def action_confirm_borrow(self):
        """Create borrowing record"""
        self.ensure_one()

        # Validate book availability
        if self.book_id.status != 'available':
            raise ValidationError(_('This book is not available for borrowing.'))

        # Create borrowing record
        borrowing = self.env['library.borrowing'].create({
            'member_id': self.member_id.id,
            'book_id': self.book_id.id,
            'borrow_date': fields.Date.context_today(self),
            'due_date': self.due_date,
        })

        # Show success message
        message = _('Book "%s" has been borrowed by "%s" successfully!') % (
            self.book_id.name, self.member_id.name
        )

        # Return based on context
        if self.env.context.get('from_book'):
            return {
                'type': 'ir.actions.act_window',
                'name': _('Book'),
                'res_model': 'library.book',
                'view_mode': 'form',
                'res_id': self.book_id.id,
                'target': 'current',
            }
        elif self.env.context.get('from_member'):
            return {
                'type': 'ir.actions.act_window',
                'name': _('Member'),
                'res_model': 'library.member',
                'view_mode': 'form',
                'res_id': self.member_id.id,
                'target': 'current',
            }
        else:
            # Return to borrowings list
            return {
                'type': 'ir.actions.act_window',
                'name': _('Borrowings'),
                'res_model': 'library.borrowing',
                'view_mode': 'tree,form',
                'target': 'current',
                'context': {'search_default_active': 1},
            }