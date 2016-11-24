class Commit:
    def __init__(self, id, date, short_explanation, committer_name, commit_message, html_url):
        self.id = id
        self.date = date
        self.short_explanation = short_explanation
        self.committer_name = committer_name
        self.commit_message = commit_message
        self.html_url = html_url

    def __str__(self):
        try:
            return 'Commit:{id=\'' + self.id + '\',date=\'' + self.date + '\',short_explanation=\'' + self.short_explanation + \
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
