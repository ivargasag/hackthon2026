import argparse
import os
import re
import sys
from openai import AzureOpenAI, OpenAI


def load_simple_dotenv(dotenv_path=".env"):
  """Load KEY=VALUE pairs from .env into environment if not already set."""
  if not os.path.exists(dotenv_path):
    return

  with open(dotenv_path, "r", encoding="utf-8") as env_file:
    for raw_line in env_file:
      line = raw_line.strip()
      if not line or line.startswith("#") or "=" not in line:
        continue

      key, value = line.split("=", 1)
      key = key.strip()
      value = value.strip().strip('"').strip("'")
      if key and os.getenv(key) is None:
        os.environ[key] = value


class PlaywrightTestGenerator:
  def __init__(
    self,
    api_key,
    model="gpt-5.1",
    provider="azure",
    azure_endpoint=None,
    azure_api_version="2024-12-01-preview",
    allow_local_fallback=True,
  ):
    self.provider = provider
    self.model = model
    self.allow_local_fallback = allow_local_fallback
    self.client = None

    if provider == "azure":
      if not azure_endpoint:
        if not self.allow_local_fallback:
          raise ValueError("azure_endpoint is required when provider is 'azure'.")
      elif not api_key:
        if not self.allow_local_fallback:
          raise ValueError("API key is required when provider is 'azure'.")
      else:
        self.client = AzureOpenAI(
          api_key=api_key,
          azure_endpoint=azure_endpoint,
          api_version=azure_api_version,
        )
    else:
      if not api_key:
        if not self.allow_local_fallback:
          raise ValueError("API key is required when provider is 'openai'.")
      else:
        self.client = OpenAI(api_key=api_key)

  def generate_test_from_description(self, description, url=None):
    """Generate Playwright test from natural language description."""

    prompt = f"""
Generate a Playwright JavaScript test based on this description: {description}

Requirements:
- Use @playwright/test in JavaScript (CommonJS)
- Include imports: const {{ test, expect }} = require('@playwright/test');
- Include a BASE_URL constant set to the target URL
- Add meaningful assertions
- Use stable Playwright locators (getByRole/getByLabel/getByText) when possible
- Include error handling where appropriate
- URL: {url if url else 'determine from context'}

Return only JavaScript code, properly formatted.
"""

    try:
      response = self.client.chat.completions.create(
        model=self.model,
        messages=[
          {
            "role": "system",
            "content": "You are an expert Playwright JavaScript test automation engineer. Generate clean, maintainable JS test code."
          },
          {"role": "user", "content": prompt}
        ],
        temperature=0.3,
      )
      return response.choices[0].message.content
    except Exception as exc:
      if not self.allow_local_fallback:
        raise
      print(
        f"Warning: remote generation failed ({type(exc).__name__}). Using local fallback template.",
        file=sys.stderr,
      )
      return self._build_local_description_test(description, url)

  def generate_test_from_user_story(self, user_story):
    """Generate test from user story format."""

    prompt = f"""
Convert this user story into a Playwright JavaScript test:

{user_story}

Generate a complete JavaScript test file with:
1. Proper setup and navigation
2. All user interactions
3. Assertions for expected outcomes
4. Error handling
5. Clear comments

Format as a complete JS Playwright file with imports.
"""

    try:
      response = self.client.chat.completions.create(
        model=self.model,
        messages=[
          {
            "role": "system",
            "content": "You are a JavaScript test automation expert. Create comprehensive Playwright JS tests from user stories."
          },
          {"role": "user", "content": prompt}
        ],
        temperature=0.2,
      )
      return response.choices[0].message.content
    except Exception as exc:
      if not self.allow_local_fallback:
        raise
      print(
        f"Warning: remote generation failed ({type(exc).__name__}). Using local fallback template.",
        file=sys.stderr,
      )
      return self._build_local_story_test(user_story)

  def generate_test_from_code_change(self, code_change):
    """Generate Playwright JavaScript test from a code diff or change snippet."""

    prompt = f"""
You are given a code change snippet. Generate a focused Playwright JavaScript test that validates the behavioral outcome of this change.

Code change:
{code_change}

Requirements:
- Use @playwright/test in JavaScript (CommonJS)
- Include imports: const {{ test, expect }} = require('@playwright/test');
- Include a BASE_URL constant set to http://localhost:3000
- Navigate with await page.goto(BASE_URL)
- Prefer stable selectors (role, label, text) when possible
- Add assertions that verify the changed behavior
- Include short comments only where needed
- Return only JavaScript code
"""

    try:
      response = self.client.chat.completions.create(
        model=self.model,
        messages=[
          {
            "role": "system",
            "content": "You are an expert Playwright JavaScript test automation engineer. Generate robust JS tests from code diffs."
          },
          {"role": "user", "content": prompt}
        ],
        temperature=0.2,
      )
      return response.choices[0].message.content
    except Exception as exc:
      if not self.allow_local_fallback:
        raise
      print(
        f"Warning: remote generation failed ({type(exc).__name__}). Using local fallback template.",
        file=sys.stderr,
      )
      return self._build_local_change_test(code_change)

  def _extract_url_from_text(self, text):
    url_match = re.search(r"https?://[^\s)\]\}]+", text)
    return url_match.group(0) if url_match else None

  def _escape_js_single_quote(self, value):
    return value.replace('\\', '\\\\').replace("'", "\\'")

  def _build_local_description_test(self, description, url=None):
    target_url = url or self._extract_url_from_text(description) or "https://example.com"
    escaped_url = self._escape_js_single_quote(target_url)
    return f'''const {{ test, expect }} = require('@playwright/test');

const BASE_URL = '{escaped_url}';

test.describe('Auto-generated from description', () => {{
  test('runs described flow', async ({{ page }}) => {{
    await page.goto(BASE_URL);

    // TODO: Replace placeholder selectors with app-specific stable locators.
    await page.getByLabel('Username').fill('valid_user');
    await page.getByLabel('Password').fill('valid_password');
    await page.getByRole('button', {{ name: 'Sign in' }}).click();

    // Generic post-login assertion; adjust to your product language if needed.
    await expect(page.getByRole('heading', {{ name: /dashboard/i }})).toBeVisible();
  }});
}});
'''

  def _build_local_story_test(self, user_story):
    escaped_story = self._escape_js_single_quote(user_story)
    return f'''const {{ test, expect }} = require('@playwright/test');

const BASE_URL = 'http://localhost:3000';

test.describe('Auto-generated from user story', () => {{
  test('story scaffold', async ({{ page }}) => {{
    const story = '{escaped_story}';
    expect(story.trim().length).toBeGreaterThan(0);

    await page.goto(BASE_URL);

    // TODO: Implement concrete user interactions and assertions from the story.
    await expect(page.locator('body')).toBeVisible();
  }});
}});
'''

  def _extract_visible_text(self, line_text):
    html_text_match = re.search(r">([^<>]+)<", line_text)
    if html_text_match:
      return html_text_match.group(1).strip()
    return line_text.strip()

  def _build_local_change_test(self, code_change):
    file_match = re.search(r"^\s*([^\n\r]+\.[A-Za-z0-9]+)\s*$", code_change, re.MULTILINE)
    old_match = re.search(r"^\s*-\s*(.+)$", code_change, re.MULTILINE)
    new_match = re.search(r"^\s*\+\s*(.+)$", code_change, re.MULTILINE)

    changed_file = file_match.group(1).strip() if file_match else "unknown_file"
    old_line = old_match.group(1).strip() if old_match else "old value"
    new_line = new_match.group(1).strip() if new_match else "new value"

    old_expectation = self._extract_visible_text(old_line)
    new_expectation = self._extract_visible_text(new_line)

    escaped_new = self._escape_js_single_quote(new_expectation)
    escaped_old = self._escape_js_single_quote(old_expectation)

    return f'''const {{ test, expect }} = require('@playwright/test');

const BASE_URL = 'http://localhost:3000';

test.describe('Auto-generated from code change', () => {{
  test('validates changed behavior for {changed_file}', async ({{ page }}) => {{
    await page.goto(BASE_URL);

    // Validate that the new text appears and the old text no longer appears.
    await expect(page.getByText('{escaped_new}')).toBeVisible();
    await expect(page.getByText('{escaped_old}')).not.toBeVisible();
  }});
}});
'''


