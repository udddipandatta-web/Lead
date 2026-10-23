"""Mark the restaurants Finely Tossed has already emailed as contacted in Harvey.

Harvey has no exclusion list. Instead it skips any company whose domain is
already in its database (discovery and the Scout both check this), and its
Sender never sends a first email to a prospect whose status is "contacted".
So this script records each restaurant from contacted.csv as a company
(keyed by its email domain) with one prospect at status "contacted".

Run it from your Harvey checkout, with Harvey's venv active, once before
`harvey run`. It is safe to run again: existing rows are left as they are.

    python /path/to/Lead/harvey-setup/seed_contacted.py
"""

import asyncio
import csv
import sys
from pathlib import Path

try:
    from harvey.models.company import Company
    from harvey.models.prospect import Prospect
    from harvey.state import StateManager
except ImportError:
    sys.exit("Run this with Harvey's venv active (source .venv/bin/activate).")

CONTACTED_CSV = Path(__file__).resolve().parent / "contacted.csv"  # kept out of git


async def main(db_path: str | None = None) -> None:
    if not CONTACTED_CSV.exists():
        sys.exit(f"Save contacted.csv next to this script first: {CONTACTED_CSV}")
    state = StateManager(db_path)
    await state.init_db()

    added = skipped = 0
    with CONTACTED_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            email = row["email"].strip().lower()
            domain = email.split("@", 1)[1]
            first, _, last = row["chef_name"].strip().partition(" ")
            note = (f"Emailed by Uddipan from Gmail on {row['sent_at']} "
                    f"(Michelin outreach batch {row['batch']}). Do not cold email again.")

            company_id = await state.add_company(Company(
                name=row["restaurant"],
                domain=domain,
                website=f"https://{domain}",
                industry="Fine dining restaurant",
                location=row["city"],
                source="finely_tossed_manual_outreach",
                notes=note,
            ))
            existing = await state.get_contacts_for_company(company_id)
            if any(p.email == email for p in existing):
                skipped += 1
                continue
            await state.add_prospect(Prospect(
                company_id=company_id,
                first_name=first,
                last_name=last,
                email=email,
                title="Chef / Owner",
                source="finely_tossed_manual_outreach",
                status="contacted",
                company=row["restaurant"],
                industry="Fine dining restaurant",
                personalization_notes=note,
            ))
            added += 1

    print(f"Marked {added} restaurants as already contacted ({skipped} were already there).")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None))
