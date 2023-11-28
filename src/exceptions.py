class InsufficientFundsError(Exception):
    def __init__(self):
        message = "User has insufficient funds for purchase."
        super().__init__(message)
