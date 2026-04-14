"""
apps/users/validators.py

FIX: BankPasswordComplexityValidator.validate() tidak pernah mengecek
panjang password meskipun get_help_text() menyebut "16+ chars".
Password 4 karakter seperti "Aa1!" lolos validator ini.
"""
import re
from django.core.exceptions import ValidationError


class BankPasswordComplexityValidator:
    """
    Validator password untuk banking app.
    Requirements: minimal 16 karakter, uppercase, lowercase, digit, special char.
    """
    MIN_LENGTH = 16

    def validate(self, password, user=None):
        errors = []

        # FIX: Validasi panjang yang sebelumnya tidak ada
        if len(password) < self.MIN_LENGTH:
            errors.append(
                ValidationError(
                    f"Password harus minimal {self.MIN_LENGTH} karakter. "
                    f"Saat ini {len(password)} karakter."
                )
            )

        if not re.search(r'[A-Z]', password):
            errors.append(
                ValidationError("Password harus mengandung minimal 1 huruf kapital.")
            )
        if not re.search(r'[a-z]', password):
            errors.append(
                ValidationError("Password harus mengandung minimal 1 huruf kecil.")
            )
        if not re.search(r'\d', password):
            errors.append(
                ValidationError("Password harus mengandung minimal 1 angka.")
            )
        if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>/?\\|`~]', password):
            errors.append(
                ValidationError("Password harus mengandung minimal 1 karakter spesial.")
            )

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return (
            f"Password harus minimal {self.MIN_LENGTH} karakter dan mengandung "
            "huruf kapital, huruf kecil, angka, dan karakter spesial "
            "(!@#$%^&* dll)."
        )
