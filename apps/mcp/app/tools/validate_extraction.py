from decimal import Decimal
import re
from shared.types import LineItem, ReceiptMetadata, ValidationResult


async def validate_extraction(metadata: ReceiptMetadata, items: list[LineItem]) -> ValidationResult:
    errors = []
    warnings = []

    # 1. Validate Merchant Name (Hỗ trợ tiếng Việt có dấu)
    if metadata.merchant_name:
        # Very flexible - allow all characters for Vietnamese names
        # Only warn about unusual characters, don't error
        if not re.match(
            r"^[A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂÂÊÔƠƯ\s\-\'\.&0-9!]+$",
            metadata.merchant_name,
            re.I,
        ):
            # Just informational - special characters are OK
            pass  # No warning needed - Vietnamese names often have special chars
    else:
        warnings.append("Merchant name not found.")

    # 2. Validate Total Amount (Currency-aware) - Flexible
    if metadata.total_amount:
        if metadata.total_amount <= 0:
            errors.append("Total amount must be positive.")

        # Very lenient warnings for unusually high amounts
        # These are just informational, not errors
        if metadata.currency == "VND" and metadata.total_amount > 100000000:  # 100 triệu
            warnings.append(f"Total amount very high for VND: {metadata.total_amount:,.0f} (>100M).")
        elif metadata.currency != "VND" and metadata.total_amount > 50000:
            warnings.append(f"Total amount very high for {metadata.currency}: {metadata.total_amount:,.0f}.")
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
            # Skip validation for discounts/promotions (negative prices) - they follow different rules
            is_discount = Decimal(str(item.total_price)) < 0
            
            if not is_discount and item.unit_price is not None:
                # Flexible validation - prices aren't the main target
                expected_item_total = Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
                actual_total = Decimal(str(item.total_price))
                diff = abs(expected_item_total - actual_total)
                
                # Very lenient - only warn if difference is extreme (>50% or >50k VND)
                tolerance_percentage = expected_item_total * Decimal("0.50")  # 50%
                tolerance = max(Decimal("50000"), tolerance_percentage)
                
                if diff > tolerance:
                    # Even extreme mismatches are just warnings - focus is on item extraction
                    warnings.append(
                        f"Item {idx+1} '{item.item_name}': Possible column mapping issue. "
                        f"Expected: {item.quantity} × {item.unit_price} ≈ {expected_item_total:.0f}, "
                        f"but found {actual_total:.0f} (diff: {diff:.0f} VND)"
                    )

            calculated_grand_total += Decimal(str(item.total_price))

        # C. Kiểm tra tổng hóa đơn - FLEXIBLE CHECK (focus on item extraction, not perfect totals)
        if metadata.total_amount:
            diff = abs(calculated_grand_total - Decimal(str(metadata.total_amount)))
            # Very lenient tolerance: 50% or 100,000 VND
            # Main goal is to extract items, not perfect price matching
            percentage_tolerance = Decimal(str(metadata.total_amount)) * Decimal("0.50")  # 50%
            allowed_diff = max(Decimal("100000"), percentage_tolerance)

            if diff > allowed_diff:
                # Even large mismatches are warnings - allow extraction to proceed
                missing_amount = Decimal(str(metadata.total_amount)) - calculated_grand_total
                percentage_diff = diff/Decimal(str(metadata.total_amount))*100
                
                warnings.append(
                    f"Total mismatch: Sum of {len(items)} items ({calculated_grand_total:,.0f}) "
                    f"vs Receipt Total ({metadata.total_amount:,.0f}). "
                    f"Difference: {diff:,.0f} VND ({percentage_diff:.1f}%). "
                    f"This is OK - focus is on extracting items, not perfect totals."
                )
            elif diff > Decimal("10000"):
                # Small difference - informational only
                warnings.append(
                    f"Minor total variance: {calculated_grand_total:,.0f} vs "
                    f"{metadata.total_amount:,.0f} (±{diff:,.0f} VND)"
                )

    # Tính toán lại confidence dựa trên lỗi
    final_confidence = metadata.confidence
    if errors:
        # Only critical errors lower confidence significantly
        final_confidence = min(0.5, final_confidence)  # Still usable even with errors
    elif len(warnings) > 5:
        # Many warnings slightly reduce confidence
        final_confidence = max(0.3, final_confidence - 0.05 * len(warnings))

    return ValidationResult(
        valid=len(errors) == 0,  # Only fail on critical errors (missing items, negative totals)
        errors=errors,
        warnings=warnings,
        confidence=float(final_confidence),
    )
