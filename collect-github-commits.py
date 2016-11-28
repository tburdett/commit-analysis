import commit
import os
import unicodecsv
import requests
import json
import re
import getopt
import sys
import datetime
import collections

api_url = "https://api.github.com/"
owner_re = re.compile('\{owner\}')
repo_re = re.compile('\{repo\}')


def dispatch_api_request(url, user, token):
    s = requests.Session()
    s.auth = (user, token)
    response = s.get(url)
    if response.status_code == 200:
        return json.loads(response.content)
    else:
        raise commit.ApiRequestError(response.status_code, response.content)


def collect_commits_from_github(author, owner, repo, user, token, fe_repo_name=""):
    if not fe_repo_name:
        fe_repo_name = repo

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
        commit_metadata = c['commit']
        committer_metadata = commit_metadata['committer']

        commit_date = datetime.datetime.strptime(committer_metadata['date'], "%Y-%m-%dT%H:%M:%SZ")
        date_str = commit_date.strftime("%d/%m/%Y")
        committer_name = committer_metadata['name']
        commit_message = commit_metadata['message']
        short_description = "1 commit"
        long_description = '{0} modified files, {1} total changes ({2} additions and {3} deletions): {4}'\
            .format(str(files), str(total), str(additions), str(deletions), str(commit_metadata['message']))
        evidence_url = 'http://gromit.ebi.ac.uk:10002/changelog/' + str(fe_repo_name) + '?cs=' + str(sha)

        master_commit_sha_list.append(sha)
        comm = commit.Commit(sha,
                             date_str,
                             committer_name,
                             commit_message,
                             files,
                             additions,
                             deletions,
                             short_description,
                             long_description,
                             evidence_url)
        commits.append(comm)
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
    evidence_filename = "output/" + str(author) + "_" + str(owner) + ":" + str(repo) + "_evidence_of_work.txt"
    calendar_filename = "output/" + str(author) + "_" + str(owner) + ":" + str(repo) + "_git_commits.csv"

    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # write evidence file, plain text with calendar-style format
    with open(evidence_filename, 'w') as f:
        # write header
        f.write("CODE COMMIT REPORT\n\n")
        f.write("=========================\n")
        f.write("Author:\t\t" + author + "\n")
        f.write("Username:\t" + author + "\n")
        f.write("Repository:\thttp://github.com/{0}/{1}\n".format(str(owner), str(repo)))
        f.write("Dates:\t\t<DATEFROM> to <DATETO>\n")
        f.write("=========================\n\n")

        # index results by date
        indexed_results = collections.OrderedDict()
        for result in results:
            if result.date in indexed_results:
                indexed_results[result.date].append(result)
            else:
                indexed_results[result.date] = [result]

        for date in reversed(indexed_results.keys()):
            f.write(str(date) + "\n")
            f.write("----------\n")
            num_commits = len(indexed_results[date])
            if num_commits == 1:
                f.write("1 commit\n")
            else:
                f.write("{0} commits\n".format(str(num_commits)))
            for next_result in indexed_results[date]:
                f.write("\t * Changed {0} files ({1} additions and {2} deletions)\n".format(
                    str(next_result.changed_file_count), str(next_result.addition_count), str(next_result.deletion_count)))
                f.write("\t\t\"{0}\"\n".format(str(next_result.commit_message)))
            f.write("\n\n")
        f.close()

    with open(calendar_filename, 'w') as f:
        writer = unicodecsv.writer(f, delimiter=',')
        writer.writerow(["Start Date", "End Date", "Work package", "Evidence", "Short Description", "Person", "Long description", "File", "Evidence URL"])

    with open(calendar_filename, 'a') as f:
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
                             evidence_filename,
                             result.link_url])
    f.close()


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
    token = ""
    has_token = False
    fe_repo_name = ""
    has_fe_repo = False

    try:
        opts, argv = getopt.getopt(argv, "ha:o:r:u:t:n:", ["help", "author=", "owner=", "repo=","username=","auth-token=","fisheye-repo-name="])
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
            has_token = True
        elif opt in ("-n", "--fisheye-repo-name"):
            fe_repo_name = str(arg)
            has_fe_repo = True

    if not has_author or not has_owner or not has_repo or not has_token:
        print "username, owner, repo and auth-token arguments are required"
        usage()
        sys.exit(2)
    else:
        sys.stdout.write("Collecting commits...")
        sys.stdout.flush()
        try:
            if has_fe_repo:
                commits = collect_commits_from_github(author, owner, repo, user, token, fe_repo_name)
            else:
                commits = collect_commits_from_github(author, owner, repo, user, token)
            write_results(commits, author, owner, repo)
        except commit.ApiRequestError as e:
            print "Failed to complete API requests - " + str(e.status_code) + ": " + str(e.content)
        sys.stdout.write("done!\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main(sys.argv[1:])