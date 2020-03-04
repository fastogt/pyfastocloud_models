import re


class M3uParser:
    def __init__(self):
        self.files = []
        self.lines = []

    # Read the file from the given path
    def read_m3u(self, file_path):
        file = open(file_path)
        self.load_content(file.read())

    def load_content(self, content):
        lines = []
        for line in content.split('\n'):
            ln = line.rstrip()
            if ln:
                if ln.startswith('#EXTM3U'):
                    lines.append(ln)
                elif ln.startswith('#EXTINF'):
                    lines.append(ln)
                elif ln[0] != '#':
                    lines.append(ln)
        self.lines = lines
        return len(self.lines)

    def parse(self):
        numLine = len(self.lines)
        for n in range(numLine):
            line = self.lines[n]
            if line[0] == '#':
                self._manage_line(n)

    # Getter for the list
    def get_list(self):
        return self.files

    # Remove files that contains a certain filterWord
    def filter_out_files_of_groups_containing(self, filter_word):
        self.files = list(filter(lambda file: filter_word not in file['tvg-group'], self.files))

    # Select only files that contais a certain filterWord
    def filter_in_files_of_groups_containing(self, filter_word):
        # Use the filter words as list
        if not isinstance(filter_word, list):
            filter_word = [filter_word]
        if not len(filter_word):
            return
        new = []
        for file in self.files:
            for fw in filter_word:
                if fw in file['tvg-group']:
                    # Allowed extension - go to next file
                    new.append(file)
                    break
        self.files = new

    # private
    def _manage_line(self, n):
        if n + 1 < len(self.lines):
            line_info = self.lines[n]
            line_link = self.lines[n + 1]
            if not line_info.startswith('#EXTM3U'):
                m = re.search('tvg-name=\"(.*?)\"', line_info)
                name = m.group(1) if m else 'Unknown'
                m = re.search('tvg-id=\"(.*?)\"', line_info)
                tid = m.group(1) if m else 'Unknown'
                m = re.search('tvg-logo=\"(.*?)\"', line_info)
                logo = m.group(1) if m else 'Unknown'
                m = re.search('group-title=\"(.*?)\"', line_info)
                group = m.group(1) if m else 'Unknown'
                m = re.search('[,](?!.*[,])(.*?)$', line_info)
                title = m.group(1) if m else 'Unknown'
                # ~ print(name+"||"+id+"||"+logo+"||"+group+"||"+title)

                test = {'title': title, 'tvg-name': name, 'tvg-id': tid, 'tvg-logo': logo, 'tvg-group': group,
                        'link': line_link}
                self.files.append(test)
