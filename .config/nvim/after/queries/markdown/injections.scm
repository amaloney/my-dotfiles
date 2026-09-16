; extends

; Map batch/cmd fence languages to batch treesitter parser
((fenced_code_block
  (info_string (language) @_lang)
  (code_fence_content) @injection.content)
  (#any-of? @_lang "batch" "cmd" "bat" "dosbatch")
  (#set! injection.language "batch"))

; PowerShell mapping
((fenced_code_block
  (info_string (language) @_lang)
  (code_fence_content) @injection.content)
  (#any-of? @_lang "powershell" "pwsh" "ps1")
  (#set! injection.language "powershell"))
