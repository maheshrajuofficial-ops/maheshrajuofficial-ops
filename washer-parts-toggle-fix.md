# Washer Tray Quantity Entry: toggle and part number fix

## What was wrong

**1. The toggle flipped by itself.**
`togg_not_in_list.Default` is `ThisItem.NotInList`, and three controls wrote to `NotInList`:

- the toggle (`OnCheck` / `OnUncheck`)
- `cmbx_part_num.OnChange` (set it to `false`)
- `txt_part_number.OnChange` (set it to `true`)

When the toggle cleared `PartNumber`, `cmbx_part_num.DefaultSelectedItems` changed. A ComboBox fires `OnChange` when its default selection changes, even while it is hidden. That wrote `NotInList: false`, the toggle's `Default` changed, `OnUncheck` fired, and so on. This was the loop.

**2. The part number was erased.**
Every time the loop ran, `OnCheck` / `OnUncheck` wrote `PartNumber: ""`. Any row refresh (for example, the new row that `txt_tray_qty` adds) could start the loop again and wipe the value you had entered.

## How it's fixed

- **Each input stores its own value.** `ListPartNumber` holds the value from `cmbx_part_num` and `ManualPartNumber` holds the value from `txt_part_number`. Neither control resets the other. The hidden one keeps its value, which does no harm.
- **Only the toggle writes `NotInList`.** The ComboBox and the text box no longer touch it.
- **The toggle doesn't clear anything.** It uses `OnChange` with a guard, `Self.Value <> ThisItem.NotInList`. When its `Default` refreshes from the collection, the values already match, so nothing is written and the loop can't start. `OnCheck` and `OnUncheck` are cleared.
- **Every write is guarded.** Each `UpdateIf` runs only if the value actually changed, so a gallery refresh or a default re-evaluation can't overwrite data.
- **The if/else is applied when the row is used.** Validation and the Submit `Patch` both pick the part number with `If(NotInList, ManualPartNumber, ListPartNumber)`.

> Collection schema change: the `PartNumber` column is replaced by `ListPartNumber` and `ManualPartNumber`. Every `ClearCollect` / `Collect` below uses the new schema, so update all of them together.

---

## 1. cmbx_machine_selection

**SelectMultiple**
```
false
```

**Items** (unchanged)
```
Sort(
    Distinct(
        'Washer Parts List M4348',
        Title
    ),
    Value,
    SortOrder.Ascending
)
```

**OnChange**
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
        SubmissionDate: "",
        SubmissionTime: ""
    }
)
```

---

## 2. gal_washer_parts

**Items** (unchanged)
```
col_washer_part_qty
```

**Visible** (unchanged)
```
!IsBlank(cmbx_machine_selection.Selected.Value)
```

---

## 3. lbl_mach_num

**Text** (unchanged)
```
ThisItem.MachineNumber
```

---

## 4. togg_not_in_list

**Default**
```
ThisItem.NotInList
```

**OnChange** (new: the only place `NotInList` is written; it never clears the part number)
```
If(
    Self.Value <> ThisItem.NotInList,
    UpdateIf(
        col_washer_part_qty,
        RowID = ThisItem.RowID,
        { NotInList: Self.Value }
    )
)
```

**OnCheck** (clear it)
```
false
```

**OnUncheck** (clear it)
```
false
```

---

## 5. cmbx_part_num

**SelectMultiple**
```
false
```

**IsSearchable**
```
true
```

**Visible**
```
!ThisItem.NotInList
```

**Items** (unchanged)
```
Sort(
    Distinct(
        Filter(
            'Washer Parts List M4348',
            Title = ThisItem.MachineNumber
        ),
        PART_NUMBER
    ),
    Value,
    SortOrder.Ascending
)
```

**DisplayFields**
```
["Value"]
```

**SearchFields**
```
["Value"]
```

**DefaultSelectedItems** (depends only on its own field, not on the toggle)
```
If(
    IsBlank(ThisItem.ListPartNumber),
    Blank(),
    Table({ Value: ThisItem.ListPartNumber })
)
```

**OnChange** (no `NotInList` write; ignored while hidden; writes only when the value changed)
```
With(
    { selectedPart: If(IsBlank(Self.Selected.Value), "", Text(Self.Selected.Value)) },
    If(
        !ThisItem.NotInList && selectedPart <> ThisItem.ListPartNumber,
        UpdateIf(
            col_washer_part_qty,
            RowID = ThisItem.RowID,
            { ListPartNumber: selectedPart }
        )
    )
)
```

---

## 6. txt_part_number

**Visible**
```
ThisItem.NotInList
```

**Default**
```
ThisItem.ManualPartNumber
```

**Format**
```
TextFormat.Text
```

**DelayOutput**
```
true
```

**HintText**
```
"Enter part number"
```

**OnChange** (no `NotInList` write; writes only when the value changed)
```
With(
    { manualPartNumber: Upper(Trim(Self.Text)) },
    If(
        manualPartNumber <> ThisItem.ManualPartNumber,
        UpdateIf(
            col_washer_part_qty,
            RowID = ThisItem.RowID,
            { ManualPartNumber: manualPartNumber }
        )
    )
)
```

---

## 7. txt_tray_qty

**Format**
```
TextFormat.Number
```

**Default** (unchanged)
```
If(ThisItem.TrayQuantity = 0, Blank(), ThisItem.TrayQuantity)
```

**HintText**
```
"Tray quantity"
```

**OnChange** (picks the active part number with if/else and doesn't touch the part number fields)
```
With(
    {
        enteredQuantity: Value(Self.Text),
        activePartNumber: If(
            ThisItem.NotInList,
            ThisItem.ManualPartNumber,
            ThisItem.ListPartNumber
        ),
        enteredSubmissionDate: Text(Now(), "[$-en-US]mm-dd-yyyy"),
        enteredSubmissionTime: Text(Now(), "[$-en-US]hh:mm AM/PM")
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
                SubmissionDate: enteredSubmissionDate,
                SubmissionTime: enteredSubmissionTime
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
                    SubmissionDate: "",
                    SubmissionTime: ""
                }
            )
        )
    )
)
```

---

## 8. Submit button

**OnSelect** (the if/else picks which part number field to patch)
```
With(
    {
        rowsToSubmit: Filter(
            col_washer_part_qty,
            !IsBlank(Trim(If(NotInList, ManualPartNumber, ListPartNumber))) &&
            TrayQuantity > 0
        )
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
                        Date: qtyRow.SubmissionDate,
                        Time: qtyRow.SubmissionTime
                    }
                )
            );
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
                    SubmissionDate: "",
                    SubmissionTime: ""
                }
            ),
            Notify("One or more records could not be submitted.", NotificationType.Error)
        )
    )
)
```

---

## 9. btn_reset

**OnSelect**
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
        SubmissionDate: "",
        SubmissionTime: ""
    }
)
```

---

## Checklist after pasting

1. Clear `togg_not_in_list.OnCheck` and `OnUncheck` (set them to `false`) and put the logic in `OnChange`.
2. Replace every `ClearCollect` / `Collect` of `col_washer_part_qty` (machine ComboBox, tray qty, Submit, Reset) so the collection schema stays consistent.
3. Search the app for any other reference to `ThisItem.PartNumber` or `col_washer_part_qty.PartNumber` and switch it to the new fields.
4. Test: pick a part, turn the toggle on, type a manual part, turn it off, enter a qty. The toggle should stay where you put it and both part number values should be kept. The one saved is the one the toggle shows.
