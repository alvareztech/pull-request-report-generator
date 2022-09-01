#!/usr/bin/env python3
import getopt
import json
import os
import subprocess
import sys
from datetime import datetime

from config import ORGANIZATION, GITHUB_API_TOKEN
from github import API_BASE_URL, TAG_GRAPHQL, GRAPHQL_URL, PR_GRAPHQL
from util import REPOS

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'requests'])
finally:
    import requests

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'jinja2'])
finally:
    from jinja2 import Environment, FileSystemLoader

try:
    import pdfkit
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'pdfkit'])
finally:
    import pdfkit

current_directory = os.path.dirname(os.path.abspath(__file__))
env = Environment(loader=FileSystemLoader(current_directory))
dist_folder = "dist"


def get_endpoint(organization, slug):
    return '%s/repos/%s/%s/' % (API_BASE_URL, organization, slug)


def get_github_pull_request(token, organization, slug, since):
    headers = {'Authorization': 'token %s' % token}
    json_body = {
        'query': TAG_GRAPHQL % (organization, slug, since)
    }
    response = requests.post(url=GRAPHQL_URL, json=json_body, headers=headers)
    json_response = response.json()
    # print(json.dumps(json_response))
    ref = json_response["data"]["organization"]["repository"]["ref"]
    if ref is None:
        print("The repository `%s` doesn't contain the `since` tag.", slug)
        return
    target = ref["target"]
    if "target" in target:
        target = target["target"]
    since_date = target["committedDate"]
    if since_date is None:
        print("The repository `%s` doesn't contain the `committedDate` value.", slug)
        return
    issues_url = "%sissues?state=closed&since=%s" % (get_endpoint(organization, slug), since_date)
    response = requests.get(url=issues_url, headers=headers)
    json_response = response.json()
    json_response.pop()  # Eliminating the PR with the `since` tag
    pull_requests_info = []
    for pr in json_response:
        number = pr["number"]
        json_body = {
            'query': PR_GRAPHQL % (organization, slug, number)
        }
        response = requests.post(url=GRAPHQL_URL, json=json_body, headers=headers)
        json_response = response.json()
        # print(json.dumps(json_response))
        pull_request = json_response["data"]["repository"]["pullRequest"]
        if pull_request is None:
            break
        if pull_request["author"] is not None:
            author = pull_request.get("author", {"login": "", "name": ""})
        else:
            author = {"login": "", "name": ""}

        if pull_request["mergedBy"] is None:
            merged_by = {"login": "", "name": ""}
        else:
            merged_by = pull_request["mergedBy"]

        merge_commit = pull_request["mergeCommit"] or {"oid": ""}
        if not pull_request["merged"]:
            continue

        # To include other branches in the report, this conditional can be changed.
        if pull_request["baseRefName"] != "master":
            continue

        pull_request_info = {
            "number": number,
            "title": str(pull_request["title"]),
            "desc": pull_request["body"],
            "url": pull_request["url"],
            "creator": {
                'user': author["login"] or "FormerEmployee*",
                'name': author["name"] or ""
            },
            "created_at": pull_request["createdAt"],
            "merged_at": str(pull_request["mergedAt"]),
            "merged_by": {
                'user': merged_by["login"] or "FormerEmployee*",
                'name': merged_by["name"] or ""
            },
            "commit": merge_commit["oid"] or "",
            "files": [],
            "reviewers": []
        }
        for file in pull_request["files"]["nodes"]:
            pull_request_info["files"].append(file["path"])
        for reviewer in pull_request["reviews"]["nodes"]:
            pull_request_info["reviewers"].append({
                "user": reviewer["author"]["login"],
                "name": reviewer["author"].get("name"),
                "state": reviewer["state"],
                "updatedAt": reviewer["updatedAt"]
            })
        pull_requests_info.append(pull_request_info)
    return pull_requests_info


def render_template(filename, content):
    return env.get_template(filename).render(content)


def generate_report(slug, pull_requests_data, version):
    all_content = ""
    for pr in pull_requests_data:
        files = ""
        for file in pr["files"]:
            files += file + "<br>"

        reviewers = ""
        for reviewer in pr["reviewers"]:
            name = reviewer["name"] or ""
            updated_at = reviewer["updatedAt"]
            reviewers += name + " (" + reviewer["user"] + ") " + reviewer["state"] + ": " + updated_at + "<br>"
        with_reviewers = render_template("template/header.html", {
            "slug": slug,
            "number": pr["number"],
            "title": pr["title"],
            "desc": pr["desc"],
            "url": pr["url"],
            "created_at": pr["created_at"],
            "creator_user": pr["creator"]["user"],
            "creator_name": pr["creator"]["name"],
            "merged_at": pr["merged_at"],
            "merged_by_user": pr["merged_by"]["user"],
            "merged_by_name": pr["merged_by"]["name"],
            "commit": pr["commit"],
            "files": files,
            "reviewers": reviewers,
            "organization": organization
        })
        all_content += with_reviewers

    result = render_template("template/main.html", {
        "title": 'Pull Request Report',
        "date": datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
        "version": version,
        "slug": slug,
        "content": all_content,
        "organization": organization
    })
    file_path = create_html_file(result, slug, version)
    create_pdf_file(file_path)


def create_html_file(content, slug, version):
    if not os.path.exists(dist_folder):
        os.makedirs(dist_folder)
    file_path = "%s/pr_report_%s_%s.html" % (dist_folder, slug, version)
    f = open(file_path, "w")
    f.write(content)
    f.close()
    return file_path


def create_pdf_file(file_path):
    options = {
        'page-size': 'Letter',
        'margin-top': '0.75in',
        'margin-right': '1in',
        'margin-bottom': '0.75in',
        'margin-left': '1in',
        'encoding': "UTF-8",
        'no-outline': None,
        'footer-right': '[page] of [topage]'
    }
    pdfkit.from_file(file_path, file_path.replace(".html", ".pdf"), options=options)


def main(argv):
    since = None
    until = None
    repos = None
    github_api_token = GITHUB_API_TOKEN
    organization = ORGANIZATION
    try:
        opts, args = getopt.getopt(argv, "hs:u:r:t:", ["help", "since=", "until=", "repos=", "token="])
    except getopt.GetoptError:
        print('ERROR: Example --since v2.0 --until v2.8 --repos my_repo,my_repo2 --token abc')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            print('HELP: Example --since v2.0 --until v2.8 --repos my_repo,my_repo2 --token abc')
            sys.exit()
        elif opt in ("-s", "--since"):
            since = arg
        elif opt in ("-u", "--until"):
            until = arg
        elif opt in ("-r", "--repos"):
            if arg == "REPOS":
                repos = REPOS
            else:
                repos = arg.split(",")
        elif opt in ("-t", "--token"):
            github_api_token = arg
    print('Since', since)
    print('Until', until)
    print('Repositories', repos)
    for repo in repos:
        print("Repository", repo)
        pull_requests_data = get_github_pull_request(github_api_token, organization, repo, since=since)
        if pull_requests_data:
            generate_report(repo, pull_requests_data, version=until)


if __name__ == '__main__':
    main(sys.argv[1:])
