# bug pattern memory

# BAD
try:
    data = json.loads(resp.read())
    info = parse_rate_limit(dict(resp.headers), prefix)  # raises ValueError on malformed values
except (OSError, json.JSONDecodeError):  # int("abc") escapes; fetcher crashes
    ...
# GOOD
except (OSError, ValueError):  # ValueError covers JSONDecodeError AND int() parse failures

Rule: when a fetch try-block contains both json parsing and any int()/float() conversion of
untrusted wire data, catch (OSError, ValueError) — ValueError subsumes JSONDecodeError, and
malformed-header ValueErrors otherwise escape "always-return" fetcher contracts.

# BAD
normalized = re.sub(r"[-_.]+", "-", name).lower()
normalized = re.sub(r"[-_.]+", "-", name).lower()  # duplicated line
# GOOD
normalized = re.sub(r"[-_.]+", "-", name).lower()  # once

Rule: check for verbatim duplicated consecutive assignments — copy/paste residue that lint
(F811 only flags redefinition of imports/names, not same-value re-assignment) does not catch.
