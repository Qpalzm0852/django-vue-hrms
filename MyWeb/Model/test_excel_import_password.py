import secrets

from django.test import TestCase

from .excel_import import EmployeeExcelImporter
from .models import Department, User


class ExcelImportPasswordTests(TestCase):
    def setUp(self):
        Department.objects.create(name="Test department")
        self.importer = EmployeeExcelImporter(None)
        self.row = {"工号": "fixture-staff", "姓名": "Synthetic Staff", "部门": "Test department", "密码": None}

    def test_new_user_with_blank_password_cannot_sign_in(self):
        self.importer._import_single_record(self.row, 2)
        self.assertFalse(User.objects.get(user_id="fixture-staff").has_usable_password())

    def test_existing_user_with_blank_password_keeps_password(self):
        password = secrets.token_urlsafe(24)
        User.objects.create_user(user_id="fixture-staff", name="Synthetic Staff", password=password)
        self.importer._import_single_record(self.row, 2)
        self.assertTrue(User.objects.get(user_id="fixture-staff").check_password(password))
