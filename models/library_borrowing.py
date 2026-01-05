from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class LibraryBorrowing(models.Model):
    _name = 'library.borrowing'
    _description = 'Book Borrowing'
    _order = 'borrow_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    member_id = fields.Many2one('library.member', string='Member', required=True, tracking=True)
    book_id = fields.Many2one('library.book', string='Book', required=True, tracking=True)
    borrow_date = fields.Date(string='Borrow Date', default=fields.Date.today, tracking=True)
    due_date = fields.Date(string='Due Date', required=True, tracking=True)
    returned = fields.Boolean(string='Returned', default=False, tracking=True)
    return_date = fields.Date(string='Return Date', tracking=True)

    # Computed fields
    is_overdue = fields.Boolean(string='Is Overdue', compute='_compute_overdue')
    days_overdue = fields.Integer(string='Days Overdue', compute='_compute_overdue')

    # price = fields.Float(string='Borrowing Price', required=True, tracking=True, help="Cost to borrow this book.")

    amount = fields.Float(string='Borrowing Amount', compute='_compute_amount', store=True)
    expense_id = fields.Many2one('expense.tracker', string='Related Expense', readonly=True)
    borrow_price = fields.Float(string="Borrow Price", default=0.0, required=True, tracking=True, help="Cost to borrow this book.")
    expense_budget_id = fields.Many2one('expense.budget', string='Related Budget', ondelete='set null')



    @api.onchange('book_id')
    def _onchange_book_id(self):
        """Automatically set amount when a book is selected."""
        if self.book_id:
            self.amount = self.book_id.borrow_price or 0.0

    @api.depends('book_id')
    def _compute_amount(self):
        for record in self:
            record.amount = record.book_id.borrow_price if record.book_id else 0.0


    @api.depends('due_date', 'returned')
    def _compute_overdue(self):
        today = fields.Date.today()
        for record in self:
            if record.returned or not record.due_date:
                record.is_overdue = False
                record.days_overdue = 0
            else:
                record.is_overdue = record.due_date < today
                if record.is_overdue:
                    delta = today - record.due_date
                    record.days_overdue = delta.days
                else:
                    record.days_overdue = 0

    @api.model
    def create(self, vals):

        if not vals.get('due_date'):
            borrow_date = vals.get('borrow_date') or fields.Date.today()
            if isinstance(borrow_date, str):
                borrow_date = fields.Date.from_string(borrow_date)
            vals['due_date'] = borrow_date + timedelta(days=14)

        # إنشاء السجل أولاً
        record = super(LibraryBorrowing, self).create(vals)

        # التحقق من وجود budget للعضو
        if not record.member_id.budget_id:
            raise ValidationError(_("Member has no budget assigned. Please create a budget first."))

        budget = record.member_id.budget_id
        book_price = record.book_id.borrow_price

        # التحقق من الرصيد الكافي
        if budget.remaining_amount < book_price:
            raise ValidationError(_("This member doesn't have enough budget to borrow this book."))

        # تحديث حالة الكتاب إلى "مستعار"
        record.book_id.write({'status': 'checked_out'})

        # إنشاء Expense جديد
        expense_vals ={
            'name': 'Borrowed Book: {}'.format(record.book_id.name),
            'amount': book_price,
            'category_id': budget.category_id.id,
            'budget_id': budget.id,
            'date': fields.Date.today(),
            'state': 'approved',  # إضافة حالة لتجنب الأخطاء
            'title': 'Book Borrowing: {}'.format(record.book_id.name)  # إضافة حقل مطلوب
        }
        expense = record.env['expense.tracker'].create(expense_vals)
        record.expense_id = expense.id

        return record
        # Set default due date (14 days from now)
    #     if not vals.get('due_date'):
    #         borrow_date = vals.get('borrow_date') or fields.Date.today()
    #         if isinstance(borrow_date, str):
    #             borrow_date = fields.Date.from_string(borrow_date)
    #         due_date = borrow_date + timedelta(days=14)
    #         vals['due_date'] = due_date

    #     # # Update book status
    #     if vals.get('book_id'):
    #         book = self.env['library.book'].browse(vals['book_id'])
    #         book.write({'status': 'checked_out'})

    #     return super().create(vals)

    #      # تحديد تاريخ الاستحقاق الافتراضي

    #      # قبل السطر 82 أضف:
    #     if not member.budget_id:
    # # إما تخلق budget تلقائياً أو ترفع خطأ واضح
    #        raise ValidationError(_("Member has no budget assigned. Please create a budget first."))
        
    #     if not vals.get('due_date'):
    #         borrow_date = vals.get('borrow_date') or fields.Date.today()
    #         if isinstance(borrow_date, str):
    #             borrow_date = fields.Date.from_string(borrow_date)
    #         vals['due_date'] = borrow_date + timedelta(days=14)



    #     record = super(LibraryBorrowing, self).create(vals)


    #      # خصم من ميزانية العضو
    #     if record.member_id and record.member_id.budget_id:
    #         budget = record.member_id.budget_id
    #         if budget.remaining_amount >= record.amount:
    #             budget.spent_amount += record.amount
    #         else:
    #             raise ValidationError(_("This member doesn't have enough budget to borrow this book."))

    #         record.expense_budget_id = budget.id


    #     # تحديث حالة الكتاب إلى "مستعار"
    #     if record.book_id:
    #         record.book_id.write({'status': 'checked_out'})

    #     # ⚙️ الربط مع Expense Tracker
    #     member = record.member_id
    #     book_price = record.book_id.price

    #     if not member.budget_id:
    #         raise ValidationError(_("This member has no budget assigned."))

    #     budget = member.budget_id

    #     # التحقق من الرصيد الكافي
    #     if budget.amount < book_price:
    #         raise ValidationError(_("Insufficient budget balance! Cannot borrow this book."))

    #     # خصم المبلغ من الميزانية
    #     budget.amount -= book_price

    #     # إنشاء Expense جديد
    #     expense = record.env['expense.tracker'].create({
    #         'name': f'Borrowed Book: {record.book_id.name}',
    #         'amount': book_price,
    #         'category_id': budget.category_id.id,
    #         'budget_id': budget.id,
    #         'date': fields.Date.today(),
    #     })
    #     record.expense_id = expense.id

    #     return record

    def action_return_book(self):
        for record in self:
            if not record.returned:
                record.write({
                    'returned': True,
                    'return_date': fields.Date.today()
                })
                # Update book status
                record.book_id.write({'status': 'available'})

    def name_get(self):
        result = []
        for record in self:
            name = "{} - {}".format(record.book_id.name, record.member_id.name)
            result.append((record.id, name))
        return result

    @api.model
    def _get_overdue_borrowings(self):
        return self.search([
            ('returned', '=', False),
            ('due_date', '<', fields.Date.today())
        ])

    @api.constrains('book_id', 'returned')
    def _check_book_availability(self):
        for rec in self:
            if not rec.returned:
                existing = self.search([
                    ('book_id', '=', rec.book_id.id),
                    ('returned', '=', False),
                    ('id', '!=', rec.id)
                ])
                if existing:
                    raise ValidationError(_('This book is already borrowed and not yet returned.'))