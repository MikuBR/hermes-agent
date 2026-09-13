# Memory and Experiential Learning v1

## Scopes

Memory is explicitly scoped. The initial hierarchy is:

```text
USER
GLOBAL
PROJECT
SESSION
```

Project memory is shared across sessions belonging to the same project. Session-local material must not leak into another project unless it is deliberately generalized and validated.

## Project resolution

Project identity should combine deterministic signals (repository, working directory, branch, files and explicit project metadata) with contextual signals (recent tasks and keywords). Keywords alone are insufficient for a write decision.

When project identity is uncertain, Hermes must prefer temporary/session-local state over persistent cross-project writes.

## Post-session learning

At session completion, Hermes may analyze the experience:

```text
session -> extraction -> diagnosis -> generalization -> validation -> persistence
```

Candidate knowledge includes facts, decisions, procedures, successful strategies, errors, root causes, constraints, and lessons.

## Anti-trauma rule

An error must not become an unconditional prohibition. Lessons should retain context and validity conditions. A failure in one environment must not automatically disable the ability to attempt the underlying strategy elsewhere.

## Promotion

Session information should be promoted only when its evidence and scope justify persistence. General lessons require stronger validation than project-specific facts.

## External memory

External systems such as Segundo Cérebro/Obsidian are optional providers/integrations. Native memory must remain functional when external memory is disabled.