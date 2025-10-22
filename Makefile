.PHONY: s1-url s1-pdf s1-validate fmt lint

s1-url:
	poetry run python -m magazine_graphs.stage1_extract.cli \
	  --pdf-url "https://example.com/scan.pdf" \
	  --page 0 \
	  --mag-title "La Plume" \
	  --issue-label "No. 123" \
	  --date-string "1893-05-12" \
	  --page-ref "p. 3" \
	  --out data/interim/la_plume_from_url.json

s1-pdf:
	poetry run python -m magazine_graphs.stage1_extract.cli \
	  --pdf-path ./your_scan.pdf \
	  --page 0 \
	  --mag-title "La Plume" \
	  --issue-label "No. 123" \
	  --date-string "1893-05-12" \
	  --page-ref "p. 3" \
	  --out data/interim/la_plume_from_pdf.json

s1-validate:
	poetry run python -c "from magazine_graphs.validate.json_validate import validate_json; validate_json('data/interim/la_plume_from_pdf.json','schemas/stage1_page.schema.json')"

fmt:
	poetry run black src || true
	poetry run ruff check --fix src || true

lint:
	poetry run ruff check src || true
