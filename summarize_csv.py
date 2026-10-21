import argparse
import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path


def parse_number(value):
    """Parse a numeric CSV value, allowing currency symbols and separators."""
    cleaned = value.strip().replace("£", "").replace(",", "")
    return Decimal(cleaned)


def main():
    project_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Remove incomplete CSV rows and summarize sales by region."
    )
    parser.add_argument(
        "input_csv",
        nargs="?",
        default=project_dir / "messy_sales.csv",
        help="Input CSV file (default: messy_sales.csv in the project folder)",
    )
    parser.add_argument(
        "--output",
        default=project_dir / "cleaned.csv",
        help="Path for the cleaned CSV (default: cleaned.csv in the project folder)",
    )
    args = parser.parse_args()

    totals_by_region = defaultdict(Decimal)
    kept = 0
    missing_removed = 0
    invalid_removed = 0

    with open(args.input_csv, newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        required_columns = {"Region", "Quantity", "Unit_Price"}

        if not reader.fieldnames:
            parser.error("Input CSV is empty or has no header row.")

        missing_columns = required_columns - set(reader.fieldnames)
        if missing_columns:
            parser.error(
                f"Required columns not found: {', '.join(sorted(missing_columns))}"
            )

        with open(args.output, "w", newline="", encoding="utf-8") as destination:
            writer = csv.DictWriter(destination, fieldnames=reader.fieldnames)
            writer.writeheader()

            for line_number, row in enumerate(reader, start=2):
                if None in row:
                    raise ValueError(
                        f"Unexpected extra fields on line {line_number}."
                    )

                if any(value is None or not value.strip() for value in row.values()):
                    missing_removed += 1
                    continue

                try:
                    quantity = parse_number(row["Quantity"])
                    unit_price = parse_number(row["Unit_Price"])
                except InvalidOperation:
                    invalid_removed += 1
                    continue

                if not quantity.is_finite() or not unit_price.is_finite():
                    invalid_removed += 1
                    continue

                region = row["Region"].strip().casefold()
                totals_by_region[region] += quantity * unit_price
                writer.writerow(row)
                kept += 1

    print(
        f"Rows kept: {kept}; "
        f"removed for missing values: {missing_removed}; "
        f"removed for invalid numbers: {invalid_removed}"
    )
    print("Sales totals by region:")
    for region in sorted(totals_by_region):
        print(f"  {region.title()}: £{totals_by_region[region]:.2f}")
    print(f"Cleaned CSV written to: {args.output}")


if __name__ == "__main__":
    main()