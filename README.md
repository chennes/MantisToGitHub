# Mantis to GitHub converter

This script uses the REST API GitHub to transfer active (open) issues from a
Mantis bug database CSV export into a GitHub Issue database. Note that although the existing issue ID
from Mantis is encoded into the GitHub issue text, the GitHub issue will be created with an
entirely new (non-configurable) issue ID.

The GitHub issues will be created using the account that is used to access the REST API, so
it is recommended that a new GitHub user account be created explicitly for this purpose.
