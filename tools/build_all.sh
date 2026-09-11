#!/bin/sh
# Full rebuild, in dependency order.
#
# tools/build.py REGENERATES src/00-tokens, src/02-components, src/03-utilities
# and src/04-shell from reference/raw — anything hand-placed in those trees is
# lost. The extractors write src/05-* and src/06-*, which build.py also clears,
# so they must run AFTER it. neobase.py assembles the shipped artifact and must
# run LAST, since it reads everything above.
set -e
cd "$(dirname "$0")/.."
python3 tools/build.py                    # src/ trees + the O11 outputs
python3 tools/osui_reskin.py              # dist/osui-reskin.css
python3 tools/extract_legacy_layout.py    # src/05-legacy-layout/
python3 tools/extract_legacy_widgets.py   # src/06-legacy-widgets/
python3 tools/extract_login.py            # src/07-login/ + dist/assets/login/
python3 tools/neobase.py                  # dist/neobase.css  <- the paste
