# Skills

Skills are markdown-defined workflows that can be invoked via slash commands (e.g., `/build-landing-page`) or detected automatically by the Host Agent from natural language requests.

## Skill File Format

Each skill is a markdown file in this directory. The format:

```markdown
# skill-name

Short description (1-2 sentences) used for search matching.
This helps the Host Agent find the right skill when users describe what they want.

## Instructions

Step-by-step instructions the Host Agent follows when executing this skill.

You can reference:
- Other agents (e.g., "delegate to website_builder_simple")
- MCP tools (e.g., "use terminal_server to run commands")
- Multi-step workflows with conditionals

The Host Agent interprets these instructions and executes them.
```

## Naming Conventions

- Filename: `skill-name.md` (kebab-case)
- The skill name comes from the H1 heading or filename (without `.md`)
- Use descriptive names that hint at what the skill does

## Examples

See the example skills in this directory:
- `list-capabilities.md` — Lists available agents, tools, and skills
- `build-landing-page.md` — Interactive landing page builder

## Invoking Skills

**Slash command (direct):**
```
/build-landing-page I need a dark-themed SaaS landing page
```

**Natural language (detected):**
```
Help me build a landing page for my startup
```

The Host Agent will detect the intent and invoke the matching skill.
