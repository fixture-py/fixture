
import os
from distutils.cmd import Command
from fixture import docs

class pushdocs(Command):
    description = "push documentation to server"
    user_options = [
        # ('optname=', None, ""),
    ]    
    # boolean_options = ['update']
    
    def initialize_options(self):
        pass
        
    def finalize_options(self):
        pass
        
    def run(self):
        assert 'FD_HOST' in os.environ, (
            "environment variable $FD_HOST must be set with the server "
            "host to connect to")
        assert os.path.exists(docs.builddir), (
            "first run python setup.py userdocs apidocs")
        apidocs = os.path.join(docs.builddir, 'apidocs')
        assert os.path.exists(apidocs), (
            "first run python setup.py apidocs")
        userdocs = os.path.join(docs.builddir, 'docs')
        assert os.path.exists(userdocs), (
            "first run python setup.py userdocs")
        def push_pkg(pkg_path):
            os.chdir(os.path.dirname(pkg_path))
            pkg = os.path.basename(pkg_path)
            os.system("rm %s.tgz" % pkg)
            os.system("tar -czf %s.tgz %s" % (pkg,pkg))
            os.system("scp %s.tgz %s:~/app/static/farmdev/projects/fixture/" % (
                        pkg, os.environ['FD_HOST']))
            os.system(
                "ssh %s 'cd ~/app/static/farmdev/projects/fixture; "
                "tar -xzf %s.tgz && rm %s.tgz'" % (
                        os.environ['FD_HOST'], pkg, pkg))
            print "pushed %s to %s" % (pkg, os.environ['FD_HOST'])
        push_pkg(apidocs)
        push_pkg(userdocs)