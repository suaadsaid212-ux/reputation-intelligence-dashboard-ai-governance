from io import BytesIO

import pandas as pd


def _safe_sheet_name(name):
    clean = str(name or "Sheet").replace("/", "-").replace("\\", "-")
    clean = clean.replace(":", "-").replace("*", "").replace("?", "")
    clean = clean.replace("[", "(").replace("]", ")")
    return clean[:31] or "Sheet"


def dataframes_to_excel_bytes(
    sheets,
    *,
    metadata=None,
):
    """
    Create an in-memory multi-sheet XLSX workbook.

    sheets:
        iterable of (sheet_name, dataframe)

    metadata:
        optional dict written to a Metadata sheet
    """
    buffer = BytesIO()

    with pd.ExcelWriter(
        buffer,
        engine="openpyxl",
    ) as writer:
        for sheet_name, frame in sheets:
            if frame is None:
                continue

            safe_name = _safe_sheet_name(
                sheet_name
            )

            current = (
                frame.copy()
                if isinstance(
                    frame,
                    pd.DataFrame,
                )
                else pd.DataFrame(
                    frame
                )
            )

            current.to_excel(
                writer,
                sheet_name=safe_name,
                index=False,
            )

            worksheet = writer.book[
                safe_name
            ]

            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = (
                worksheet.dimensions
            )

            for column_cells in worksheet.columns:
                values = [
                    str(cell.value or "")
                    for cell
                    in column_cells[:250]
                ]

                max_length = max(
                    [
                        len(value)
                        for value in values
                    ]
                    + [8]
                )

                width = min(
                    max(
                        10,
                        max_length + 2,
                    ),
                    45,
                )

                worksheet.column_dimensions[
                    column_cells[0].column_letter
                ].width = width

        if metadata:
            meta_frame = pd.DataFrame(
                [
                    {
                        "Field": key,
                        "Value": value,
                    }
                    for key, value
                    in metadata.items()
                ]
            )

            meta_frame.to_excel(
                writer,
                sheet_name="Metadata",
                index=False,
            )

            worksheet = writer.book[
                "Metadata"
            ]

            worksheet.freeze_panes = "A2"
            worksheet.column_dimensions[
                "A"
            ].width = 28
            worksheet.column_dimensions[
                "B"
            ].width = 60

    buffer.seek(0)
    return buffer.getvalue()
