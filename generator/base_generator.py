from faker import Faker
from uuid import uuid4
from datetime import datetime


class BaseGenerator:
    """
    Базовый класс для генерации случайных данных.
    Использует библиотеку Faker для создания реалистичных данных.
    """

    faker = Faker("RU")

    def get_id(self, uid):
        if uid is None:
            return str(uuid4())
        return uid

    def get_name(self, name):
        if name is None:
            return self.faker.company()
        return name

    def get_address(self, address):
        if address is None:
            return self.faker.address()
        return address

    def get_phone(self, phone):
        if phone is None:
            return self.faker.phone_number()
        return phone

    def get_logo_id(self, logo_id):
        if logo_id is None:
            return "00000000-0000-0000-0000-000000000000"
        return logo_id

    def get_integration_key(self, integration_key_length):
        if integration_key_length is not None:
            return self.faker.password(length=integration_key_length, special_chars=True, digits=True, upper_case=True, lower_case=True)
        return None

    def get_integration_source(self, integration_source):
        if integration_source is None:
            return None
        return integration_source

    def get_external_license(self, external_license):
        if external_license is None:
            return False
        return external_license

    def get_invoice_customer_ids(self, invoice_customer_ids_value=None, invoice_customer_ids_count=0, uid=None):
        lst = []
        if invoice_customer_ids_value is None:
            for i in range(invoice_customer_ids_count):
                customer_id = self.get_id(uid)
                lst.append(customer_id)
            return lst
        return invoice_customer_ids_value

    def get_contact_url(self, contact_url):
        if contact_url is None:
            return self.faker.url()
        return contact_url

    def get_firms(self, firms_value=None, firms_count=0, uid=None, name=None):
        lst = []
        if firms_value is None:
            for i in range(firms_count):
                firms = {
                    "id": self.get_id(uid),
                    "name": self.get_name(name)
                }
                lst.append(firms)
            return lst
        return firms_value

    def get_point(self, point):
        if point is None:
            return {
                "latitude": 0,
                "longitude": 0
            }
        return point

    def get_payment_method(self, payment_method):
        if payment_method is None:
            return "cash"
        return payment_method
        
    def get_paid(self, paid):
        if paid is None:
            return True
        return paid

    def get_time_from(self, time_from):
        if time_from is None:
            # Получаем текущее время в UTC
            now = datetime.utcnow()
            # Форматируем его в нужный формат, добавляя окончание
            return now.replace(hour=7, minute=0, second=0, microsecond=0).isoformat() + "Z"
        return time_from

    def get_time_till(self, time_till):
        if time_till is None:
            # Получаем текущее время в UTC
            now = datetime.utcnow()
            # Форматируем его в нужный формат, добавляя окончание
            return now.replace(hour=20, minute=59, second=0, microsecond=0).isoformat() + "Z"
        return time_till

    def get_external_number(self, number):  
        if number is None:
            return "TEST-" + str(self.faker.random_int(min=1000, max=9999))
        return number