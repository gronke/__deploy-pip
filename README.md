PyPi Deployment (Service Reposity)
==================================

This service repository hosts secrets for deployment to PyPi registry.
Because contributors of a source repository can globally access GitHub Secrets, a protected branch is not enough to constrain access.

How does it work?
-----------------

When a new git tag has been published to the source repository, a GitHub Workflow step triggers a bot account, @gronke-bot, to create a new Issue in this repository.
No other account has permission to write to *this* repository, and the `master` branch of the remote repository can be trusted, because it is protected with requirement to pass a review by the global code owner (defined in `.github/CODEOWNERS`).
Now the tag commit can be checked to exist in the source repository master branch history, or the deployment will be cancelled.
The secret PyPi API Token has never been exposed during this process.

What can be improved?
---------------------

This repository could be owned by a third (service) account, which is unrelated to the bot posting the GitHub Issue to trigger this workflow.
The bot must not be a contributor of this repository, but is mentioned within the sources to be authenticated by GitHub user name to trigger a deployment.
(Every issue created by somebody else is just ignored.)
