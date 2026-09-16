---
name: windows/dotnet-testing
description: .NET testing - MSTest, NUnit, xUnit patterns
invocation: auto
---

# .NET Testing

## Framework Selection

| Framework | When                | Trigger                |
| --------- | ------------------- | ---------------------- |
| xUnit     | Modern, DI-friendly | `[Fact]` `[Theory]`    |
| NUnit     | Constraint model    | `[Test]` `Assert.That` |
| MSTest    | VS/legacy           | `[TestMethod]`         |

## Lifecycle

| xUnit              | NUnit            | MSTest              |
| ------------------ | ---------------- | ------------------- |
| Constructor        | `[SetUp]`        | `[TestInitialize]`  |
| `IDisposable`      | `[TearDown]`     | `[TestCleanup]`     |
| `IClassFixture<T>` | `[OneTimeSetUp]` | `[ClassInitialize]` |

## Parameterized

```csharp
// xUnit
[Theory] [InlineData(2,3,5)]
public void Add(int a, int b, int exp) => Assert.Equal(exp, a+b);

// NUnit
[TestCase(2,3,5)]
public void Add(int a, int b, int exp) => Assert.That(a+b, Is.EqualTo(exp));

// MSTest
[DataTestMethod] [DataRow(2,3,5)]
public void Add(int a, int b, int exp) => Assert.AreEqual(exp, a+b);
```

## Assertions

| xUnit                    | NUnit                               | MSTest                            |
| ------------------------ | ----------------------------------- | --------------------------------- |
| `Assert.Equal(exp,act)`  | `Assert.That(act, Is.EqualTo(exp))` | `Assert.AreEqual(exp,act)`        |
| `Assert.Throws<T>(()=>)` | `Assert.Throws<T>(()=>)`            | `Assert.ThrowsException<T>(()=>)` |
| `Assert.Contains(s,str)` | `Assert.That(str, Does.Contain(s))` | `StringAssert.Contains(str,s)`    |
| `Assert.Collection(...)` | `Assert.That(c, Has.Member(x))`     | `CollectionAssert.Contains(c,x)`  |

## Mocking (Moq)

```csharp
var mock = new Mock<IService>();
mock.Setup(s => s.Get(It.IsAny<int>())).Returns("val");
mock.Verify(s => s.Get(42), Times.Once);
```

## Setup

```bash
dotnet add package xunit xunit.runner.visualstudio  # xUnit
dotnet add package NUnit NUnit3TestAdapter          # NUnit
dotnet add package MSTest.TestFramework MSTest.TestAdapter  # MSTest
dotnet add package Moq                              # Mocking
```

Run: `dotnet test` | Filter: `dotnet test --filter "Category=Smoke"`
