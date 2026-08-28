---
name: using-git-worktrees
description: Create an isolated, safe workspace for a Jira task when parallel work needs it.
---

# Using Git worktrees

Use only when a task needs parallel local work. First check `git status` is clean and
fetch `origin/develop`. Create a task branch from `origin/develop`, then create a
worktree outside the repository root. Run the baseline harness before changing files.
Never remove a worktree until its PR is merged or intentionally abandoned and the team
has confirmed no uncommitted work remains.
