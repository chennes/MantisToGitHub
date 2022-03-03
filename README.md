# Mantis to GitHub converter

This script uses the REST API GitHub to transfer active (open) issues from a
Mantis bug database CSV export into a GitHub Issue database. See the code for the columns
required. Note that although the existing issue ID from Mantis is encoded into the GitHub 
issue text, the GitHub issue will be created with an entirely new (non-configurable) issue ID.

## Details

The GitHub issues will be created using the account that is used to access the REST API, so
it is recommended that a new GitHub user account be created explicitly for this purpose. You
will then need to create a GitHub access token for that account with permission to create
issues. That token should be stored in a file someplace: there is a configuration variable in
the script for setting that file's location.

Second, if you are importing more than about 150 tickets, expect the process to be interrupted
by GitHub's rate limiter. The code will shut itself down when it detects that case: you
will need to wait some length of time (I went with one hour), then restart from the last
ticket attempted. I did not automate that restart process. We imported about 800 tickets, which
took most of the day, running in batches of ~150 each hour.

There are some configuration variables in the source code related to Mantis-to-GitHub username 
mapping: note that if any of the mapped ticket assignees do not have the appropriate GitHub 
permissions, the importer will fail with a 403: Unprocessible Entity error. It will print out 
the name of the failed assignment, which you will either need to remove from the list, or give 
assignment permissions to in your repo.

It is intended that the Mantis instance is kept alive for some significant time after the
migration, in particular to support attachements. As of this writing there is no public,
documented GitHub REST API for uploading files, so this script does not migrate attachments,
instead opting to provide a back-link to the original Mantis ticket.

An auxilliary script is provided to create Mantis database entries linking back to the GitHub
issue. This script is intended to be run on the server with the Mantis instance on it, and has
configuration variables at the top. It requires the BBCodePlus Mantis plugin (or you can 
modify the script to not use the BBCode tags for the URL).

## Example

The FreeCAD project used this importer to migrate our Mantis database: you can see the results
starting at https://github.com/FreeCAD/FreeCAD/issues/5538, and the original issues at
https://tracker.freecad.org
