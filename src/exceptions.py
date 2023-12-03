class InsufficientFundsError(Exception):
    def __init__(self):
        self.message = "User has insufficient funds for purchase."
        super().__init__(self.message)


class ForcedFailureError(Exception):
    def __init__(self):
        self.message = "Failure in payment service!"
        super().__init__(self.message)
