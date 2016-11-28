class Commit:
    def __init__(self, id, date, committer_name, commit_message, changed_file_count, addition_count, deletion_count, short_explanation, long_explanation, link_url):
        self.id = id
        self.date = date
        self.committer_name = committer_name
        self.changed_file_count = changed_file_count
        self.addition_count = addition_count
        self.deletion_count = deletion_count
        self.short_explanation = short_explanation
        self.long_explanation = long_explanation
        self.commit_message = commit_message
        self.link_url = link_url

    def __str__(self):
        try:
            return 'Commit:{id=\'' + self.id + '\',date=\'' + self.date + '\',short_explanation=\'' + self.short_explanation + \
                   ',committer=\'' + self.committer_name + '\',commit_message=\'' + self.commit_message + \
                   '\',link=\'' + self.link_url + '\''
        except UnicodeDecodeError:
            print "Something went wrong handling commit " + self.id


class ApiRequestError(Exception):
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content

    def __str(self):
        return 'API request did not complete OK (' + self.status_code + ': ' + self.content + ').'
