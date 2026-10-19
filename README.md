# Order Management System

Flask and MySQL order-management group project with admin and customer workflows.

**Portfolio:** [Carl Renz Colico](https://github.com/renzkie8) · **Year:** Year 2

## Methodology

Use server-rendered templates, SQLAlchemy models and role-based login to manage products, customers and orders.

## Results and limitations

Source, templates, product assets and schema structure are preserved. Account records, password hashes, private environment settings and bundled virtual environments are excluded. Credentials are read from environment variables in the publication copy.

This upload documents the supplied submission. Experiments, model training, graphical interfaces and external services were not fully rerun during portfolio preparation. See VALIDATION.md for checks actually performed.

## Getting started

Install the original requirements in a compatible virtual environment; the app also imports Flask-Migrate, which is missing from the original requirements. Configure MySQL, copy source_code/.env.example to source_code/.env and fill in local values. Run the app from source_code. `init_db.py` drops existing tables: use it only against a new disposable coursework database. Original package-version and duplicate SQLAlchemy-initialization issues may need repair before execution.

## Contents

See [FILES.md](FILES.md) for the file inventory and [DATA.md](DATA.md) for inputs and exclusions. Original documentation, when supplied, follows below. Nonidentical drafts remain identifiable by their original names or a `variant` suffix.

## Provenance and credits

Group submission by Bacsain, Colico and Tercero, as identified by the source archive.

Source submissions: `G5_BACSAIN_COLICO_TERCERO_FP_IM_CCCS_105.zip`

No new blanket license is applied to third-party assets, datasets, course templates or collaborative work. Existing notices remain applicable.

## Topics

python, flask, mysql, sqlalchemy, order-management, group-project
