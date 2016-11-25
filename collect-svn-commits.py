import svn.local
import datetime
import sys
import re
import os
import unicodecsv
import getopt
import commit


finalpath_re = re.compile('([^/]+$)')


def collect_commits_from_svn(author, repo, fe_repo_name, date_from="", date_to=""):
    if not fe_repo_name:
        fe_repo_name = repo

    slc = svn.local.LocalClient(repo)

    if date_from and date_to:
        df = datetime.datetime.strptime(date_from, "%d/%m/%Y")
        dt = datetime.datetime.strptime(date_to, "%d/%m/%Y")
        log_entries = slc.log_default(df, dt)
    else:
        log_entries = slc.log_default()

    commits = []
    for le in log_entries:
        if le.author == author:
            revision = le.revision
            date = le.date.strftime('%d/%m/%Y')
            short_explanation = "1 commit"
            committer = le.author
            commit_message = le.msg
            evidence_url = 'http://gromit.ebi.ac.uk:10002/changelog/' + fe_repo_name + '?cs=' + revision

            comm = commit.Commit(revision,
                                 date,
                                 short_explanation,
                                 committer,
                                 commit_message,
                                 evidence_url)
            commits.append(comm)
    return commits


def write_results(results, author, repo):
    # get last pathname of repo for filename, rather than use full URL
    reponame = finalpath_re.search(repo).group(0)

    dirname = 'output'
    filename = "output/" + str(author) + "_" + str(reponame) + "_svn_commits.csv"

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
          "\t-a (--author)\tto supply the username/email of the author to print SVN logs for,\n" \
          "\t-r (--repo)\tto supply the local path to the checkout of the repository from which to collect commits\n" \
          "\t-df (--date-from)\t to supply the start date to collect commits from, format dd/mm/yyyy\n" \
          "\t-dt (--date-to)\tto supply the end date of commits, format dd/mm/yyyy"


def main(argv):
    # arguments for author, owner, repo
    author = ""
    has_author = False
    repo = ""
    has_repo = False
    has_date = False
    fe_repo_name = ""
    has_fe_repo = False

    try:
        opts, argv = getopt.getopt(argv, "ha:r:f:t:n:", ["help", "author=", "repo=", "date-from=", "date-to=", "fisheye-repo-name="])
    except getopt.GetoptError:
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-a", "--author"):
            author = str(arg)
            has_author = True
        elif opt in ("-r", "--repo"):
            repo = str(arg)
            has_repo = True
        elif opt in ("-f", "--date-from"):
            date_from = str(arg)
            has_date = True
        elif opt in ("-t", "--date-to"):
            date_to = str(arg)
            has_date = True
        elif opt in ("-n", "--fisheye-repo-name"):
            fe_repo_name = str(arg)
            has_fe_repo = True

    if not has_author or not has_repo or not has_fe_repo:
        print "username, repo and fisheye repository name arguments are required"
        usage()
        sys.exit(2)
    else:
        try:
            if has_date:
                sys.stdout.write("Collecting commits from " + date_from + " to " + date_to + "...")
                sys.stdout.flush()
                commits = collect_commits_from_svn(author, repo, fe_repo_name, date_from, date_to)
            else:
                sys.stdout.write("Collecting commits...")
                sys.stdout.flush()
                commits = collect_commits_from_svn(author, repo, fe_repo_name)
            write_results(commits, author, repo)
        except commit.ApiRequestError as e:
            print "Failed to complete API requests - " + str(e.status_code) + ": " + str(e.content)
        sys.stdout.write("done!\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main(sys.argv[1:])