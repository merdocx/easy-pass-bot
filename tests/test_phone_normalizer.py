"""
Тесты для модуля нормализации телефонов
"""

import unittest
from src.easy_pass_bot.utils.phone_normalizer import (
    normalize_phone_number,
    format_russian_phone,
    validate_phone_format,
    is_russian_phone
)


class TestPhoneNormalizer(unittest.TestCase):
    """Тесты для функций нормализации телефонов"""
    
    def test_normalize_standard_format(self):
        """Тест нормализации стандартных форматов"""
        test_cases = [
            ("+7 999 123 45 67", "+7 999 123 45 67"),
            ("8 999 123 45 67", "+7 999 123 45 67"),
            ("89991234567", "+7 999 123 45 67"),
            ("79991234567", "+7 999 123 45 67"),
            ("799912345678", "+7 999 123 45 67"),  # 12 цифр
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(phone=input_phone):
                result = normalize_phone_number(input_phone)
                self.assertEqual(result, expected)
    
    def test_normalize_with_brackets_and_dashes(self):
        """Тест нормализации номеров с скобками и дефисами"""
        test_cases = [
            ("+7(999)123-45-67", "+7 999 123 45 67"),
            ("8(999)123-45-67", "+7 999 123 45 67"),
            ("+7 999-123-45-67", "+7 999 123 45 67"),
            ("8 999-123-45-67", "+7 999 123 45 67"),
            ("+7 (999) 123-45-67", "+7 999 123 45 67"),
            ("8 (999) 123-45-67", "+7 999 123 45 67"),
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(phone=input_phone):
                result = normalize_phone_number(input_phone)
                self.assertEqual(result, expected)
    
    def test_normalize_with_different_spacing(self):
        """Тест нормализации номеров с разными пробелами"""
        test_cases = [
            ("+7  999  123  45  67", "+7 999 123 45 67"),
            ("8  999  123  45  67", "+7 999 123 45 67"),
            ("+7\t999\t123\t45\t67", "+7 999 123 45 67"),
            ("8\t999\t123\t45\t67", "+7 999 123 45 67"),
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(phone=input_phone):
                result = normalize_phone_number(input_phone)
                self.assertEqual(result, expected)
    
    def test_normalize_edge_cases(self):
        """Тест граничных случаев"""
        test_cases = [
            # Уже нормализованные номера
            ("+7 999 123 45 67", "+7 999 123 45 67"),
            
            # Номера без пробелов
            ("+79991234567", "+7 999 123 45 67"),
            
            # Номера с лишними символами
            ("+7 (999) 123-45-67 ext. 123", "+7 999 123 45 67"),
            ("8 (999) 123-45-67 доб. 456", "+7 999 123 45 67"),
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(phone=input_phone):
                result = normalize_phone_number(input_phone)
                self.assertEqual(result, expected)
    
    def test_invalid_phone_numbers(self):
        """Тест некорректных номеров телефонов"""
        invalid_phones = [
            "123",  # Слишком короткий
            "9991234567",  # 10 цифр - теперь недопустимо
            "999 123 45 67",  # 10 цифр - теперь недопустимо
            "1234567890",  # 10 цифр, не начинается с 9
            "8999999999",  # 8 + 9 цифр (неправильная длина)
            "7999999999",  # 7 + 9 цифр (неправильная длина)
            "999999999999",  # 12 цифр, но начинается с 9
            "123456789012",  # 12 цифр, но не начинается с 7
            "",  # Пустая строка
            "abc",  # Не цифры
            "+380 99 999 99 99",  # Украинский номер
            "+1 555 123 4567",  # Американский номер
        ]
        
        for phone in invalid_phones:
            with self.subTest(phone=phone):
                result = normalize_phone_number(phone)
                # Некорректные номера должны возвращаться как есть
                self.assertEqual(result, phone)
    
    def test_long_phone_numbers(self):
        """Тест длинных номеров телефонов (должны нормализоваться)"""
        test_cases = [
            ("799999999999", "+7 999 999 99 99"),  # 12 цифр с 7 - валидный
            ("899999999999", "+7 999 999 99 99"),  # 12 цифр с 8 - валидный
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(phone=input_phone):
                result = normalize_phone_number(input_phone)
                self.assertEqual(result, expected)
    
    def test_empty_and_none_input(self):
        """Тест пустых и None значений"""
        test_cases = [
            ("", ""),
            (None, ""),
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(phone=input_phone):
                result = normalize_phone_number(input_phone)
                self.assertEqual(result, expected)
    
    def test_format_russian_phone(self):
        """Тест функции форматирования российского номера"""
        test_cases = [
            ("9991234567", "+7 999 123 45 67"),
            ("9123456789", "+7 912 345 67 89"),
            ("9876543210", "+7 987 654 32 10"),
        ]
        
        for input_digits, expected in test_cases:
            with self.subTest(digits=input_digits):
                result = format_russian_phone(input_digits)
                self.assertEqual(result, expected)
    
    def test_format_russian_phone_invalid_length(self):
        """Тест функции форматирования с некорректной длиной"""
        with self.assertRaises(ValueError):
            format_russian_phone("123")  # Слишком короткий
        
        with self.assertRaises(ValueError):
            format_russian_phone("123456789012")  # Слишком длинный
    
    def test_validate_phone_format(self):
        """Тест валидации формата телефона"""
        valid_phones = [
            "+7 999 123 45 67",  # 11 цифр
            "8 999 123 45 67",   # 11 цифр
            "89991234567",       # 11 цифр
            "79991234567",       # 11 цифр
            "+7(999)123-45-67",  # 11 цифр
            "8(999)123-45-67",   # 11 цифр
            "799912345678",      # 12 цифр
            "+7 999 123 45 678", # 12 цифр
        ]
        
        invalid_phones = [
            "123",               # Слишком короткий
            "9991234567",        # 10 цифр - теперь недопустимо
            "999 123 45 67",     # 10 цифр - теперь недопустимо
            "1234567890",        # 10 цифр, не начинается с 9
            "999999999999",      # 12 цифр, но начинается с 9
            "123456789012",      # 12 цифр, не начинается с 7
            "",                  # Пустой
            "abc",               # Не цифры
            "+380 99 999 99 99", # Украинский номер
            "+1 555 123 4567",   # Американский номер
        ]
        
        for phone in valid_phones:
            with self.subTest(phone=phone):
                self.assertTrue(validate_phone_format(phone))
        
        for phone in invalid_phones:
            with self.subTest(phone=phone):
                self.assertFalse(validate_phone_format(phone))
    
    def test_is_russian_phone(self):
        """Тест проверки российского номера"""
        russian_phones = [
            "+7 999 123 45 67",   # 11 цифр
            "8 999 123 45 67",    # 11 цифр
            "79991234567",        # 11 цифр
            "89991234567",        # 11 цифр
            "799912345678",       # 12 цифр
            "+7 999 123 45 678",  # 12 цифр
        ]
        
        non_russian_phones = [
            "9991234567",         # 10 цифр - теперь недопустимо
            "999 123 45 67",      # 10 цифр - теперь недопустимо
            "+380 99 999 99 99",  # Украинский
            "+1 555 123 4567",    # Американский
            "+49 30 12345678",    # Немецкий
            "123",
            "",
            "abc",
        ]
        
        for phone in russian_phones:
            with self.subTest(phone=phone):
                self.assertTrue(is_russian_phone(phone))
        
        for phone in non_russian_phones:
            with self.subTest(phone=phone):
                self.assertFalse(is_russian_phone(phone))
    
    def test_comprehensive_examples(self):
        """Комплексный тест с реальными примерами"""
        test_cases = [
            # Различные форматы российских номеров (11-12 цифр)
            ("+7 916 123 45 67", "+7 916 123 45 67"),
            ("8 916 123 45 67", "+7 916 123 45 67"),
            ("89161234567", "+7 916 123 45 67"),
            ("79161234567", "+7 916 123 45 67"),
            ("791612345678", "+7 916 123 45 67"),  # 12 цифр
            ("+7(916)123-45-67", "+7 916 123 45 67"),
            ("8(916)123-45-67", "+7 916 123 45 67"),
            ("+7 916-123-45-67", "+7 916 123 45 67"),
            ("8 916-123-45-67", "+7 916 123 45 67"),
            
            # Номера с лишними символами
            ("+7 916 123 45 67 доб. 123", "+7 916 123 45 67"),
            ("8 916 123 45 67 ext. 456", "+7 916 123 45 67"),
            
            # Некорректные номера (должны остаться как есть)
            ("916 123 45 67", "916 123 45 67"),  # 10 цифр - теперь недопустимо
            ("9161234567", "9161234567"),  # 10 цифр - теперь недопустимо
            ("+380 99 999 99 99", "+380 99 999 99 99"),
            ("123", "123"),
            ("", ""),
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(phone=input_phone):
                result = normalize_phone_number(input_phone)
                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
