"""
Тесты интеграции нормализации телефонов в Telegram Bot
"""

import unittest
from src.easy_pass_bot.security.validator import InputValidator


class TestPhoneIntegration(unittest.TestCase):
    """Тесты интеграции нормализации телефонов в валидаторе"""
    
    def test_validate_registration_data_with_phone_normalization(self):
        """Тест нормализации телефонов при валидации данных регистрации"""
        test_cases = [
            # (input_data, expected_phone_in_result)
            ("Иванов Иван Иванович, 8 999 123 45 67, 15", "+7 999 123 45 67"),
            ("Петров Петр Петрович, +7(999)123-45-67, 20А", "+7 999 123 45 67"),
            ("Сидоров Сидор Сидорович, 89991234567, 100", "+7 999 123 45 67"),
            ("Кузнецов Кузьма Кузьмич, 799912345678, 5", "+7 999 123 45 67"),  # 12 цифр
        ]
        
        for input_data, expected_phone in test_cases:
            with self.subTest(data=input_data):
                is_valid, error_msg, form_data = InputValidator.validate_registration_data(input_data)
                
                self.assertTrue(is_valid, f"Validation failed: {error_msg}")
                self.assertIsNotNone(form_data)
                self.assertEqual(form_data['phone_number'], expected_phone)
    
    def test_validate_phone_with_normalization(self):
        """Тест валидации телефонов с нормализацией"""
        valid_phones = [
            "+7 999 123 45 67",  # 11 цифр
            "8 999 123 45 67",   # 11 цифр
            "89991234567",       # 11 цифр
            "79991234567",       # 11 цифр
            "+7(999)123-45-67",  # 11 цифр
            "8(999)123-45-67",   # 11 цифр
            "799912345678",      # 12 цифр
        ]
        
        for phone in valid_phones:
            with self.subTest(phone=phone):
                is_valid, error_msg = InputValidator.validate_phone(phone)
                self.assertTrue(is_valid, f"Phone {phone} should be valid: {error_msg}")
    
    def test_validate_phone_invalid_numbers(self):
        """Тест валидации некорректных номеров"""
        invalid_phones = [
            "123",  # Слишком короткий
            "9991234567",  # 10 цифр - теперь недопустимо
            "999 123 45 67",  # 10 цифр - теперь недопустимо
            "1234567890",  # 10 цифр, не начинается с 9
            "999999999999",  # 12 цифр, но начинается с 9
            "123456789012",  # 12 цифр, но не начинается с 7
            "abc",  # Не цифры
            "",  # Пустой
        ]
        
        for phone in invalid_phones:
            with self.subTest(phone=phone):
                is_valid, error_msg = InputValidator.validate_phone(phone)
                self.assertFalse(is_valid, f"Phone {phone} should be invalid")
                self.assertIsNotNone(error_msg)


if __name__ == "__main__":
    unittest.main()


