---
name: cpp
description: C++ development following Google C++ Style Guide
invocation: auto
extensions: [".cpp", ".cc", ".cxx", ".c++", ".hpp", ".h", ".hxx"]
keywords: ["c++", "cpp", "cmake"]
---

# C++ (Google Style Guide)

Handoff: `next: done`.

**Line limit**: 80 characters. Exceptions: URLs, paths, long string literals, include statements.

## Naming Conventions

| Type | Style | Example |
|------|-------|---------|
| Files | lowercase, underscores | `my_class.cc`, `my_class.h` |
| Types (class/struct/enum/typedef) | CamelCase | `MyClass`, `UrlTable` |
| Variables | lowercase_underscores | `table_name`, `num_errors` |
| Class members | trailing underscore | `table_name_`, `count_` |
| Struct members | no underscore | `table_name` |
| Constants | k + CamelCase | `kDaysInWeek`, `kMaxSize` |
| Functions | CamelCase | `AddTableEntry()`, `DeleteUrl()` |
| Accessors/mutators | lowercase like variable | `count()`, `set_count()` |
| Namespaces | lowercase | `websearch::index` |
| Macros | ALL_CAPS | `MY_MACRO_NAME` |

## Formatting

```cpp
// 2-space indent, no tabs
// Brace on same line, space after keywords
if (condition) {
  DoSomething();
} else {
  DoOther();
}

// No space between function name and paren
void MyFunction(int arg);

// Pointer/reference attached to type (preferred)
char* str;
const std::string& name;

// Constructor initializer list
MyClass::MyClass(int value)
    : member_(value),
      other_(0) {
}
```

## Header Files

### Include Guards
```cpp
#ifndef PROJECT_PATH_FILE_H_
#define PROJECT_PATH_FILE_H_
// content
#endif  // PROJECT_PATH_FILE_H_
```

Or use `#pragma once` (non-standard but widely supported).

### Include Order
```cpp
// 1. Related header (for .cc files)
#include "foo/bar/my_class.h"

// 2. C system headers
#include <unistd.h>

// 3. C++ standard library
#include <string>
#include <vector>

// 4. Other libraries
#include <gtest/gtest.h>

// 5. Project headers
#include "foo/bar/other.h"
```

Alphabetize within each group. Blank line between groups.

## Classes

### Member Order
```cpp
class MyClass {
 public:
  // Types and aliases
  using ValueType = int;

  // Constants
  static constexpr int kMaxSize = 100;

  // Constructors, assignment, destructor
  explicit MyClass(int value);
  MyClass(const MyClass&) = delete;
  MyClass& operator=(const MyClass&) = delete;
  ~MyClass();

  // Other methods
  void DoSomething();
  int count() const { return count_; }
  void set_count(int c) { count_ = c; }

 private:
  // Data members (always private)
  int count_;
  std::string name_;
};
```

### Key Rules
- Mark single-arg constructors `explicit`
- Use `= default` / `= delete` explicitly
- Data members should be `private`
- Avoid virtual calls in constructors/destructors

## Functions

### Parameters
```cpp
// Input params: value or const ref
// Output params: non-const ref or pointer
// Input before output
void ProcessData(const std::string& input,  // input
                 std::vector<int>* output);  // output

// Prefer return values over output parameters
std::vector<int> ProcessData(const std::string& input);
```

## Modern C++

### Use
```cpp
// nullptr, not NULL or 0
int* ptr = nullptr;

// auto when type is obvious
auto it = container.begin();
auto callback = [](int x) { return x * 2; };

// Range-based for
for (const auto& item : container) {
  Process(item);
}

// constexpr for compile-time constants
constexpr int kBufferSize = 1024;

// Smart pointers
std::unique_ptr<MyClass> obj = std::make_unique<MyClass>();
```

### Avoid
```cpp
// No C-style casts
int x = (int)y;           // Bad
int x = static_cast<int>(y);  // Good

// No using namespace
using namespace std;      // Bad
using std::string;        // OK in .cc files

// No exceptions (Google-specific)
// No RTTI unless necessary

// Prefer ++i over i++ for iterators
for (auto it = c.begin(); it != c.end(); ++it)
```

## Comments

```cpp
// File header (if needed)
// Copyright notice here

// Class: describe purpose and usage
// Keep brief - one or two sentences
class MyClass {
  // ...
};

// Functions: describe what, not how
// Document params and return value
// Returns the Foo with the given id, or nullptr if not found.
Foo* GetFoo(int id);

// Inline comments for tricky code only
// Prefer self-documenting code
```

## CMake

```cmake
cmake_minimum_required(VERSION 3.20)
project(MyProject LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Warnings
if(MSVC)
  add_compile_options(/W4)
else()
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()
```

## Windows-Specific

```cpp
// Define before windows.h
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX

#include <windows.h>

// Use wide strings for Windows APIs
std::wstring path = L"C:\\path\\to\\file";

// Prefer std::filesystem over Win32 path APIs
namespace fs = std::filesystem;
```

## Gotchas

| Issue | Solution |
|-------|----------|
| `std::wstring` vs `std::string` | Windows APIs use wide strings |
| Header include cycles | Forward declare when possible |
| `const` correctness | Mark params/methods const when applicable |
| RAII | Use smart pointers, avoid raw `new`/`delete` |
| Move semantics | Implement move ctor/assignment for resource-owning classes |
