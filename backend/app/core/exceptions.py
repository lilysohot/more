from fastapi import HTTPException, status


class CredentialsException(HTTPException):
    def __init__(self, detail: str = "无法验证凭据"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class UserNotFoundException(HTTPException):
    def __init__(self, detail: str = "用户不存在"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class UserAlreadyExistsException(HTTPException):
    def __init__(self, detail: str = "用户已存在"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class InvalidPasswordException(HTTPException):
    def __init__(self, detail: str = "密码错误"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class APIConfigLimitException(HTTPException):
    def __init__(self, detail: str = "已达到 API 配置数量上限"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class APIConfigNotFoundException(HTTPException):
    def __init__(self, detail: str = "API 配置不存在"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
