# Coursework provenance and subsequent work

Public author: **Neer-1**. The author confirms individual ownership of the original Database Principles assignment report/SQL, permission to publish their coursework-derived implementation, and no original collaborators. License remains undecided.

## Evidence and source boundary

The original course folder contained no standalone SQL project. `schema.sql` was previously transcribed/reconstructed from the submitted report's Question 2 DDL (report pages 4-5). This release preserves that staged schema byte-for-byte. It is not the original submitted SQL export, and the new repository is not the exact original submission. The original question paper, report, screenshots, grades and private records are excluded.

The report establishes the six entities, their columns, six primary keys, two unique email columns and four foreign keys. The brief requests order-management modelling, documented constraints/relationships, test data and SQL query categories. It does not establish non-negative values, mandatory relationships or detailed business workflows beyond the submitted design. The report recommends hashed password storage in a comment; that is not an authentication implementation.

## New portfolio additions prepared with Codex assistance

- `seed.sql`: entirely new synthetic data with explicit IDs and consistent non-null relationships, plus intentional nullable/unused records for outer joins. No original personal/sample contact records or password strings were reused.
- `queries.sql`: new/adapted examples covering the required operator, sort, aggregate, join, update and delete categories, plus per-order totals. Filters, output columns, deterministic ordering and fixture expectations are adapted; these are not verbatim submitted answers.
- `validate.py`: new isolated Windows MySQL regression runner, based on the already-reviewed staging test approach. It verifies behavior, limitations, fresh replay and cleanup using only Python standard-library orchestration and installed MySQL tools.
- README: new setup instructions, schema dictionary, ER overview and release limitations. The diagram is reconstructed from enforced foreign keys, not copied from a university diagram.

No corrective schema constraints were added. Improvements are in reproducibility, synthetic examples, regression checks and accurate documentation; they must not be mistaken for newly enforced business rules.

## Corrections to earlier reconstruction notes

The report's original sample Orders data refers to an absent customer ID when run against its fresh four-customer seed. Sample OrderDetails rows omit OrderID, but the DDL permits NULL: this is a missing association, not a NOT NULL violation.

An earlier text-only review could not extract query text from the report. Direct inspection of query screenshots on pages 10-14 confirmed SELECT, aggregate, join, update and delete statements. The report's RIGHT JOIN caption says all suppliers, but the displayed `Suppliers RIGHT JOIN Products` preserves products. The new example uses `Products RIGHT JOIN Suppliers` to match the all-suppliers objective and tests an unused supplier. This correction changes the new query example, not the schema.

Screenshot row identifiers and some values differ from the report's insert listing; screenshot results are historical evidence, not reproducible release test results. New expected outputs are calculated from the new synthetic fixture and verified independently of those screenshots.

## Third-party review and publication boundary

Inspection of staged SQL, report DDL/query screenshots and the proposed files found no copied-library headers, third-party attribution notices, imported SQL packages or external assets. This is not proof that no conventional example was consulted during the original coursework. Any later identified attribution obligation must be resolved before publication; no license grant is presumed. MySQL/Python binaries and their documentation are not distributed.

This seven-file package excludes university documents and private test output. Final repository publication requires the author's separate approval.
