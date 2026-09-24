# Washer Tray Quantity Entry: changes in round 2

This file lists only what changed since the last version. Controls and properties not listed here stay as they were.

## Summary

| # | Change | Where |
|---|--------|-------|
| 1 | Fixed the `Invalid argument type (Boolean). Expecting a Table value` error | Submit `OnSelect` |
| 2 | `Date` now holds the date and time as ISO 8601 UTC text. Nothing is written to `Time` | `txt_tray_qty.OnChange`, Submit `OnSelect` |
| 3 | Removed `SubmissionTime` from the collection | Every `ClearCollect` / `Collect` |
| 4 | `COST_CENTER` is read with `First()` and written to the entry list | Submit `OnSelect` |
| 5 | New `lbl_part_description` label | `lbl_part_description.Text` |

### Why the error happened
In `IfError(value, fallback)`, the value and the fallback must return the same type. The value ended with `ClearCollect(...)`, which returns a **table**. The fallback was `Notify(...)`, which returns a **Boolean**. Now the value ends with `true` and the fallback ends with `false`, so both return a Boolean. The result goes to an `If` that runs the success steps.

### Date format
`Text(Now(), DateTimeFormat.UTC)` writes text like `2026-09-24T14:05:32.123Z`. This is ISO 8601 in UTC:
- **Power BI** reads the text column as Date/Time with no custom parsing. Convert it to local time in the model if you need to.
- **Power Automate** can use it directly in `formatDateTime()`, `convertFromUtc()` and date comparisons.

> **Assumption:** the destination column for the cost center is named `Cost_Center` in `'Washer Tray Quantity Entry'`. Change the name in the Submit code if yours is different. If `COST_CENTER` is a number and `Cost_Center` is text, wrap the value in `Text(...)`.
>
> **Assumption:** the machine number in `'Washer Parts List M4348'` is stored in `Title`, as in the existing machine ComboBox. If you filter on a separate `MACHINE_NUMBER` column, use it instead of `Title` below.

---

## 1. cmbx_machine_selection.OnChange
`SubmissionTime` is removed.
```
ClearCollect(
    col_washer_part_qty,
    {
        RowID: GUID(),
        MachineNumber: Text(Self.Selected.Value),
        ListPartNumber: "",
        ManualPartNumber: "",
        TrayQuantity: 0,
        NotInList: false,
        SubmissionDate: ""
    }
)
```

---

## 2. lbl_part_description (new)

**Text**
```
If(
    ThisItem.NotInList || IsBlank(ThisItem.ListPartNumber),
    "",
    LookUp(
        'Washer Parts List M4348',
        Title = ThisItem.MachineNumber && PART_NUMBER = ThisItem.ListPartNumber,
        PART_DESCRIPTION
    )
)
```

**Visible** (optional: hides the label while typing a manual part number)
```
!ThisItem.NotInList
```

---

## 3. txt_tray_qty.OnChange
The value is now an ISO 8601 UTC date and time, and the time variable is removed.
```
With(
    {
        enteredQuantity: Value(Self.Text),
        activePartNumber: If(
            ThisItem.NotInList,
            ThisItem.ManualPartNumber,
            ThisItem.ListPartNumber
        ),
        enteredSubmissionDate: Text(Now(), DateTimeFormat.UTC)
    },
    If(
        IsBlank(Self.Text) || !IsNumeric(Self.Text) || enteredQuantity <= 0,
        Notify("Enter a tray quantity greater than zero.", NotificationType.Error);
        Reset(Self),

        IsBlank(Trim(activePartNumber)),
        Notify(
            If(
                ThisItem.NotInList,
                "Enter the part number before entering the tray quantity.",
                "Select a part number before entering the tray quantity."
            ),
            NotificationType.Error
        );
        Reset(Self),

        UpdateIf(
            col_washer_part_qty,
            RowID = ThisItem.RowID,
            {
                TrayQuantity: enteredQuantity,
                SubmissionDate: enteredSubmissionDate
            }
        );
        If(
            ThisItem.RowID = Last(col_washer_part_qty).RowID,
            Collect(
                col_washer_part_qty,
                {
                    RowID: GUID(),
                    MachineNumber: Text(cmbx_machine_selection.Selected.Value),
                    ListPartNumber: "",
                    ManualPartNumber: "",
                    TrayQuantity: 0,
                    NotInList: false,
                    SubmissionDate: ""
                }
            )
        )
    )
)
```

---

## 4. Submit button.OnSelect
This fixes the IfError type error, writes the date and time to `Date`, stops writing `Time`, and adds `Cost_Center`.
```
With(
    {
        rowsToSubmit: Filter(
            col_washer_part_qty,
            !IsBlank(Trim(If(NotInList, ManualPartNumber, ListPartNumber))) &&
            TrayQuantity > 0
        ),
        machineCostCenter: First(
            Filter(
                'Washer Parts List M4348',
                Title = cmbx_machine_selection.Selected.Value
            )
        ).COST_CENTER
    },
    If(
        CountRows(rowsToSubmit) = 0,
        Notify("Enter at least one part number and tray quantity.", NotificationType.Error),

        IfError(
            ForAll(
                rowsToSubmit As qtyRow,
                Patch(
                    'Washer Tray Quantity Entry',
                    Defaults('Washer Tray Quantity Entry'),
                    {
                        Machine_Number: qtyRow.MachineNumber,
                        Part_Number: If(
                            qtyRow.NotInList,
                            Upper(Trim(qtyRow.ManualPartNumber)),
                            qtyRow.ListPartNumber
                        ),
                        Tray_Quantity: qtyRow.TrayQuantity,
                        Cost_Center: machineCostCenter,
                        Date: qtyRow.SubmissionDate
                    }
                )
            );
            true,
            Notify("One or more records could not be submitted.", NotificationType.Error);
            false
        ),
        Notify("Tray quantities submitted successfully.", NotificationType.Success);
        ClearCollect(
            col_washer_part_qty,
            {
                RowID: GUID(),
                MachineNumber: Text(cmbx_machine_selection.Selected.Value),
                ListPartNumber: "",
                ManualPartNumber: "",
                TrayQuantity: 0,
                NotInList: false,
                SubmissionDate: ""
            }
        )
    )
)
```
Here `If(cond1, r1, cond2, r2)` works like this: if there are no rows, it shows the "enter at least one" message. Otherwise, if `IfError` returned `true`, meaning every Patch succeeded, it shows the success message and resets the rows. If a Patch failed, the error message was already shown and the rows stay, so the user can try again.

---

## 5. btn_reset.OnSelect
`SubmissionTime` is removed.
```
ClearCollect(
    col_washer_part_qty,
    {
        RowID: GUID(),
        MachineNumber: Text(cmbx_machine_selection.Selected.Value),
        ListPartNumber: "",
        ManualPartNumber: "",
        TrayQuantity: 0,
        NotInList: false,
        SubmissionDate: ""
    }
)
```

---

## Checklist
1. Paste all five blocks. All four `ClearCollect` / `Collect` records must match, otherwise Power Apps reports a schema mismatch on `col_washer_part_qty`.
2. Check that `Cost_Center` exists in `'Washer Tray Quantity Entry'` and that its type matches `COST_CENTER`.
3. If Power Apps still shows the removed `Time` column, refresh the `'Washer Tray Quantity Entry'` data source (Data pane → ⋯ → Refresh).
