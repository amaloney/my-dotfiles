# Variables, Arrays, POSIX vs Bash

## Variables & Expansion

| Syntax                              | Effect                     |
| ----------------------------------- | -------------------------- |
| `${var:-default}`                   | Use default if unset/empty |
| `${var:=default}`                   | Set and use default        |
| `${var?error}`                      | Exit with error if unset   |
| `local`, `export`, `readonly`       | Scope modifiers            |
| `${#str}`, `${str:0:5}`             | Length, substring          |
| `${str/old/new}`, `${str//old/new}` | Replace first/all          |
| `${str#prefix}`, `${str%suffix}`    | Remove prefix/suffix       |

## Arrays (Bash)

```bash
arr=("one" "two"); echo "${arr[0]}" "${arr[@]}" "${#arr[@]}"  # First, all, length
declare -A map; map[key]="value"   # Associative (bash 4+)
```

## POSIX vs Bash

| Feature                | POSIX | Bash |
| ---------------------- | ----- | ---- |
| `[[ ]]`, arrays, `<<<` | No    | Yes  |
| `=~` regex             | No    | Yes  |
