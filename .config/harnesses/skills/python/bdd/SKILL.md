---
name: python/bdd
description: BDD testing with Behave - Gherkin features, step definitions, hooks
invocation: auto
---

# BDD with Behave

## Structure

```
features/
├── login.feature           # Gherkin specs
├── steps/
│   └── login_steps.py      # Step implementations
├── environment.py          # Hooks
└── conftest.py             # Shared fixtures
```

## Feature File

```gherkin
Feature: User Login
  As a registered user
  I want to log into the application

  Background:
    Given I am on the login page

  Scenario: Successful login
    When I enter "user@test.com" as email
    And I enter "password123" as password
    And I click login
    Then I should see the dashboard

  Scenario Outline: Login with various users
    When I enter "<email>" as email
    And I enter "<password>" as password
    And I click login
    Then I should see "<result>"

    Examples:
      | email          | password | result    |
      | admin@test.com | admin123 | Dashboard |
      | bad@test.com   | wrong    | Error     |
```

## Step Definitions

```python
from behave import given, when, then

@given('I am on the login page')
def step_on_login(context):
    context.browser.get(context.base_url + '/login')

@when('I enter "{text}" as email')
def step_enter_email(context, text):
    context.browser.find_element(By.ID, 'email').send_keys(text)

@when('I enter "{text}" as password')
def step_enter_password(context, text):
    context.browser.find_element(By.ID, 'password').send_keys(text)

@when('I click login')
def step_click_login(context):
    context.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

@then('I should see the dashboard')
def step_see_dashboard(context):
    assert '/dashboard' in context.browser.current_url
```

## Environment Hooks

```python
# features/environment.py
from selenium import webdriver

def before_all(context):
    context.base_url = 'http://localhost:3000'

def before_scenario(context, scenario):
    context.browser = webdriver.Chrome()
    context.browser.implicitly_wait(10)

def after_scenario(context, scenario):
    if scenario.status == 'failed':
        context.browser.save_screenshot(f'screenshots/{scenario.name}.png')
    context.browser.quit()
```

## Tags

```gherkin
@smoke
Feature: Login
  @critical @wip
  Scenario: ...
```

```bash
behave --tags=@smoke
behave --tags="@smoke and not @wip"
behave --tags="@critical or @smoke"
```

## Commands

| Command                          | Purpose              |
| -------------------------------- | -------------------- |
| `behave`                         | Run all features     |
| `behave features/login.feature`  | Run specific feature |
| `behave --tags=@smoke`           | Run tagged scenarios |
| `behave --format json -o report` | JSON report          |
| `behave --dry-run`               | Validate without run |
| `behave --no-capture`            | Show print output    |

## Step Patterns

```python
# Regex capture
@when('I wait for {seconds:d} seconds')
def step_wait(context, seconds):
    time.sleep(seconds)

# Table data
@given('the following users exist')
def step_users_exist(context):
    for row in context.table:
        create_user(row['name'], row['email'])

# Multi-line text
@given('the config is')
def step_config(context):
    config = yaml.safe_load(context.text)
```

## Setup

```bash
pip install behave selenium
```

[[python/testing]] [[python/mocking]] [[python/conftest]]
