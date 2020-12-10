"""Import pull requests."""
from dataclasses import dataclass

from retrocookie.pr import appname
from retrocookie.pr import events
from retrocookie.pr.base.bus import Bus
from retrocookie.pr.base.bus import Context
from retrocookie.pr.cache import Cache
from retrocookie.pr.protocols import github
from retrocookie.pr.protocols.retrocookie import Retrocookie
from retrocookie.pr.repository import Repository


@dataclass
class Importer:
    """Importer for pull requests."""

    project: Repository
    template: Repository
    bus: Bus
    cache: Cache
    retrocookie: Retrocookie

    def import_(
        self,
        project_pull: github.PullRequest,
        *,
        force: bool = False,
    ) -> None:
        """Import the given pull request from the project into its template."""
        template_branch = f"{appname}/{project_pull.branch}"
        head = f"{self.template.github.owner}:{template_branch}"
        template_pull = self.template.github.pull_request_by_head(head)
        event: Context

        if template_pull is None:
            event = events.CreatePullRequest(self.template.github, head, project_pull)
        elif force:
            event = events.UpdatePullRequest(
                self.template.github, template_pull, project_pull
            )
        else:
            self.bus.events.raise_(
                events.PullRequestAlreadyExists(
                    self.template.github, template_pull, project_pull
                )
            )

        with self.bus.contexts.publish(event):
            with self.cache.worktree(
                self.template.clone, template_branch, force=True
            ) as worktree:
                self.retrocookie(
                    self.project.clone.path,
                    branch=project_pull.branch,
                    upstream=self.project.github.default_branch,
                    path=worktree.path,
                )
            # https://stackoverflow.com/a/41153073/1355754
            self.template.clone.push(
                self.template.github.push_url, f"+{template_branch}", force=force
            )

            if template_pull is None:
                template_pull = self.template.github.create_pull_request(
                    head=head,
                    title=project_pull.title,
                    body=project_pull.body,
                    labels=project_pull.labels,
                )
            else:
                template_pull.update(
                    title=project_pull.title,
                    body=project_pull.body,
                    labels=project_pull.labels,
                )

        if isinstance(event, events.CreatePullRequest):
            self.bus.events.publish(
                events.PullRequestCreated(
                    self.template.github, template_pull, project_pull
                )
            )
