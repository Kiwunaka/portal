from __future__ import annotations


class AccountSecurityError(ValueError):
    def __init__(self, code: str, *, message: str | None = None) -> None:
        super().__init__(message or code)
        self.code = str(code or "account_security_error")
        self.message = message or self.code


class AccountRecoveryError(AccountSecurityError):
    pass


class EmailOtpError(AccountRecoveryError):
    pass
