#!/usr/bin/env python
"An assistant for making Python releases by Benjamin Peterson"
from __future__ import with_statement

import sys
import os
import optparse
import re
import subprocess
import shutil
import tempfile

from hashlib import md5
from string import Template
from urlparse import urlsplit, urlunsplit

SPACE = ' '


# Ideas stolen from Mailman's release script, Lib/tokens.py and welease

def error(*msgs):
    print >> sys.stderr, "**ERROR**"
    for msg in msgs:
        print >> sys.stderr, msg
    sys.exit(1)


def run_cmd(args, silent=False):
    cmd = SPACE.join(args)
    if not silent:
        print "Executing %s" % cmd
    try:
        if silent:
            code = subprocess.call(cmd, shell=True, stdout=PIPE)
        else:
            code = subprocess.call(cmd, shell=True)
    except OSError:
        error("%s failed" % cmd)


def check_env():
    if "EDITOR" not in os.environ:
        error("editor not detected.",
              "Please set your EDITOR enviroment variable")
    if not os.path.exists(".svn"):
        error("CWD is not a Subversion checkout")
        

def get_arg_parser():
    usage = "%prog [options] tagname"
    p = optparse.OptionParser(usage=usage)
    p.add_option("-b", "--bump",
        default=False, action="store_true",
        help="bump the revision number in important files")
    p.add_option("-e", "--export",
        default=False, action="store_true",
        help="Export the SVN tag to a tarball")
    p.add_option("-m", "--branch",
        default=False, action="store_true",
        help="create a maintance branch to go along with the release")
    p.add_option("-t", "--tag",
        default=False, action="store_true",
        help="Tag the release in Subversion")
    return p


def constant_replace(fn, updated_constants,
                     comment_start="/*", comment_end="*/"):
    "Inserts in between --start constant-- and --end constant-- in a file"
    start_tag = comment_start + "--start constants--" + comment_end
    end_tag = comment_start + "--end constants--" + comment_end
    with open(fn) as infile:
        with open(fn + '.new', 'w') as outfile:
            found_constants = False
            waiting_for_end = False
            for line in infile:
                if line[:-1] == start_tag:
                    print >> outfile, start_tag
                    print >> outfile, updated_constants
                    print >> outfile, end_tag
                    waiting_for_end = True
                    found_constants = True
                elif line[:-1] == end_tag:
                    waiting_for_end = False
                elif waiting_for_end:
                    pass
                else:
                    outfile.write(line)
    if not found_constants:
        error('Constant section delimiters not found: %s' % fn)
    os.rename(fn + '.new', fn)


def bump(tag):
    print "Bumping version to %s" % tag
    
    wanted_file = "Misc/RPM/python-%s.spec" % tag.basic_version
    print "Updating %s" % wanted_file,
    if not os.path.exists(wanted_file):
        specs = os.listdir("Misc/RPM/")
        for file in specs:
            if file.startswith("python-"):
                break
        full_path = os.path.join("Misc/RPM/", file)
        print "\nrenaming %s to %s" % (full_path, wanted_file)
        run_cmd(["svn", "rename", "--force", full_path, wanted_file])
        print "File was renamed; please commit"
        run_cmd(["svn", "commit"])
    new = "%define version " + tag.text + \
        "\n%define libver " + tag.basic_version
    constant_replace(wanted_file, new, "#", "")
    print "done"
    
    print "Updating Include/patchlevel.h...",
    template = Template("""\
#define PY_MAJOR_VERSION\t$major
#define PY_MINOR_VERSION\t$minor
#define PY_MICRO_VERSION\t$patch
#define PY_RELEASE_LEVEL\t$level
#define PY_RELEASE_SERIAL\t$serial

/* Version as a string */
#define PY_VERSION      \t\"$text\"""")
    substitutions = {}
    for what in ('major', 'minor', 'patch', 'serial', 'text'):
        substitutions[what] = getattr(tag, what)
    substitutions['level'] = dict(
        a   = 'PY_RELEASE_LEVEL_ALPHA',
        b   = 'PY_RELEASE_LEVEL_BETA',
        c   = 'PY_RELEASE_LEVEL_GAMMA',
        f   = 'PY_RELEASE_LEVEL_FINAL',
        )[tag.level]
    new_constants = template.substitute(substitutions)
    constant_replace("Include/patchlevel.h", new_constants)
    print "done"
    
    print "Updating Lib/idlelib/idlever.py...",
    with open("Lib/idlelib/idlever.py", "w") as fp:
        new = "IDLE_VERSION = \"%s\"\n" % tag.next_text
        fp.write(new)
    print "done"
    
    print "Updating Lib/distutils/__init__.py...",
    new = "__version__ = \"%s\"" % tag.text
    constant_replace("Lib/distutils/__init__.py", new, "#", "")
    print "done"
    
    other_files = ["README"]
    if tag.patch == 0 and tag.level == "a" and tag.serial == 0:
        other_files += ["Doc/tutorial/interpreter.rst",
            "Doc/tutorial/stdlib.rst", "Doc/tutorial/stdlib2.rst"]
    print "\nManual editing time..."
    for fn in other_files:
        print "Edit %s" % fn
        manual_edit(fn)
    
    print "Bumped revision"
    print "Please commit and use --tag"


