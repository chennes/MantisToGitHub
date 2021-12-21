# -*- coding: utf-8 -*-

#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2021 Chris Hennes <chennes@pioneerlibrarysystem.org>    *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENSE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

import os
import json
import csv
import sys
import itertools
import requests
import urllib
import urllib.request
import urllib.error
import urllib.response
import urllib.parse
import time
from typing import Dict, List, Optional

from bbcode_to_markdown import BBCodeToMarkdown

#########################################################################################
#                                     CONFIGURATION                                     #
#########################################################################################

# Mantis data should be exported with the following CSV data set:
# id, project_id, reporter_id, handler_id, priority, severity, reproducibility, version, category_id, date_submitted, os, os_build, platform, view_state, last_updated, summary, description, status, resolution, fixed_in_version, additional_information, attachment_count, bugnotes_count, notes, tags, source_related_changesets, custom_FreeCAD Information
MANTIS_EXPORT_PATH = "./chennes-7.csv"

# The real values for the final import
#GITHUB_REPO_OWNER = "FreeCAD"
#GITHUB_REPO_NAME = "FreeCAD"

# For testing
GITHUB_REPO_OWNER = "chennes"
GITHUB_REPO_NAME = "MantisToGitHub"

# The GitHub API token file should contain a single JSON object specifying the
# username and api key, e.g.
# {
#   "username":"jsmith",
#   "apikey":"abcdefghijklmnopqrstuvwxyz"
# }
# This key should be configured with repo access.
GITHUB_API_TOKEN_FILE = "github.txt" # !!!! DO NOT ADD THIS FILE TO THE GIT REPO !!!!

MANTIS_TO_GITHUB_USERNAME_MAP = {
    "abdullah":"abdullahtahiriyo" ,
    "AR795":"" ,
    "berndhahnebach":"berndhahnebach" ,
    "carlopav":"carlopav" ,
    "chennes":"chennes" ,
    "chrisb":"" ,
    "David_D":"" ,
    "DeepSOIC":"deepsoic" ,
    "eivindkvedalen":"eivindkv" ,
    "howetuft":"" ,
    "HoWil":"" ,
    "hyarion":"hyarion" ,
    "ian.rees":"ianrees" ,
    "ickby":"ickby" ,
    "kkremitzki":"kkremitzki" ,
    "Kunda1":"luzpaz" ,
    "looo":"looooo" ,
    "mlampert":"mlampert" ,
    "openBrain":"0penBrain" ,
    "paullee":"paullee0" ,
    "realthunder":"realthunder" ,
    "russ4262":"Russ4262" ,
    "sgrogan":"sgrogan" ,
    "shaiseger":"shaise" ,
    "shoogen":"5263" ,
    "sliptonic":"sliptonic" ,
    "triplus":"triplus" ,
    "uwestoehr":"donovaly" ,
    "vejmarie":"vejmarie" ,
    "wandererfan":"WandererFan" ,
    "wmayer":"wwmayer" ,
    "yorik":"yorikvanhavre"
}

# Not all Mantis projects have corresponding GitHub labels: for those that do,
# this map does the translation between them
MANTIS_PROJECT_TO_GITHUB_LABEL_MAP = {
    "Arch":"🏛 Arch",
    "Bug":"🐛 bug",
    "FreeCAD":"core",
    "Draft":"📐 Draft",
    "FEM":"🧪 FEM",
    "Part":"Part",
    "PartDesign":"🚜 PartDesign",
    "Path":"🛤️ Path",
    "Sketcher":"✏️ Sketcher",
    "Spreadsheet":"Spreadsheet",
    "TechDraw":"TechDraw"
}


#########################################################################################


