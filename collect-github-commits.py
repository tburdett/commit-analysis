import os
import unicodecsv
import requests
import json
import re
import getopt
import sys

api_url = "https://api.github.com/"
owner_re = re.compile('\{owner\}')
repo_re = re.compile('\{repo\}')


class Commit:
    def __init__(self, sha, date, short_explanation, committer_name, commit_message, html_url):
        self.sha = sha
        self.date = date
        self.short_explanation = short_explanation
        self.committer_name = committer_name
        self.commit_message = commit_message
        self.html_url = html_url

    def __str__(self):
        try:
            return 'Commit:{sha=\'' + self.sha + '\',date=\'' + self.date + '\',short_explanation=\'' + self.short_explanation + \
                   ',committer=\'' + self.committer_name + '\',commit_message=\'' + self.commit_message + \
                   '\',link=\'' + self.html_url + '\''
        except UnicodeDecodeError:
            print "Something went wrong handling commit " + self.sha


class ApiRequestError(Exception):
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content

    def __str(self):
        return 'API request did not complete OK (' + self.status_code + ': ' + self.content + ').'


def dispatch_api_request(url, user, token):
    s = requests.Session()
    s.auth = (user, token)
    response = s.get(url)
    if response.status_code == 200:
        return json.loads(response.content)
    else:
        raise ApiRequestError(response.status_code, response.content)


def collect_commits_from_github(author, owner, repo, user, token):
    template_repository_url = find_repository(user, token)

    # repository url contains pointers for {owner} and {repo} - replace these
    repository_url = re.sub(repo_re, repo, re.sub(owner_re, owner, template_repository_url))
#    branches_to_sha = find_branches(repository_url, user, token)

    # now collect all commits to master
    commits_url = repository_url + '/commits?author=' + author
    cs = dispatch_api_request(commits_url, user, token)

    commits = []
    master_commit_sha_list = []
    for c in cs:
        sha = c['sha']
        commit_url = c['url']
        commit_response = dispatch_api_request(commit_url, user, token)
        total = commit_response['stats']['total']
        files = len(commit_response['files'])
        additions = commit_response['stats']['additions']
        deletions = commit_response['stats']['deletions']
        short_explanation = '{0} modified files, {1} total changes ({2} additions and {3} deletions)'\
            .format(str(files), str(total), str(additions), str(deletions))

        commit_metadata = c['commit']
        committer_metadata = commit_metadata['committer']
        master_commit_sha_list.append(sha)
        commit = Commit(sha,
                        committer_metadata['date'],
                        short_explanation,
                        committer_metadata['name'],
                        commit_metadata['message'],
                        c['html_url'])
        commits.append(commit)
    return commits


def find_repository(user, token):
    api_response = dispatch_api_request(api_url, user, token)
    return api_response['repository_url']


def find_branches(repository_url, user, token):
    branches_url = repository_url + '/branches'
    branches = dispatch_api_request(branches_url, user, token)

    # now, collect all the branch names and map to sha
    branches_dict = {}
    for branch in branches:
        name = branch['name']
        sha = branch['commit']['sha']
        branches_dict[name] = sha
    return branches_dict


def write_results(results, author, owner, repo):
    dirname = 'output'
    filename = "output/" + str(author) + "_" + str(owner) + ":" + str(repo) + "_commits.csv"

    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            writer = unicodecsv.writer(f, delimiter=',')
            writer.writerow(["Start Date", "End Date", "Work package", "Evidence", "Short Description", "Person", "Long description", "File", "Evidence URL"])

    with open(filename, 'a') as f:
        writer = unicodecsv.writer(f, delimiter=',')
        # print "Writing " + str(len(results)) + " annotations to " + filename
        for result in results:
            writer.writerow([result.date,
                             result.date,
                             "",
                             "Code commit",
                             result.short_explanation,
                             result.committer_name,
                             result.commit_message,
                             "",
                             result.html_url])


def usage():
    print "Collects and writes out GitHub commit info for a user to a given repo.\n" \
          "For usage info, run with -h (--help).\n" \
          "Required arguments:\n" \
          "\t-a (--author)\tto supply the username/email of the author to print GitHub logs for,\n" \
          "\t-o (--owner)\tto supply to owner of the repository (e.g. EBISPOT) and\n" \
          "\t-r (--repo)\tto supply the repository from which to collect commits\n" \
          "\t-u (--username)\tYOUR github username (will be used for authentication)\n" \
          "\t-a (--auth-token)\tyour authentication token. " \
          "You can generate a new one of these here: https://github.com/settings/tokens"


def main(argv):
    # arguments for author, owner, repo
    author = ""
    has_author = False
    owner = ""
    has_owner = False
    repo = ""
    has_repo = False
    user = "tburdett"
    token = "8f98550124a38a2b0f99fd21bc27f0790d30c460"

    try:
        opts, argv = getopt.getopt(argv, "ha:o:r:u:t:", ["help", "author=", "owner=", "repo=","username=","auth-token="])
    except getopt.GetoptError:
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-a", "--author"):
            author = str(arg)
            has_author = True
        elif opt in ("-o", "--owner"):
            owner = str(arg)
            has_owner = True
        elif opt in ("-r", "--repo"):
            repo = str(arg)
            has_repo = True
        elif opt in ("-u", "--username"):
            user = str(arg)
        elif opt in ("-t", "--auth-token"):
            token = str(arg)

    if not has_author or not has_owner or not has_repo:
        print "username, owner and repo arguments are required"
        usage()
        sys.exit(2)
    else:
        sys.stdout.write("Collecting commits...")
        sys.stdout.flush()
        try:
            commits = collect_commits_from_github(author, owner, repo, user, token)
            write_results(commits, author, owner, repo)
        except ApiRequestError as e:
            print "Failed to complete API requests - " + str(e.status_code) + ": " + str(e.content)
        sys.stdout.write("done!\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main(sys.argv[1:])