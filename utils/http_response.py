from ctypes import Union
from typing import Any, Dict, List, Optional, TypeVar

T = TypeVar("T")


def json(
    data: Optional[Union[T, List[T]]] = None,
    message: str = "Thành công",
    status: int = 200,
    locale: str = "en",
) -> Dict[str, Any]:
    """
    Tạo response thành công theo định dạng chuẩn

    Args:
        data: Dữ liệu trả về
        message: Thông điệp thành công
        status: Mã trạng thái HTTP
        locale: Ngôn ngữ

    Returns:
        Dict với định dạng API response chuẩn
    """
    return {
        "data": data,
        "message": message,
        "status": status,
        "locale": locale,
        "errors": None,
    }


def fail(
    message: str = "Có lỗi xảy ra",
    status: int = 500,
    errors: Optional[List[str]] = None,
    locale: str = "vi",
) -> Dict[str, Any]:
    """
    Tạo response lỗi theo định dạng chuẩn

    Args:
        message: Thông điệp lỗi
        status: Mã trạng thái HTTP lỗi
        errors: Chi tiết lỗi
        locale: Ngôn ngữ

    Returns:
        Dict với định dạng API response lỗi chuẩn
    """
    return {
        "data": None,
        "message": message,
        "status": status,
        "locale": locale,
        "errors": errors or message,
    }


def validataion(
    validation_errors: List[str],
    message: str = "Dữ liệu đầu vào không hợp lệ",
    locale: str = "vi",
) -> Dict[str, Any]:
    """
    Tạo response lỗi validation

    Args:
        validation_errors: Danh sách lỗi validation
        message: Thông điệp lỗi chính
        locale: Ngôn ngữ

    Returns:
        Dict với định dạng API response lỗi validation
    """
    return {
        "data": None,
        "message": message,
        "status": 400,
        "locale": locale,
        "errors": "; ".join(validation_errors),
    }


def not_found(resource: str = "Tài nguyên", locale: str = "vi") -> Dict[str, Any]:
    """
    Tạo response không tìm thấy

    Args:
        resource: Tên tài nguyên không tìm thấy
        locale: Ngôn ngữ

    Returns:
        Dict với định dạng API response 404
    """
    return {
        "data": None,
        "message": f"{resource} không được tìm thấy",
        "status": 404,
        "locale": locale,
        "errors": f"{resource} không tồn tại trong hệ thống",
    }

def unauthorized(message: str = "Không có quyền truy cập",
    locale: str = "vi"
) -> Dict[str, Any]:
    """
    Tạo response không có quyền truy cập

    Args:
        message: Thông điệp lỗi
        locale: Ngôn ngữ

    Returns:
        Dict với định dạng API response 403
    """
    return {
        "data": None,
        "message": message,
        "status": 401,
        "locale": locale,
        "errors": message
    }