class Issue:

    def __init__(self, row_data):
        if len(row_data) < 27 :
            raise RuntimeError(f"Expected 27 fields in CSV row, found only {len(row_data)}")
        element_index = itertools.count(0)
        self.id = row_data[next(element_index)]
        self.project = row_data[next(element_index)]
        self.reporter = row_data[next(element_index)]
        self.assigned_to = row_data[next(element_index)]
        self.priority = row_data[next(element_index)]
        self.severity = row_data[next(element_index)]
        self.reproducibility = row_data[next(element_index)]
        self.product_version = row_data[next(element_index)]
        self.target_version = row_data[next(element_index)]
        self.category = row_data[next(element_index)]
        self.date_submitted = row_data[next(element_index)]
        self.os = row_data[next(element_index)]
        self.os_version = row_data[next(element_index)]
        self.platform = row_data[next(element_index)]
        self.view_status = row_data[next(element_index)]
        self.updated = row_data[next(element_index)]
        self.summary = row_data[next(element_index)]
        self.description = row_data[next(element_index)]
        self.steps_to_reproduce = row_data[next(element_index)]
        self.status = row_data[next(element_index)]
        self.resolution = row_data[next(element_index)]
        self.fixed_in_version = row_data[next(element_index)]
        self.additional_information = row_data[next(element_index)]
        self.num_attachments = row_data[next(element_index)]
        self.num_notes = row_data[next(element_index)]
        self.notes = row_data[next(element_index)]
        self.tags = row_data[next(element_index)]
        self.related = row_data[next(element_index)]
        self.freecad_information = row_data[next(element_index)]

    def to_github_api_fields(self) -> Dict[str,str]:
        # GitHub REST API fields for creating an issue:
        # accept(string), header	Setting to application/vnd.github.v3+json is recommended.
        # owner(string), path	
        # repo(string), path	
        # title(string), body	Required. The title of the issue.
        # body(string), body	The contents of the issue.
        # assignee(string), body	Login for the user that this issue should be assigned to. NOTE: Only users with push access can set the assignee for new issues. The assignee is silently dropped otherwise. This field is deprecated.
        # milestone(string), body	The number of the milestone to associate this issue with. NOTE: Only users with push access can set the milestone for new issues. The milestone is silently dropped otherwise.
        # labels(array of strings), body	Labels to associate with this issue. NOTE: Only users with push access can set labels for new issues. Labels are silently dropped otherwise.
        # assignees(array of strings), body	Logins for Users to assign to this issue. NOTE: Only users with push access can set assignees for new issues. Assignees are silently dropped otherwise.
        result = {}
        result["title"] = self.summary
        result["body"] = self._create_markdown()
        #if self.target_version:
        #    result["milestone"] = self.target_version
        if self.assigned_to:
            result["assignees"] = self._map_assignee()
        result["labels"] = self._create_labels()
        return result

    def _create_markdown(self) -> str:
        md = ""
        md += f"Issue imported from https://tracker.freecad.org/view.php?id={self.id}\n\n"
        md += f"* **Reporter:** {self.reporter}\n"
        md += f"* **Date submitted:** {self.date_submitted}\n"
        md += f"* **FreeCAD version:** {self.product_version}\n"
        md += f"* **Category:** {self.category}\n"
        md += f"* **Status:** {self.status}\n"
        md += f"* **Tags:** {self.tags}\n"
        md += f"\n\n# Original report text\n\n"
        md += BBCodeToMarkdown(self.description,MANTIS_TO_GITHUB_USERNAME_MAP).md()
        if self.additional_information:
            md += f"\n\n# Additional information\n\n"
            md += BBCodeToMarkdown(self.additional_information,MANTIS_TO_GITHUB_USERNAME_MAP).md()
        if self.steps_to_reproduce:
            md += f"\n\n# Steps to reproduce\n\n"
            md += BBCodeToMarkdown(self.steps_to_reproduce,MANTIS_TO_GITHUB_USERNAME_MAP).md()
        cleaned_freecad_info = self._clean_freecad_info()
        if "Build type" in cleaned_freecad_info: # "Build type" is one of the strings that should always be there
            md += f"\n\n# FreeCAD Info\n\n"
            md += f"```\n{cleaned_freecad_info}\n```"
        md += "\n\n# Other bug information\n\n"
        if self.priority:
            md += f"* **Priority:** {self.priority}\n"
        if self.severity:
            md += f"* **Severity:** {self.severity}\n"
        #if self.reproducibility:
        #    md += f"* **Reproducibility:** {self.reproducibility}\n"
        if self.category:
            md += f"* **Category:** {self.category}\n"
        if self.os or self.os_version:
            md += f"* **OS: {self.os} {self.os_version}**\n"
        if self.platform:
            md += f"* **Platform:** {self.platform}\n"
        #if self.view_status:
        #    md += f"* **View status:** {self.view_status}\n"
        if self.updated:
            md += f"* **Updated:** {self.updated}\n"
        #if self.resolution:
        #    md += f"* **Resolution:** {self.resolution}\n"
        if self.fixed_in_version:
            md += f"* **Fixed in version:** {self.fixed_in_version}\n"
        try:
            num_notes = int(self.num_notes)
        except Exception:
            num_notes = 0
        if self.notes and num_notes > 0:
            md += f"\n\n# Discussion from Mantis ticket\n\n"
            md += self._process_comments()
        return md

    def _map_assignee(self) -> Optional[List[str]]:
        if self.assigned_to in MANTIS_TO_GITHUB_USERNAME_MAP:
            mapped_value = MANTIS_TO_GITHUB_USERNAME_MAP[self.assigned_to]
            if mapped_value:
                return [mapped_value]
        return None

    def _create_labels(self) -> List[str]:
        # For FreeCAD's purposes, the only label we use is the project name:
        labels = []
        if self.project in MANTIS_PROJECT_TO_GITHUB_LABEL_MAP:
            labels.append (MANTIS_PROJECT_TO_GITHUB_LABEL_MAP[self.project])
        else:
            labels.append (self.project)
        if self.category == "Bug":
            labels.append ("🐛 bug")
        elif self.category == "Feature":
            labels.append ("Feature")
        return labels

    def _clean_freecad_info(self) -> str:
        text_to_remove = """<!--ATTENTION:
COMPLETELY ERASE THIS AFTER PASTING YOUR 
Help > About FreeCAD > Copy to clipboard 
NOTE: just the snippet alone will do without anything else included.
The ticket will not be submitted without it.
-->"""
        if self.freecad_information.startswith(text_to_remove):
            return self.freecad_information[len(text_to_remove):]
        else:
            return self.freecad_information

    def _process_comments(self) -> str:
        split_comments = self.notes.split("\n=-=\n")
        comments = ""
        first = True
        for comment in reversed(split_comments):
            if not first:
                comments += "\n\n---\n\n"
            else:
                first = False
            this_comment_text = BBCodeToMarkdown(comment,MANTIS_TO_GITHUB_USERNAME_MAP).md()
            comment_lines = this_comment_text.split("\n")
            first_line = True
            for comment_line in comment_lines:
                if first_line:
                    first_line = False
                    comments += "### Comment by " + comment_line + "\n"
                else:
                    comments += comment_line + "\n"
        comments += "\n"
        return comments


