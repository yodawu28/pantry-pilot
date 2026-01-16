from decimal import Decimal
import re
from shared.types import LineItem, ReceiptMetadata, ValidationResult


async def validate_extraction(metadata: ReceiptMetadata, items: list[LineItem]) -> ValidationResult:
    errors = []
    warnings = []

    # 1. Validate Merchant Name (Hỗ trợ tiếng Việt có dấu)
    if metadata.merchant_name:
        # Regex này cho phép tiếng Việt và các ký tự phổ biến
        if not re.match(
            r"^[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂÂÊÔƠƯ\s\-\'\.&0-9]+$",
            metadata.merchant_name,
            re.I,
        ):
            warnings.append(
                f"Merchant name '{metadata.merchant_name}' contains special characters."
            )
    else:
        warnings.append("Merchant name not found.")

    # 2. Validate Total Amount (Currency-aware)
    if metadata.total_amount:
        if metadata.total_amount <= 0:
            errors.append("Total amount must be positive.")

        # Ngưỡng cảnh báo theo đơn vị tiền tệ
        if metadata.currency == "VND" and metadata.total_amount > 50000000:  # 50 triệu
            warnings.append("Total amount unusually high for VND (>50M).")
        elif metadata.currency != "VND" and metadata.total_amount > 10000:
            warnings.append(
                f"Total amount unusually high for {metadata.currency} (>{metadata.total_amount})."
            )
    else:
        errors.append("Total amount missing.")

    # 3. Validate Line Items (QUAN TRỌNG NHẤT)
    if not items:
        errors.append("No line items extracted. Please check the 'SL' and 'Thành tiền' columns.")
    else:
        calculated_grand_total = Decimal("0")

        for idx, item in enumerate(items):
            # A. Cho phép số lượng < 1 (Dành cho hàng cân ký như 0.4kg dưa leo)
            if item.quantity <= 0:
                errors.append(f"Item {idx+1} ({item.item_name}): Quantity must be > 0.")

            # B. Kiểm tra logic nhân: Quantity * Unit Price = Total Price
            # Cho phép sai lệch nhỏ (do làm tròn trên hóa đơn)
            expected_item_total = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
            if abs(expected_item_total - Decimal(str(item.total_price))) > Decimal(
                "500"
            ):  # Ngưỡng 500đ
                warnings.append(
                    f"Item {idx+1}: Math mismatch. {item.quantity} * {item.unit_price} = {expected_item_total}, but found {item.total_price}."
                )

            calculated_grand_total += Decimal(str(item.total_price))

        # C. Kiểm tra tổng hóa đơn
        if metadata.total_amount:
            diff = abs(calculated_grand_total - Decimal(str(metadata.total_amount)))
            # Với hóa đơn Việt Nam, thường làm tròn đến hàng đơn vị hoặc chục
            allowed_diff = Decimal("1000") if metadata.currency == "VND" else Decimal("0.05")

            if diff > allowed_diff:
                errors.append(
                    f"Sum of items ({calculated_grand_total}) != Total Amount ({metadata.total_amount}). "
                    f"Difference: {diff}. Please re-scan for missing items or discount lines."
                )

    # Tính toán lại confidence dựa trên lỗi
    final_confidence = metadata.confidence
    if errors:
        final_confidence = min(0.3, final_confidence)  # Giảm mạnh nếu có lỗi logic
    elif warnings:
        final_confidence = max(0.1, final_confidence - 0.1 * len(warnings))

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        confidence=float(final_confidence),
    )
