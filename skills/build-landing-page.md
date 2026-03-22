# build-landing-page

Interactively build a landing page by gathering requirements and delegating to the website builder agent.

## Instructions

When the user wants to build a landing page:

1. **Gather requirements** — Ask clarifying questions if not already provided:
   - What is the purpose of the landing page? (SaaS product, portfolio, event, etc.)
   - What theme/style do you prefer? (dark, light, colorful, minimal)
   - What sections should be included? (hero, features, pricing, testimonials, CTA, footer)
   - Any specific colors, branding, or content to include?

2. **Summarize the plan** — Before building, confirm with the user:
   - "I'll create a [theme] landing page with [sections] for [purpose]. Sound good?"

3. **Delegate to website builder** — Use the `_delegate_task` tool to send a detailed request to the `website_builder_simple` agent:
   - Include all gathered requirements in the message
   - Be specific about theme, sections, and any content

4. **Return the result** — Present the generated HTML/CSS/JS code to the user.

5. **Offer iterations** — Ask if they want any changes or additions to the page.
