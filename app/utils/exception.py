class CustomValidationError(Exception):
    def __init__(self, detail: str, status_code: int):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class TokenExpiredSignatureError(Exception):
    def __init__(self, detail: str, status_code: int):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code
