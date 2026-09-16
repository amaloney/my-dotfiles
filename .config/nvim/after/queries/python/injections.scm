; extends

; SQL injection for database execute calls
(call
  (attribute
    attribute: (identifier) @_attr (#any-of? @_attr "execute" "executemany" "executescript"))
  (argument_list
    (string (string_content) @injection.content (#set! injection.language "sql"))))

; Variable name suffix patterns for embedded languages
; SQL: var_sql = "SELECT ..."
(assignment
  left: (identifier) @_left (#match? @_left "_(sql|SQL)$")
  right: (string (string_content) @injection.content (#set! injection.language "sql")))

; JavaScript: var_js = "const x = ..."
(assignment
  left: (identifier) @_left (#match? @_left "_(js|JS)$")
  right: (string (string_content) @injection.content (#set! injection.language "javascript")))

; CSS: var_css = ".class { ... }"
(assignment
  left: (identifier) @_left (#match? @_left "_(css|CSS)$")
  right: (string (string_content) @injection.content (#set! injection.language "css")))

; HTML: var_html = "<div>...</div>"
(assignment
  left: (identifier) @_left (#match? @_left "_(html|HTML)$")
  right: (string (string_content) @injection.content (#set! injection.language "html")))

; JSON: var_json = '{"key": "value"}'
(assignment
  left: (identifier) @_left (#match? @_left "_(json|JSON)$")
  right: (string (string_content) @injection.content (#set! injection.language "json")))

; Shell/Bash: var_sh = "echo hello"
(assignment
  left: (identifier) @_left (#match? @_left "_(sh|SH|bash|BASH)$")
  right: (string (string_content) @injection.content (#set! injection.language "bash")))
