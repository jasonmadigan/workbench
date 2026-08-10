# Kuadrant conventions

Load this reference only for a Kuadrant repository or when the user names the
Kuadrant team view.

## Project board

- Discover the live org-level **Kuadrant** board (#18) through open issues'
  `projectItems`. `repository.projectsV2` can return only the closed Backlog
  board (#23), as it does for `kuadrant-console-plugin`.
- Fields are Status (Todo, In Progress, Ready For Review, In Review, Done),
  Priority (Must, Should, Could), Sprint, Team, Area, Estimate, and Release.
- UI items often have no Priority. Rank them by Sprint and Status. The operative
  team field is Area.
- Saved view 41, **UI Touchgrass Team**, uses
  `area:"UI Touch Grass" sprint:@current` and spans
  `kuadrant-console-plugin`, `kuadrant-backstage-plugin`, and
  `developer-portal-controller`. Reproduce it by paging board items, not by
  walking one repository's issues.

When this view drives selection, identify it in the output header, including
its filter.

## Jira mapping

For any `Kuadrant/*` repository, include CONNLINK tickets when filtering Jira
results to the current repository. This covers repositories such as
`kuadrant-operator` and `mcp-gateway`.
