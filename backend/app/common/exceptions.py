"""统一异常处理.

错误码格式：{模块2位}{级别1位}{序号2位}，详见 docs/03-api/ERROR_CODES.md
- 模块：00=通用, 01=资产, 02=配置, 03=凭证, 04=采集, 05=状态, 06=事件, 07=告警,
        08=策略, 09=自动化, 10=日志, 11=AIops, 12=知识, 13=工单, 14=治理
- 级别：1=参数错误, 2=业务错误, 3=权限错误, 4=系统错误
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.common.response import error


class ErrorCode:
    """5位模块化错误码，来源：docs/03-api/ERROR_CODES.md

    格式：{模块2位}{级别1位}{序号2位}
    用字符串存储避免 Python 前导零语法错误，返回时转为 int。
    """
    # 通用 (00xxx)
    UNKNOWN = "00001"
    VALIDATION = "00010"
    BAD_FORMAT = "00011"
    UNAUTHORIZED = "00100"
    TOKEN_EXPIRED = "00101"
    TOKEN_INVALID = "00102"
    FORBIDDEN = "00103"
    ACCOUNT_LOCKED = "00104"
    NOT_FOUND = "00200"
    DUPLICATE = "00201"
    CONFLICT = "00202"
    DB_ERROR = "00300"
    CACHE_ERROR = "00301"
    EXTERNAL_ERROR = "00400"
    AI_UNAVAILABLE = "00401"
    # 资产 (01xxx)
    ASSET_NAME_EMPTY = "01100"
    ASSET_TYPE_INVALID = "01101"
    ASSET_IP_INVALID = "01102"
    ASSET_NOT_FOUND = "01200"
    ASSET_DUPLICATE = "01201"
    ASSET_HAS_RELATIONS = "01202"
    # 配置 (02xxx)
    CONFIG_KEY_EMPTY = "02100"
    CONFIG_NOT_FOUND = "02200"
    CONFIG_VERSION_NOT_FOUND = "02201"
    CONFIG_PUBLISHED = "02202"
    # 凭证 (03xxx)
    CRED_NOT_FOUND = "03200"
    CRED_TEST_FAILED = "03202"
    # 采集 (04xxx)
    COLLECTOR_NOT_FOUND = "04200"
    COLLECTOR_OFFLINE = "04201"
    # 告警 (07xxx)
    ALERT_RULE_INVALID = "07100"
    ALERT_NOT_FOUND = "07200"
    # 策略 (08xxx)
    POLICY_NOT_FOUND = "08200"
    POLICY_CONFLICT = "08202"
    # 自动化 (09xxx)
    SCRIPT_EMPTY = "09100"
    EXEC_NOT_FOUND = "09200"
    EXEC_BLOCKED = "09202"
    # AIops (11xxx)
    AI_ANALYSIS_NOT_FOUND = "11200"
    AI_UNAVAILABLE_ANALYSIS = "11201"
    # 知识 (12xxx)
    KNOWLEDGE_NOT_FOUND = "12200"
    # 工单 (13xxx)
    TICKET_NOT_FOUND = "13200"
    TICKET_INVALID_STATE = "13201"
    # 治理 (14xxx)
    USER_NOT_FOUND = "14200"
    USER_DUPLICATE = "14201"


class AppError(Exception):
    """业务异常基类."""

    def __init__(self, code: str | int, message: str, status_code: int = 400):
        self.code = int(code) if isinstance(code, str) else code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    """资源不存在."""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=ErrorCode.NOT_FOUND, message=message, status_code=404)


class DuplicateError(AppError):
    """资源重复."""

    def __init__(self, message: str = "资源已存在"):
        super().__init__(code=ErrorCode.DUPLICATE, message=message, status_code=409)


class PermissionDeniedError(AppError):
    """权限不足."""

    def __init__(self, message: str = "权限不足"):
        super().__init__(code=ErrorCode.FORBIDDEN, message=message, status_code=403)


class UnauthorizedError(AppError):
    """未认证."""

    def __init__(self, message: str = "未认证"):
        super().__init__(code=ErrorCode.UNAUTHORIZED, message=message, status_code=401)


class ValidationError(AppError):
    """参数错误."""

    def __init__(self, message: str = "参数验证失败"):
        super().__init__(code=ErrorCode.VALIDATION, message=message, status_code=422)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """业务异常处理器."""
    trace_id = getattr(request.state, "trace_id", "")
    return JSONResponse(
        status_code=exc.status_code,
        content=error(exc.code, exc.message, trace_id).model_dump(),
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器."""
    trace_id = getattr(request.state, "trace_id", "")
    return JSONResponse(
        status_code=500,
        content=error(int(ErrorCode.UNKNOWN), "服务器内部错误", trace_id).model_dump(),
    )