def main():
  load_simple_dotenv()

  parser = argparse.ArgumentParser(description="Generate Playwright JavaScript tests using OpenAI.")
  parser.add_argument("--provider", choices=["azure", "openai"], default=os.getenv("OPENAI_PROVIDER", "azure"))
  parser.add_argument("--api-key", default=os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"), help="API key")
  parser.add_argument("--mode", choices=["description", "story", "change"], default="description")
  parser.add_argument("--text", required=True, help="Description, user story, or code change input")
  parser.add_argument("--url", default=None, help="Optional URL for description mode")
  parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5.1"), help="Model or deployment name")
  parser.add_argument("--azure-endpoint", default=os.getenv("AZURE_OPENAI_ENDPOINT"), help="Azure endpoint, e.g. https://<resource>.openai.azure.com/")
  parser.add_argument("--azure-api-version", default=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"), help="Azure API version")
  parser.add_argument("--no-local-fallback", action="store_true", help="Disable local template fallback if remote API fails")
  args = parser.parse_args()

  if not args.api_key and args.no_local_fallback:
    raise ValueError("API key is required when fallback is disabled. Set AZURE_OPENAI_API_KEY/OPENAI_API_KEY or pass --api-key.")

  if args.provider == "azure" and not args.azure_endpoint and args.no_local_fallback:
    raise ValueError("Azure endpoint is required when fallback is disabled. Set AZURE_OPENAI_ENDPOINT or pass --azure-endpoint.")

  generator = PlaywrightTestGenerator(
    api_key=args.api_key,
    model=args.model,
    provider=args.provider,
    azure_endpoint=args.azure_endpoint,
    azure_api_version=args.azure_api_version,
    allow_local_fallback=not args.no_local_fallback,
  )

  if args.mode == "description":
    generated_test = generator.generate_test_from_description(args.text, args.url)
  elif args.mode == "change":
    generated_test = generator.generate_test_from_code_change(args.text)
  else:
    generated_test = generator.generate_test_from_user_story(args.text)

  print(generated_test)


if __name__ == "__main__":
  main()
