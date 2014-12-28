import os
import json

from .. import printer


class Config(object):
    file = ""
    url = u"http://localhost/"
    api_key = u""

    def __init__(self, file):
        self.file = file

    def load(self):
        """
        Load config from file
        """
        with open(self.file, 'r') as infile:
            config = json.load(infile)
            if 'url' in config:
                self.url = config['url']
            if 'api_key' in config:
                self.api_key = config['api_key']


    def save(self):
        """
        Save config to file
        """
        with open(self.file, 'w') as outfile:
            json.dump(
                {
                    'url': self.url,
                    'api_key': self.api_key
                },
                outfile
            )


    def exists(self):
        """
        Check if the config file exist
        """
        return os.path.isfile(self.file)

    def install(self):
        printer.info(u"Type root url of redmine (don't forget scheme)")
        url = raw_input('> ').strip()
        if url:
            self.url = url
        elif self.url:
            printer.info(u"Use default url : " + self.url)

        printer.info(u"Type your api key")
        api_key = raw_input('> ').strip()
        if api_key:
            self.api_key = api_key
        elif self.api_key:
            printer.info(u"Use default api key : " + self.api_key)

        self.save()




