from typing import List, Optional, TypeVar, Union
from fastapi.responses import JSONResponse

T = TypeVar("T")


def json(
    data: Optional[Union[T, List[T]]] = None,
    message: str = "Thành công",
    status: int = 200,
    locale: str = "en",
) -> JSONResponse:
    """
    Tạo response thành công theo định dạng chuẩn

    Args:
        data: Dữ liệu trả về
        message: Thông điệp thành công
        status: Mã trạng thái HTTP
        locale: Ngôn ngữ

    Returns:
        JSONResponse với status code chính xác
    """
    response_data = {
        "data": data,
        "message": message,
        "status": status,
        "locale": locale,
        "errors": None,
    }
    return JSONResponse(content=response_data, status_code=status)


def fail(
    message: str = "Có lỗi xảy ra",
    status: int = 500,
    errors: Optional[List[str]] = None,
    locale: str = "vi",
) -> JSONResponse:
    """
    Tạo response lỗi theo định dạng chuẩn

    Args:
        message: Thông điệp lỗi
        status: Mã trạng thái HTTP lỗi
        errors: Chi tiết lỗi
        locale: Ngôn ngữ

    Returns:
        JSONResponse với status code lỗi chính xác
    """
    response_data = {
        "data": None,
        "message": message,
        "status": status,
        "locale": locale,
        "errors": errors or message,
    }
    return JSONResponse(content=response_data, status_code=status)


def validataion(
    validation_errors: List[str],
    message: str = "Dữ liệu đầu vào không hợp lệ",
    locale: str = "vi",
) -> JSONResponse:
    """
    Tạo response lỗi validation

    Args:
        validation_errors: Danh sách lỗi validation
        message: Thông điệp lỗi chính
        locale: Ngôn ngữ

    Returns:
        JSONResponse với status code 400
    """
    response_data = {
        "data": None,
        "message": message,
        "status": 400,
        "locale": locale,
        "errors": "; ".join(validation_errors),
    }
    return JSONResponse(content=response_data, status_code=400)


def not_found(resource: str = "Tài nguyên", locale: str = "vi") -> JSONResponse:
    """
    Tạo response không tìm thấy

    Args:
        resource: Tên tài nguyên không tìm thấy
        locale: Ngôn ngữ

    Returns:
        JSONResponse với status code 404
    """
    response_data = {
        "data": None,
        "message": f"{resource} không được tìm thấy",
        "status": 404,
        "locale": locale,
        "errors": f"{resource} không tồn tại trong hệ thống",
    }
    return JSONResponse(content=response_data, status_code=404)

def unauthorized(message: str = "Không có quyền truy cập",
    locale: str = "vi"
) -> JSONResponse:
    """
    Tạo response không có quyền truy cập

    Args:
        message: Thông điệp lỗi
        locale: Ngôn ngữ

    Returns:
        JSONResponse với status code 401
    """
    response_data = {
        "data": None,
        "message": message,
        "status": 401,
        "locale": locale,
        "errors": message
    }
    return JSONResponse(content=response_data, status_code=401)