def manual_edit(fn):
    run_cmd([os.environ["EDITOR"], fn])


def export(tag):
    if not os.path.exists('dist'):
        print "creating dist directory"
        os.mkdir('dist')
    if not os.path.isdir('dist'):
        error('dist/ is not a directory')
    tgz = "dist/Python-%s.tgz" % tag.text
    bz = "dist/Python-%s.tar.bz2" % tag.text
    old_cur = os.getcwd()
    try:
        print "chdir'ing to dist"
        os.chdir('dist')
        try:
            print 'Exporting tag:', tag.text
            python = 'Python-%s' % tag.text
            run_cmd(["svn", "export",
                     "http://svn.python.org/projects/python/tags/r%s"
                     % tag.nickname, python])
            print "Making .tgz"
            run_cmd(["tar cf - %s | gzip -9 > %s.tgz" % (python, python)])
            print "Making .tar.bz2"
            run_cmd(["tar cf - %s | bzip2 -9 > %s.tar.bz2" %
                     (python, python)])
        finally:
            os.chdir(old_cur)
        print "Moving files to dist"
    finally:
        print "Cleaning up"
    print 'Calculating md5 sums'
    md5sum_tgz = md5()
    with open(tgz) as source:
        md5sum_tgz.update(source.read())
    md5sum_bz2 = md5()
    with open(bz) as source:
        md5sum_bz2.update(source.read())
    print md5sum_tgz.hexdigest(), ' ', tgz
    print md5sum_bz2.hexdigest(), ' ', bz
    with open(tgz + '.md5', 'w') as md5file:
        print >> md5file, md5sum_tgz.hexdigest()
    with open(bz + '.md5', 'w') as md5file:
        print >> md5file, md5sum_bz2.hexdigest()
    print 'Signing tarballs'
    os.system('gpg -bas ' + tgz)
    os.system('gpg -bas ' + bz)
    print "**Now extract the archives and run the tests**"


class Tag:
    def __init__(self, text, major, minor, patch, level, serial):
        self.text = text
        self.next_text = self.text
        self.major = major
        self.minor = minor
        self.patch = patch
        self.level = level
        self.serial = serial
        self.basic_version = major + '.' + minor
    
    def __str__(self):
        return self.text

    @property
    def nickname(self):
        return self.text.replace('.', '')


def break_up_tag(tag):
    exp = re.compile(r"(\d+)(?:\.(\d+)(?:\.(\d+))?)?(?:([abc])(\d+))?")
    result = exp.search(tag)
    if result is None:
        error("tag %s is not valid" % tag)
    data = list(result.groups())
    # fix None level
    if data[3] is None:
        data[3] = "f"
    # None Everythign else should be 0
    for i, thing in enumerate(data):
        if thing is None:
            data[i] = 0
    return Tag(tag, *data)


def branch(tag):
    if tag.minor > 0 or tag.patch > 0 or tag.level != "f":
        print "It doesn't look like your making a final release."
        if raw_input("Are you sure you want to branch?") != "y":
            return
    run_cmd(["svn", "copy", get_current_location(),
        "svn+ssh://svn.python.org/projects/python/branches/" 
            "release%s-maint" % (tag.major + tag.minor)])


def get_current_location():
    proc = subprocess.Popen('svn info', shell=True, stdout=subprocess.PIPE)
    data = proc.stdout.read().splitlines()
    for line in data:
        if line.startswith('URL: '):
            return line.lstrip('URL: ')


def make_tag(tag):
    url = urlsplit(get_current_location())
    new_path = 'python/tags/r' + tag.nickname
    tag_url = urlunsplit((url.scheme, url.netloc, new_path,
                          url.query, url.fragment))
    run_cmd(['svn', 'copy', get_current_location(), tag_url])


def main(argv):
    parser = get_arg_parser()
    options, args = parser.parse_args(argv)
    if len(args) != 2:
        parser.print_usage()
        sys.exit(1)
    tag = break_up_tag(args[1])
    if not options.export:
        check_env()
    if options.bump:
        bump(tag)
    elif options.tag:
        make_tag(tag)
    elif options.branch:
        branch(tag)
    elif options.export:
        export(tag)


if __name__ == "__main__":
    main(sys.argv)