from abc import ABC, abstractmethod


class FetchSubtitle(ABC):

    @abstractmethod
    def search(self, query: dict):
        """Search for subtitles based on a query."""
        pass  # noqa: PIE790




# """
# # 1. Define the Abstract Base Class
# class PaymentProcessor(ABC):
    
#     @abstractmethod
#     def process_payment(self, amount: float):
#         """Abstract method; contains no actual implementation logic."""
#         pass

#     def generate_receipt(self, amount: float):
#         """Concrete method; abstract classes can have fully functional methods."""
#         print(f"Receipt generated for ${amount}")

# # 2. Implement Subclasses (Must define 'process_payment')
# class CreditCardProcessor(PaymentProcessor):
#     def process_payment(self, amount: float):
#         print(f"Processing credit card payment of ${amount} via Stripe API.")

# class CryptoProcessor(PaymentProcessor):
#     def process_payment(self, amount: float):
#         print(f"Processing cryptocurrency payment of ${amount} via Blockchain Node.")

# # --- Execution ---
# # payment = PaymentProcessor()  # ERROR: TypeError (Can't instantiate abstract class)

# processors = [CreditCardProcessor(), CryptoProcessor()]

# for p in processors:
#     p.process_payment(150.00)   # Polymorphic execution
#     p.generate_receipt(150.00)  # Inherited functionality
# """