class InsufficientFundsError(Exception):
    def __init__(self):
        self.message = "User has insufficient funds for purchase."
        super().__init__(self.message)