def load_api_key(filename:str) -> Dict[str,str]:
    with open(filename,"r") as f:
        api_key_json = f.read()
        api_key = json.loads(api_key_json)
        if not "username" in api_key:
            print (f"Malformed API key file {filename}: no username")
            exit(1)
        if not "apikey" in api_key:
            print (f"Malformed API key file {filename}: no apikey")
            exit(1)
    return api_key

def csv_iteration_wrapper(csv_iterator):
    """ Iteration over the CSV might encounter all manner of errors: turn them into warnings. """

    counter = 0
    while True:
        try:
            counter += 1
            yield next(csv_iterator)
        except StopIteration:
            break
        except Exception as e:
            print(f"WARNING: CSV reader encountered an error and skipped row {counter} ({e})")

if __name__ == '__main__':

    github_api_key = load_api_key(GITHUB_API_TOKEN_FILE)

    if not os.path.isfile(MANTIS_EXPORT_PATH):
        print (f"Could not locate {MANTIS_EXPORT_PATH}")
        exit(1)

    counter = 0
    sys.stdout.reconfigure(encoding='utf-8') # Beat MSYS2 into submission
    trigger_start_at_issue = None
    with open (MANTIS_EXPORT_PATH, "r", encoding="utf-8", errors='ignore') as f:
        csv.field_size_limit(2147483647) # Some of these bug reports are very large...
        csv_reader = csv.reader(f, delimiter=',', quotechar='"')

        for row in csv_iteration_wrapper(csv_reader):
            try:
                if len(row) > 0:
                    try:
                        id = int(row[0])
                    except Exception:
                        continue

                    if trigger_start_at_issue is not None:
                        if id == trigger_start_at_issue:
                            trigger_start_at_issue = None
                        else:
                            continue

                    print (f"Processing issue ID {id}")
                    issue = Issue(row)
                    counter += 1

                    url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/issues"
                    headers = {
                        "Authorization":f"token {github_api_key['apikey']}",
                        "accept":"application/vnd.github.v3+json"
                    }

                    try:
                        try_again = True
                        while try_again:
                            r = requests.post(url, headers=headers, json=issue.to_github_api_fields())
                            if r.status_code == 201:
                                try_again = False
                                response = r.json()

                                print (f"Mantis issue {id} migrated to GitHub issue {response['number']} ({response['html_url']})")
                                time.sleep(1) # Avoid the secondary rate limiter by waiting one second between requests
                            elif r.status_code == 403:
                                # Probably we hit a rate limit: check for the try_again header
                                if "Retry-After" in r.headers:
                                    wait_for = int(r.headers["Retry-After"])
                                    print (f"Hit rate limiter, will re-try in {wait_for} seconds")
                                    time.sleep(wait_for)
                                else:
                                    print (f"Received a 403 error when trying to migrate issue {id}. Stopping.")
                                    exit(r.status_code)
                            else:
                                print (f"Received a {r.status_code} error when trying to migrate issue {id}. Stopping.")
                                exit(r.status_code)

                    except Exception as e:
                        print ("Failed to create GitHub issue:")
                        print (url)
                        print (headers)
                        print (e)
                        exit(1)

            except RuntimeError as e:
                print (e)

    print ("*"*90)
    print ("SUMMARY")
    print ("*"*90)
    print (f"Found {counter} issues in the CSV file")
